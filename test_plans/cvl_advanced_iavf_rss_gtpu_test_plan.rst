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

===============================
CVL IAVF: Advanced RSS For GTPU 
===============================

Description
===========

Enable RSS in CVL IAVF for GTP-U Up/Down Link sperately.
IAVF RSS hash algorithm is based on 5 Tuple (Src IP Address/Dst IP Address/Src Port/Dst Port/l4 Protocol) using the DPDK RTE_FLOW rules for GTP-U packets.
It can support ipv4+ipv6 combination of GTP-U packet.

* ipv4(outer) + ipv4(inner)
* ipv4(outer) + ipv6(inner)
* ipv6(outer) + ipv4(inner)
* ipv6(outer) + ipv6(inner)

IAVF also support symmetric hash function by rte_flow for GTP-U packets. But simple-xor hash function is not supported in IAVF.
And it need DDP Comms Package to support GTP-U protocol.

support pattern and input set 
-----------------------------
.. table::

    +------------------------------------+-------------------------------------------------------------------------------------------+
    | Hash function: toeplitz                                                                                                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | Packet Type                        | All the Input Set options in combination                                                  |
    +====================================+===========================================================================================+
    | MAC_IPV4_GTPU_EH_IPV4              | ipv4, l3-src-only, l3-dst-only                                                            |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU_EH_IPV4_UDP          | ipv4, ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU_EH_IPV4_TCP          | ipv4, ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU_IPV4                 | ipv4, gtpu, l3-src-only, l3-dst-only                                                      |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU_IPV4_UDP             | ipv4, ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU_IPV4_TCP             | ipv4, ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU_EH_IPV6              | ipv6, l3-src-only, l3-dst-only                                                            |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU_EH_IPV6_UDP          | ipv6, ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU_EH_IPV6_TCP          | ipv6, ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU_IPV6                 | ipv6, gtpu, l3-src-only, l3-dst-only                                                      |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU_IPV6_UDP             | ipv6, ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU_IPV6_TCP             | ipv6, ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV4              | ipv4, l3-src-only, l3-dst-only                                                            |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV4_UDP          | ipv4, ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV4_TCP          | ipv4, ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_IPV4                 | ipv4, gtpu, l3-src-only, l3-dst-only                                                      |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_IPV4_UDP             | ipv4, ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_IPV4_TCP             | ipv4, ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV6              | ipv6, l3-src-only, l3-dst-only                                                            |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV6_UDP          | ipv6, ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV6_TCP          | ipv6, ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_IPV6                 | ipv6, gtpu, l3-src-only, l3-dst-only                                                      |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_IPV6_UDP             | ipv6, ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU_IPV6_TCP             | ipv6, ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                        |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPU                      | ipv4, l3-src-only, l3-dst-only                                                            |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPU                      | ipv6, l3-src-only, l3-dst-only                                                            |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV4_GTPC                      | ipv4, l3-src-only, l3-dst-only                                                            |
    +------------------------------------+-------------------------------------------------------------------------------------------+
    | MAC_IPV6_GTPC                      | ipv6, l3-src-only, l3-dst-only                                                            |
    +------------------------------------+-------------------------------------------------------------------------------------------+


.. table::

    +------------------------------------+------------------------------------------------+
    | Hash function: Symmetric_toeplitz                                                   |
    +------------------------------------+------------------------------------------------+
    | Pattern                            | all the input set options in combination       |
    +====================================+================================================+
    | MAC_IPV4_GTPU_EH_IPV4              | ipv4                                           |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU_EH_IPV4_UDP          | ipv4-udp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU_EH_IPV4_TCP          | ipv4-tcp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU_IPV4                 | ipv4                                           |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU_IPV4_UDP             | ipv4-udp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU_IPV4_TCP             | ipv4-tcp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU_EH_IPV6              | ipv6                                           |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU_EH_IPV6_UDP          | ipv6-udp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU_EH_IPV6_TCP          | ipv6-tcp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU_IPV6                 | ipv6                                           |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU_IPV6_UDP             | ipv6-udp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU_IPV6_TCP             | ipv6-tcp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV4              | ipv4                                           |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV4_UDP          | ipv4-udp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV4_TCP          | ipv4-tcp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_IPV4                 | ipv4                                           |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_IPV4_UDP             | ipv4-udp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_IPV4_TCP             | ipv4-tcp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV6              | ipv6                                           |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV6_UDP          | ipv6-udp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_EH_IPV6_TCP          | ipv6-tcp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_IPV6                 | ipv6                                           |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_IPV6_UDP             | ipv6-udp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU_IPV6_TCP             | ipv6-tcp                                       |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPU                      | ipv4                                           |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPU                      | ipv6                                           |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV4_GTPC                      | ipv4                                           |
    +------------------------------------+------------------------------------------------+
    | MAC_IPV6_GTPC                      | ipv6                                           |
    +------------------------------------+------------------------------------------------+


Prerequisites
=============

1. Hardware:

  - Intel E810 series ethernet cards: columbiaville_25g/columbiaville_100g/

2. Software:

  - dpdk: http://dpdk.org/git/dpdk
  - scapy: http://www.secdev.org/projects/scapy/

.. note::

    This rss feature designed for CVL NIC 25G and 100G, so below cases only support CVL NIC.

3. create a VF from a PF in DUT, set mac address for thi VF::

    echo 1 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ip link set enp24s0f0 vf 0 mac 00:11:22:33:44:55

4. bind VF to vfio-pci::

    modprobe vfio-pci
    usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:18:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

5. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd  -c 0xff -n 4 -w 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd>set fwd rxonly
    testpmd>set verbose 1

6. start scapy and configuration NVGRE and GTP profile in tester
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

6. destroy the rule and list rule. check the flow list has no rule.



Pattern: outer ipv4 + inner ipv4
--------------------------------

GTPoGRE is imported in DPDK-21.02.
The Ptype is parsed same as GTP packet, so they match gtp RSS rule.
We just need to add the GTPoGRE packet to the packets check.
we need to add GTPoGRE packet to "basic hit pattern packets",
"hit pattern/defined input set" and "hit pattern/not defined input set".
the GTPoGRE packet format in this pattern is to add::

    IP(proto=0x2F)/GRE(proto=0x0800)/

after Ether layer, before IP layer, just like::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

Test case: MAC_IPV4_GTPU_EH_IPV4 with UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

DL case

basic hit pattern packets are the same in this test case.
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_L3DST
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_L3SRC
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern and defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")

UL case::

   basic hit pattern packets are the same in this test case.
   ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")

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

Test case: MAC_IPV4_GTPU_EH_IPV4_UDP with UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

DL case

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

UL case

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

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

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4SRC.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4DST.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4SRC.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4DST.

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

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L3
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP.


Test case: MAC_IPV4_GTPU_EH_IPV4_TCP with UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

DL case

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

UL case

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4SRC.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4DST.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4SRC.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4DST.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4DST.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4SRC.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP.


Test case: MAC_IPV4_GTPU_EH_IPV4 without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case.
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_L3DST
::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_L3SRC
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern and defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")


Test case: MAC_IPV4_GTPU_EH_IPV4_UDP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L4DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L4SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP
::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")


Test case: MAC_IPV4_GTPU_EH_IPV4_TCP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L4DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L4SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP
::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")


Test case: MAC_IPV4_GTPU_IPV4
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case.
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    
ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_L3DST
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    
ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    
ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_L3SRC
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern and defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    
ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    
ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4
:::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_gtpu
::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types gtpu end key_len 0 queues end / end

hit pattern and defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123457)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    
ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123457)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")
    
ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123457)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")
    
ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123457)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp134s0f0")
    
ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123457)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set:
ipv4-nonfrag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    
ipv4-frag packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2")/TCP()/("X"*480)],iface="enp134s0f0")

ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2")/UDP()/("X"*480)],iface="enp134s0f0")


Test case: MAC_IPV4_GTPU_IPV4_UDP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_UDP_L4DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_UDP_L4SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3
::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP
:::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")


Test case: MAC_IPV4_GTPU_IPV4_TCP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_TCP_L4DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
Subcase: MAC_IPV4_GTPU_IPV4_TCP_L4SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    
hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3
::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP
:::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")



Pattern: outer ipv4 + inner ipv6
--------------------------------

reconfig all the cases of "Pattern: outer ipv4 + inner ipv4"

    rule:
        change inner ipv4 to ipv6, change ipv4-udp to ipv6-udp, change ipv4-tcp to ipv6-tcp.
    packets:
        change the packet's inner L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.

the GTPoGRE packet format in this pattern is to add::

    IP(proto=0x2F)/GRE(proto=0x0800)/

after Ether layer, before IP layer, just like::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")


Pattern: outer ipv6 + inner ipv4
--------------------------------

reconfig all the cases of "Pattern: outer ipv4 + inner ipv4"

    rule:
        change outer ipv4 to ipv6.
    packets:
        change the packet's outer L3 layer from IP to IPv6;

the GTPoGRE packet format in this pattern is to add::

    IPv6(nh=0x2F)/GRE(proto=0x86dd)/

after Ether layer, before IP layer, just like::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")


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

the GTPoGRE packet format in this pattern is to add::

    IPv6(nh=0x2F)/GRE(proto=0x86dd)/

after Ether layer, before IP layer, just like::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

Pattern: MAC_IPV4_GTPU
----------------------
basic hit pattern packets are the same in this test case::
MAC_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_L3SRC
>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::
MAC_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

hit pattern but not defined input set::
MAC_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_L3DST
>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::
MAC_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

hit pattern but not defined input set::
MAC_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_L3
>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::
MAC_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

hit pattern but not defined input set::
MAC_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()],iface="enp134s0f0")


Pattern: MAC_IPV4_GTPC
----------------------
basic hit pattern packets are the same in this test case::
MAC_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=27)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPC_L3SRC
>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpc / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::
MAC_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=27)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

hit pattern but not defined input set::
MAC_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=27)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPC_L3DST
>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpc / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::
MAC_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=27)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

hit pattern but not defined input set::
MAC_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=27)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPC_L3
>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpc / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::
MAC_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=27)/GTPPDUNotificationRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=27)/GTPPDUNotificationRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=27)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.11.1", dst="192.168.11.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

hit pattern but not defined input set::
MAC_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=27)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")


Pattern: MAC_IPV6_GTPU
----------------------
reconfig all the cases of "Test case: MAC_IPV4_GTPU"

    rule:
        change ipv4 to ipv6.
    packets:
        change the packet's L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.


Pattern: MAC_IPV6_GTPC
----------------------
reconfig all the cases of "Test case: MAC_IPV4_GTPC"

    rule:
        change ipv4 to ipv6.
    packets:
        change the packet's L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.



symmetric cases
===============

all the test cases run the same test steps as below:

1. validate rule.
2. create rule and list rule.
3. send a basic hit pattern packet,record the hash value.
4. send a hit pattern packet with switched value of input set in the rule.
   check the received packets have same hash value.
   check both the packets are distributed to queues by rss.
5. destroy the rule and list rule.
6. send the packet in step 4.
   check the received packet has different hash value with which in step 3(including the case has no hash value).

Note: the GTPoGRE packets need to be added to symmetric cases as a Ptype, just like toeplitz cases.


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

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4 frag::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.3",dst="192.168.0.8",frag=6)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.8",dst="192.168.0.3",frag=6)/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_ICMP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/ICMP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/ICMP()/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_UDP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/UDP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/UDP()/("X"*480)], iface="enp134s0f0")


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

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")


Subcase: symmetric MAC_IPV4_GTPU_EH_UL_IPV4_UDP
:::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase symmetric MAC_IPV4_GTPU_EH_DL_IPV4.


Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_TCP with UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
the rules and packets in this test case is similar to "Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_UDP with UL/DL"
just change some parts of rules and packets::

    rule:
        change inner udp to tcp, change ipv4-udp to ipv4-tcp
    packets:
        change the packet's inner L4 layer UDP to TCP

Subcase: symmetric MAC_IPV4_GTPU_EH_DL_IPV4_TCP
:::::::::::::::::::::::::::::::::::::::::::::::

Subcase: symmetric MAC_IPV4_GTPU_EH_UL_IPV4_TCP
:::::::::::::::::::::::::::::::::::::::::::::::

Test case: symmetric MAC_IPV4_GTPU_EH_IPV4 without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::
MAC_IPV4_GTPU_EH_DL_IPV4 nonfrag::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4 frag::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.3",dst="192.168.0.8",frag=6)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.8",dst="192.168.0.3",frag=6)/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_ICMP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/ICMP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/ICMP()/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_UDP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/UDP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/UDP()/("X"*480)], iface="enp134s0f0")


Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_UDP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set::
MAC_IPV4_GTPU_EH_DL_IPV4_UDP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_UL_IPV4_UDP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")


Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_TCP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
the rules and packets in this test case is similar to "Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_UDP without UL/DL"
just change some parts of rules and packets::

    rule:
        change inner udp to tcp, change ipv4-udp to ipv4-tcp
    packets:
        change the packet's inner L4 layer UDP to TCP


Test case: symmetric MAC_IPV4_GTPU_IPV4
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::
MAC_IPV4_GTPU_IPV4 nonfrag::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_IPV4 frag::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.3",dst="192.168.0.8",frag=6)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.8",dst="192.168.0.3",frag=6)/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_IPV4_ICMP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.10",dst="192.168.0.20")/ICMP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.20",dst="192.168.0.10")/ICMP()/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_IPV4_UDP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.10",dst="192.168.0.20")/UDP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.20",dst="192.168.0.10")/UDP()/("X"*480)], iface="enp134s0f0")

Test case: symmetric MAC_IPV4_GTPU_IPV4_UDP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")


Test case: symmetric MAC_IPV4_GTPU_IPV4_TCP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
the rules and packets in this test case is similar to "Test case: symmetric MAC_IPV4_GTPU_IPV4_UDP"
just change some parts of rules and packets::

    rule:
        change inner udp to tcp, change ipv4-udp to ipv4-tcp
    packets:
        change the packet's inner L4 layer UDP to TCP



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
        change the packet's outer L3 layer from IP to IPv6



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


Pattern: symmetric MAC_IPV4_GTPU
--------------------------------
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::
MAC_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_REQUEST packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPU_ECHO_RESPONSE packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")


Pattern: symmetric MAC_IPV4_GTPC
--------------------------------
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpc / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::
MAC_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_VLAN_IPV4_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.3", dst="192.168.1.1")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")


Pattern: symmetric MAC_IPV6_GTPU
--------------------------------
rule::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end

hit pattern/defined input set::
MAC_IPV6_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV6_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_IPV6_GTPU_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV6_GTPU_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPU_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPU_EH_PAY packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPU_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPU_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")


Pattern: symmetric MAC_IPV6_GTPC
--------------------------------
rule::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpc / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end

hit pattern/defined input set::
MAC_IPV6_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_IPV6_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_IPV6_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV6_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV6_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_IPV6_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_IPV6_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_IPV6_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_IPV6_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_IPV6_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPC_EchoRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPC_EchoResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPC_CreatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPC_CreatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPC_UpdatePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPC_UpdatePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPC_DeletePDPContextRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPC_DeletePDPContextResponse packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPC_PDUNotificationRequest packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()],iface="enp134s0f0")

MAC_VLAN_IPV6_GTPC_SupportedExtensionHeadersNotification packet::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()],iface="enp134s0f0")


symmetric negative case
=======================
1. create rules with invalid input set::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end

2. check all the rules failed to be created.


toeplitz negative case
======================

1. create rules with invalid input set::

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

2. check all the rule failed to be created.


inner L4 protocol hash case
===========================
Note: add two GTPoGRE packets in each subcase with::

    IPv6(nh=0x2F)/GRE(proto=0x86dd)/

or::

    IP(proto=0x2F)/GRE(proto=0x0800)/

Subcase: MAC_IPV4_GTPU_IPV4_UDP/TCP
-----------------------------------
1. create rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. check the two packets received with different hash values, and distributed to queue by RSS.

4. flush the rules, send the two packets again, check they are distributed to the same queue::

    testpmd> flow flush 0

Subcase: MAC_IPV6_GTPU_IPV4_UDP/TCP
-----------------------------------
1. create rules::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. check the two packets received with different hash values, and distributed to queue by RSS.

4. flush the rules, send the two packets again, check they are distributed to the same queue::

    testpmd> flow flush 0

Subcase: MAC_IPV4_GTPU_IPV6_UDP/TCP
-----------------------------------
1. create rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888",src="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888",src="2222:3333:4444:5555:6666:7777:8888:9999")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. check the two packets received with different hash values, and distributed to queue by RSS.

4. flush the rules, send the two packets again, check they are distributed to the same queue::

    testpmd> flow flush 0

Subcase: MAC_IPV6_GTPU_IPV6_UDP/TCP
-----------------------------------
1. create rules::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888",src="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888",src="2222:3333:4444:5555:6666:7777:8888:9999")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. check the two packets received with different hash values, and distributed to queue by RSS.

4. flush the rules, send the two packets again, check they are distributed to the same queue::

    testpmd> flow flush 0


multirules case
===============

Subcase: IPV4_GTPU_IPV4/IPV4_GTPU_EH_IPV4
-----------------------------------------
1. create IPV4_GTPU_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")

3. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

4. create IPV4_GTPU_EH_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")

6. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

7. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")

8. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

9. destroy IPV4_GTPU_IPV4 rule::

    flow destroy 0 rule 0

10. repeat step 2, check packet 1-3 have no hash value, and distributed to queue 0. repeat step 5 and 7, check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

11. recreate IPV4_GTPU_IPV4 rule::

     flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

12. repeat step 2, check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

13. destroy IPV4_GTPU_EH_IPV4 rule::

     flow destroy 0 rule 1

14. repeat step 5 and 7, check packets have no hash value, and distributed to queue 0.

    
Subcase: IPV4_GTPU_EH_IPV4 with/without UL/DL
---------------------------------------------
1. create IPV4_GTPU_EH_DL_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")

3. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

4. create IPV4_GTPU_EH_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")

6. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.
 
7. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")

8. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

9. destroy IPV4_GTPU_EH_IPV4 rule::

    flow destroy 0 rule 1

10. repeat step 5 and 7, check packets have no hash value, and distributed to queue 0


Subcase: IPV4_GTPU_EH_IPV4 without/with UL/DL
---------------------------------------------
1. create IPV4_GTPU_EH_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")

3. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.
 
4. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")

5. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

6. create IPV4_GTPU_EH_UL_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

7. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")

8. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

9. repeat step 2, check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

10. destroy IPV4_GTPU_EH_IPV4 rule::

     flow destroy 0 rule 0

11. repeat step 2, check packets have no hash value, and distributed to queue 0. repeat step 7, check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.


Subcase: IPV4_GTPU_EH_IPV4 and IPV4_GTPU_EH_IPV4_UDP
----------------------------------------------------
1. create IPV4_GTPU_EH_IPV4_UDP rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

3. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

4. create IPV4_GTPU_EH_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")

6. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

7. repeat step 2, check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

8. destroy IPV4_GTPU_EH_IPV4 rule::

    flow destroy 0 rule 1

9. repeat step 2, check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

10. recreate IPV4_GTPU_EH_IPV4 rule::

     flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

11. destroy IPV4_GTPU_EH_IPV4_UDP rule::

     flow destroy 0 rule 0

12. repeat step 5, check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.


Subcase: IPV6_GTPU_EH_IPV6 and IPV6_GTPU_EH_IPV6_TCP
----------------------------------------------------
1. create IPV6_GTPU_EH_IPV6_TCP rule::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

3. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

4. create IPV6_GTPU_EH_IPV6 rule::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:1111")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)], iface="enp134s0f0")

6. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

7. repeat step 2, check all the packets has same hash value.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

8. destroy IPV6_GTPU_EH_IPV6 rule::

    flow destroy 0 rule 1

9. repeat step 5, check all the packets has different hash value.


Subcase: IPV4_GTPU_EH_IPV6 and IPV4_GTPU_EH_IPV6_UDP without UL/DL
------------------------------------------------------------------
1. create IPV4_GTPU_EH_IPV6_UDP rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:1111")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

3. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

4. create IPV4_GTPU_EH_IPV6 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:1111")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)], iface="enp134s0f0")

6. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

7. repeat step 2, packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.


Subcase: IPV6_GTPU_IPV4 and IPV6_GTPU_IPV4_TCP
----------------------------------------------
1. create IPV4_GTPU_IPV6_TCP rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:1111")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

3. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

4. create IPV4_GTPU_IPV6 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:1111")/("X"*480)], iface="enp134s0f0")

6. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

7. repeat step 2, packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.


toeplitz and symmetric rules combination case
=============================================

Subcase: toeplitz/symmetric with same pattern
---------------------------------------------
1. DUT create rule for the RSS function is toeplitz::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")

3. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

4. DUT create rule for the RSS function is symmetric:: 

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.3",dst="192.168.0.8",frag=6)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.8",dst="192.168.0.3",frag=6)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/ICMP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/ICMP()/("X"*480)], iface="enp134s0f0")

6. check each 2 pkts has same hash value.

7. DUT verify rule can be listed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS
    1       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS

8. repeat step 2, check the toeplitz rule can't work now.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

11. destroy the rule 1::

     testpmd> flow destroy 0 rule 1

12. repeat step 5, check the symmetric can't work now.

13. repeat step 2, check the toeplitz also can't work now.


Subcase: toeplitz/symmetric with same ptype different UL/DL
-----------------------------------------------------------
1. DUT create rule for the RSS function is toeplitz::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")

3. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

4. DUT create rule for the RSS function is symmetric:: 

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.3",dst="192.168.0.8",frag=6)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.8",dst="192.168.0.3",frag=6)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/ICMP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/ICMP()/("X"*480)], iface="enp134s0f0")

6. check each 2 pkts has same hash value.

7. DUT verify rule can be listed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS
    1       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS

8. repeat step 2, check the toeplitz rule also can work now.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

9. destroy the rule 1::

    testpmd> flow destroy 0 rule 1

10. repeat step 5, check the symmetric can't work now.

11. repeat step 2, check the toeplitz also can work now.

12. DUT recreate rule for the RSS function is symmetric::

     flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

13. repeat step 5, check the symmetric can work now.

14. destroy the rule 0::

     testpmd> flow destroy 0 rule 0

15. repeat step 5, check the symmetric also can work now.

16. repeat step 2, check the toeplitz can't work now.


Subcase: toeplitz/symmetric with different pattern
--------------------------------------------------
1. DUT create rule for the RSS function is toeplitz::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

3. check packet 2 and 3 has different hash value with packet 1, packet 4 has same hash value with packet 1.

4. DUT create rule for the RSS function is symmetric::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="2222:3333:4444:5555:6666:7777:8888:9999",dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:ABCD",dst="1111:2222:3333:4444:5555:6666:7777:1234")/IPv6ExtHdrFragment()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1234",dst="1111:2222:3333:4444:5555:6666:7777:ABCD")/IPv6ExtHdrFragment()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1888",dst="2222:3333:4444:5555:6666:7777:8888:1999")/ICMP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="2222:3333:4444:5555:6666:7777:8888:1999",dst="1111:2222:3333:4444:5555:6666:7777:1888")/ICMP()/("X"*480)], iface="enp134s0f0")

6. check each 2 pkts has same hash value.

7. DUT verify rule can be listed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 UDP => RSS
    1       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV6 => RSS

8. repeat step 2, check the toeplitz rule also can work now.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

9. destroy the rule 1::

    testpmd> flow destroy 0 rule 1

10. repeat step 5, check the symmetric can't work now.

11. repeat step 2, check the toeplitz also can work now.

12. DUT recreate rule for the RSS function is symmetric::

     flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end

13. repeat step 5, check the symmetric can work now.

14. destroy the rule 0::

     testpmd> flow destroy 0 rule 0

15. repeat step 5, check the symmetric also can work now.

16. repeat step 2, check the toeplitz can't work now.


Subcase: toeplitz/symmetric with different pattern (with/without UL/DL)
-----------------------------------------------------------------------
1. DUT create rule for the RSS function is toeplitz::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:1111")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

3. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

4. DUT create rule for the same pattern without UL/DL::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:1111")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:1111")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:1111")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

6. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.
   check packet 5 has different hash value with packet 4, packet 6 has same hash value with packet 4.
   check packet 8 has different hash value with packet 7, packet 9 has same hash value with packet 7.

7. DUT verify rule can be listed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 UDP => RSS
    1       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV6 => RSS

8. repeat step 2, check the rule with UL/DL can't work now.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

9. destroy the rule 1::

    testpmd> flow destroy 0 rule 1

10. repeat step 5, check the rule without UL/DL can't work now.


stress case
===========
Subcase: add/delete IPV4_GTPU_UL_IPV4_TCP rules
-----------------------------------------------
1. create/delete IPV4_GTPU_UL_IPV4_TCP rule for 100 times::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end
    flow destroy 0 rule 0

2. create the rule again, and list the rule::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 TCP => RSS

3. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

4. check packet 2 and 3 has different hash value with packet 1, packet 4 has same hash value with packet 1.

Subcase: add/delete IPV4_GTPU_DL_IPV4 rules
-------------------------------------------
1. create/delete IPV4_GTPU_DL_IPV4 rule for 100 times::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end    
    flow destroy 0 rule 0

2. create the rule again, and list the rule::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS

3. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    
4. check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.
