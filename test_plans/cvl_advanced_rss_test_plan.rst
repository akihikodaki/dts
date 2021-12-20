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

=========================
CVL: Advanced RSS FOR CVL
=========================

Description
===========

Advanced RSS only support columbiaville nic with ice , through creating rules which include related pattern and input-set
to hash IP and ports domain, diverting the packets to different queues.

* inner header hash for tunnel packets, including comms package.
* symmetric hash by rte_flow RSS func.
* input set changed by rte_flow RSS types.

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
    |                               |                           | l4-src-only, l4-dst-only, ipv4                                                   |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_TCP              | eth, l2-src-only, l2-dst-only, ipv4-tcp, l3-src-only, l3-dst-only,               |
    |                               |                           | l4-src-only, l4-dst-only, ipv4                                                   |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_SCTP             | eth, l2-src-only, l2-dst-only, ipv4-sctp, l3-src-only, l3-dst-only,              |
    |                               |                           | l4-src-only, l4-dst-only, ipv4                                                   |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6                  | eth, l2-src-only, l2-dst-only, ipv6, l3-src-only, l3-dst-only                    |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_UDP              | eth, l2-src-only, l2-dst-only, ipv6-udp, l3-src-only, l3-dst-only,               |
    |                               |                           | l4-src-only, l4-dst-only, ipv6                                                   |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_TCP              | eth, l2-src-only, l2-dst-only, ipv6-tcp, l3-src-only, l3-dst-only,               |
    |                               |                           | l4-src-only, l4-dst-only, ipv6                                                   |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_SCTP             | eth, l2-src-only, l2-dst-only, ipv6-sctp, l3-src-only, l3-dst-only,              |
    |                               |                           | l4-src-only, l4-dst-only, ipv6                                                   |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
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
    | PPPOES                        | MAC_PPPOES_IPV4           | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only, ipv4                    |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV4_UDP       | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only,                         |
    |                               |                           | l4-src-only, l4-dst-only, ipv4-udp, ipv4                                         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV4_TCP       | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only,                         |
    |                               |                           | l4-src-only, l4-dst-only, ipv4-tcp, ipv4                                         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV4_SCTP      | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only,                         |
    |                               |                           | l4-src-only, l4-dst-only, ipv4-sctp, ipv4                                        |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV6           | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only, ipv6                    |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV6_UDP       | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only,                         |
    |                               |                           | l4-src-only, l4-dst-only, ipv6-udp, ipv6                                         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV6_TCP       | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only,                         |
    |                               |                           | l4-src-only, l4-dst-only, ipv6-tcp, ipv6                                         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV6_SCTP      | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only,                         |
    |                               |                           | l4-src-only, l4-dst-only, ipv6-udp, ipv6                                         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOES                | eth, l2-src-only, l2-dst-only, pppoe                                             |
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
    | PPPOES                        | MAC_PPPOES_IPV4           | ipv4                                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV4_UDP       | ipv4-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV4_TCP       | ipv4-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV4_SCTP      | ipv4-sctp                                                                      |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV6           | ipv6                                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV6_UDP       | ipv6-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV6_TCP       | ipv6-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_PPPOES_IPV6_SCTP      | ipv6-sctp                                                                      |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+

.. note::

    This test plan only cover the packet type IPv4/IPv6 + TCP/UDP/SCTP,
    including toeplitz, symmetric and simple-xor.
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

3. bind the CVL port to dpdk driver in DUT::

    modprobe vfio-pci
    usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:18:00.0

.. note::

   The kernel must be >= 3.6+ and VT-d must be enabled in bios.

4. Launch the testpmd to configuration queue of rx and tx number 64 in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

   or disable rss in command line::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -c 0xff -n 4 -- -i --rxq=64 --txq=64 --disable-rss --port-topology=loop
    testpmd>set fwd rxonly
    testpmd>set verbose 1
    testpmd>rx_vxlan_port add 4789 0

5. start scapy and configuration NVGRE and GTP profile in tester
   scapy::

   >>> import sys
   >>> sys.path.append('~/dts/dep')
   >>> from nvgre import NVGRE
   >>> from scapy.contrib.gtp import *


Default parameters
------------------

   MAC::

    [Src MAC]: 00:11:22:33:44:55
    [Dest MAC]: 68:05:CA:BB:26:E0

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
launch testpmd with "--disable-rss"
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
6. send not hit pattern packets with input set in the rule.
   check the received packets have not hash value, and distributed to queue 0.
   note: if there is not this type packet in the case, omit this step.
7. distroy the rule and list rule.
8. send same packet with step 3.
   check the received packets have not hash value, and distributed to queue 0.

Test case: MAC_IPV4
===================
basic hit pattern packets are the same in this test case:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

ipv4-udp-vxlan packet::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src='192.168.0.2')/UDP(sport=22,dport=23)/("X"*480)], iface="ens786f0")

not hit pattern packets are the same in this test case::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*80)],iface="ens786f0")

Subcase: MAC_IPV4_L2SRC
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l2-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.3", src="192.168.0.5",frag=7)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=19,dport=99)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_L2DST
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l2-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5",frag=7)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=23,dport=25)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_L2SRC_L2DST
-----------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types eth end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5",frag=7)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=23,dport=25)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_L3SRC
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_L3DST
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

ipv4-udp-vxlan packet::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.1.1", src='192.168.0.2')/UDP(sport=22,dport=23)/("X"*480)], iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=33)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_ALL
---------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)],iface="ens786f0")

Test case: MAC_IPV4_UDP
=======================

basic hit pattern packets are the same in this test case.
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

nvgre packet::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="ens786f0")

not hit pattern packets are the same in this test case::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/Raw("x"*80)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)], iface="ens786f0")

Subcase: MAC_IPV4_UDP_L2SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_UDP_L2DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_UDP_L2SRC_L2DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types eth end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_UDP_L3SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

nvgre packet::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)], iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_UDP_L3DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

nvgre packet::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=33)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_UDP_L3SRC_L4SRC
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_UDP_L3SRC_L4DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_UDP_L3DST_L4SRC
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_UDP_L3DST_L4DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_UDP_L4SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_UDP_L4DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV4_UDP_IPV4
--------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:53", src="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_ALL
-------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

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

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

nvgre packet::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")

not hit pattern packets are the same in this test case::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV6_L2SRC
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types eth l2-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV6_L2DST
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types eth l2-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV6_L2SRC_L2DST
-----------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types eth end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV6_L3SRC
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=33)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV6_L3DST
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV6_ALL
---------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="ens786f0")


Test case: MAC_IPV6_UDP
=======================
basic hit pattern packets are the same in this test case:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

not hit pattern packets are the same in this test case::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(src="192.168.0.1",dst="192.168.0.2")/UDP(sport=22,dport=23)/Raw("x"*80)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV6_UDP_L2SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV6_UDP_L2DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV6_UDP_L2SRC_L2DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types eth end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: MAC_IPV6_UDP_L3SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=33)/("X"*480)],iface="ens786f0")


Subcase: MAC_IPV6_UDP_L3DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="ens786f0")


Subcase: MAC_IPV6_UDP_L3SRC_L4SRC
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")


Subcase: MAC_IPV6_UDP_L3SRC_L4DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")


Subcase: MAC_IPV6_UDP_L3DST_L4SRC
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")


Subcase: MAC_IPV6_UDP_L3DST_L4DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")


Subcase: MAC_IPV6_UDP_L4SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")


Subcase: MAC_IPV6_UDP_L4DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")


Subcase: MAC_IPV6_UDP_IPV6
--------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:53", src="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")


Subcase: MAC_IPV6_UDP_ALL
-------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

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
Launch testpmd without "--disable-rss"
all the test cases run the same test steps as below:

1. validate rule.
2. if the rule is MAC_IPV4_UDP/TCP/SCTP or MAC_IPV6_UDP/TCP/SCTP,
   set "port config all rss all".
3. send hit pattern packets with switched value of input set in the rule.
   check the received packets have different hash value.
   check all the packets are distributed to queues by rss.
4. create rule and list rule.
5. send same packets with step 2.
   check the received packets have the same hash value.
   check all the packets are distributed to queues by rss.
6. send not hit pattern packets with switched value of input set in the rule.
   check the received packets have different hash value.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.
7. distroy the rule and list rule.
8. send same packets with step 3, only switch ip address.
   check the received packets which switched ip address have not hash value,
   or have different hash value.

Test case: symmetric MAC_IPV4
=============================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)],iface="ens786f0")

ipv4-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/ICMP()/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. not hit pattern with switched value of input set in the rule:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2928",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")

Test case: symmetric MAC_IPV4_UDP
=================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)],iface="ens786f0")

3. not hit pattern/not defined input set packets::
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")


Test case: symmetric MAC_IPV4_TCP
=================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=23,dport=22)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=23,dport=22)/("X"*480)],iface="ens786f0")

3. not hit pattern/not defined input set packets::
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")


Test case: symmetric MAC_IPV4_SCTP
==================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss func symmetric_toeplitz types ipv4-sctp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-sctp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=23,dport=22)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=23,dport=22)/("X"*480)],iface="ens786f0")

3. not hit pattern/not defined input set packets::
ipv4-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

Test case: symmetric MAC_IPV6
=============================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="ens786f0")

ipv6-frag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="ens786f0")

ipv6-icmp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="ens786f0")

ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. not hit pattern with switched value of input set in the rule:
ipv4-nonfrag packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)],iface="ens786f0")

Test case: symmetric MAC_IPV6_UDP
=================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. not hit pattern/not defined input set packets::
ipv6-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

Test case: symmetric MAC_IPV6_TCP
=================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. not hit pattern/not defined input set packets::
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")


Test case: symmetric MAC_IPV6_SCTP
==================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-sctp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. not hit pattern/not defined input set packets::
ipv6-udp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

Test case: global simple-xor
============================
1. Launch testpmd without "--disable-rss"

2. send packets with switched l3 address::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)], iface="ens786f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)], iface="ens786f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=22, dport=23)/("X" * 80)], iface="ens786f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X" * 80)], iface="ens786f0")

3. check the pair of packets with switched l3 address have different hash value, and distributed by rss.

4. create a simple-xor rule::

    flow create 0 ingress pattern end actions rss func simple_xor key_len 0 queues end / end

5. send the packet in step 2 again.

6. check the pair of packets with switched l3 address have same hash value, and distributed to same queue.

7. delete the rule::

    flow destroy 0 rule 0

8. send the packet in step 2 again.

9. check the pair of packets with switched l3 address have different hash value, and distributed by rss.

Test Case: negative case
========================
1. create rules with invalid input set::

    testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l3-src-only end key_len 0 queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff3b61eb08, Invalid input set: Invalid argument
    testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-udp end key_len 0 queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff3b61eb08, Invalid input set: Invalid argument
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types udp end key_len 0 queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff70533a48, Invalid input set: Invalid argument
    testpmd> flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types tcp end key_len 0 queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff70533a48, Invalid input set: Invalid argument
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

2. validate all the rules in step 1::

    flow validate 0 ingress pattern eth / ipv4 / end actions rss types eth l3-src-only end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / end actions rss types ipv4-udp end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / udp / end actions rss types udp end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv6 / tcp / end actions rss types tcp end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / end actions rss types ipv6 end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 l3-src-only end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types eth end key_len 0 queues end / end

   check all the rule failed to be validated.

Test Case: multirules test
==========================
Launch testpmd without "--disable-rss"

Subcase 1: two rules with same pattern but different hash input set, not hit default profile
--------------------------------------------------------------------------------------------

1. create a MAC_IPV4_UDP_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_IPV4_UDP packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")

   check the hash value is different from the first packet.

3. create a rule with same pattern but different hash input set::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_IPV4_UDP packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")

   check the hash value is the same as the first packet.
   change the field [Dest IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.7")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")

   check the hash value is different from the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.
   send a MAC_IPV4_UDP packet, you can find it hit default ipv4 profile::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")

   change the fields [Source IP] or [Dest IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.9")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.9")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")

   check the hash values of the last two packets are different from the first packet.
   destroy the rule 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule 0 not exists in the list.
   send a MAC_IPV4_UDP packet, you can find it hit default ipv4 profile::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")

   change the fields [Source IP] or [Dest IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.9")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.9")/UDP(dport=45)/Raw("x"*480)], iface="ens786f0")

   check the hash values of the last two packets are different from the first packet.

Subcase 2: two rules with same pattern but different hash input set, hit default profile
----------------------------------------------------------------------------------------

1. create a MAC_IPV4_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_IPV4_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/Raw("x"*480)], iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/Raw("x"*480)], iface="ens786f0")

   check the hash value is different from the first packet.
   change the field [Dest IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8")/Raw("x"*480)], iface="ens786f0")

   check the hash value is the same as the first packet.

3. create a rule with same pattern but different hash input set::

     testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_IPV4_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/Raw("x"*480)], iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/Raw("x"*480)], iface="ens786f0")

   check the hash value is the same as the first packet.
   change the field [Dst IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.7")/Raw("x"*480)], iface="ens786f0")

   check the hash value is different from the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.

Subcase 3: two rules, scope smaller created first, and the larger one created later
-----------------------------------------------------------------------------------

1. create a MAC_IPV4_UDP_PAY_L4_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_IPV4_UDP_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="ens786f0")

   change the field [Source Port], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25, dport=45)/Raw("x"*480)], iface="ens786f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.8")/UDP(sport=23, dport=44)/Raw("x"*480)], iface="ens786f0")

   check the hash value is the same as the first packet.

3. create a MAC_IPV4_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_IPV4_UDP_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="ens786f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8")/UDP(sport=25, dport=99)/Raw("x"*480)], iface="ens786f0")

   check the hash value is the same as the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.
   destroy the rule 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

Subcase 4: two rules, scope larger created first, and the smaller one created later
-----------------------------------------------------------------------------------

1. create a MAC_IPV4_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_IPV4_UDP_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="ens786f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8")/UDP(sport=25, dport=99)/Raw("x"*480)], iface="ens786f0")

   check the hash value is the same as the first packet.

3. create a MAC_IPV4_UDP_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_IPV4_UDP_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="ens786f0")

   change the field [Source Port], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25, dport=45)/Raw("x"*480)], iface="ens786f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.8")/UDP(sport=23, dport=44)/Raw("x"*480)], iface="ens786f0")

   check the hash value is the same as the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.
   destroy the rule 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

Test case: MAC_IPV4_IPV4_CHKSUM
===============================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-chksum  end queues end / end

2. basic hit pattern packet::

    p1=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1",dst="192.168.0.2",chksum=0x1)/ ("X"*48)

3. hit pattern/changed defined input set::

    p2=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1",dst="192.168.0.2",chksum=0xffff)/ ("X"*48)

4. hit pattern/changed not defined input set::

    p3=Ether(dst="00:11:22:33:44:53", src="52:00:00:00:00:01")/IP(src="192.168.1.1",dst="192.168.1.2",chksum=0x1)/ ("X"*48)

5. not hit pattern::

    p4=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/("X"*48)

Test case: MAC_IPV4_UDP_CHKSUM
==============================
Subcase 1: MAC_IPV4_UDP_L4_CHKSUM
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l4-chksum  end queues end / end

2. basic hit pattern packet::

    p1=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1",dst="192.168.0.2")/UDP(sport=22, dport=23,chksum=0xffff)/("X"*48)

3. hit pattern/changed defined input set::

    p2=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1",dst="192.168.0.2")/UDP(sport=22, dport=23,chksum=0xfffe)/("X"*48)

4. hit pattern/changed not defined input set::

    p3=Ether(dst="00:11:22:33:44:53", src="52:00:00:00:00:01")/IP(src="192.168.1.1", dst="192.168.1.2",chksum=0x3)/UDP(sport=32, dport=33,chksum=0xffff)/("X"*48)

5. not hit pattern::

    p4=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1",dst="192.168.0.2")/SCTP(sport=22, dport=23,chksum=0xffff)/("X"*48)

Subcase 2: MAC_IPV4_UDP_IPV4_CHKSUM
-----------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-chksum  end queues end / end

2. basic hit pattern packet::

    p1=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1",dst="192.168.0.2",chksum=0xffff)/UDP(sport=22, dport=23)/("X"*48)

3. hit pattern/changed defined input set::

    p2=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1",dst="192.168.0.2",chksum=0xfffe)/UDP(sport=22, dport=23)/("X"*48)

4. hit pattern/changed not defined input set::

    p3=Ether(dst="00:11:22:33:44:53", src="52:00:00:00:00:01")/IP(src="192.168.1.1", dst="192.168.1.2",chksum=0xffff)/UDP(sport=32, dport=33,chksum=0xffff)/("X"*48)

5. not hit pattern::

    p4=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1",dst="192.168.0.2",chksum=0xffff)/SCTP(sport=22, dport=23)/("X"*48)

Test case: MAC_IPV4_TCP_CHKSUM
==============================
The rules and packets in this test case is similar to "Test case: MAC_IPV4_UDP_CHKSUM",
just change some parts of rules and packets:

    rule:
        change udp to tcp
    packets:
        if the packet's L4 layer is UDP, change it to TCP;
        if the packet's L4 layer is TCP, change it to UDP;

Subcase 1: MAC_IPV4_TCP_L4_CHKSUM
---------------------------------

Subcase 2: MAC_IPV4_TCP_IPV4_CHKSUM
-----------------------------------

Test case: MAC_IPV4_SCTP_CHKSUM
===============================
The rules and packets in this test case is similar to "Test case: MAC_IPV4_UDP_CHKSUM",
just change some parts of rules and packets:

    rule:
        change udp to sctp
    packets:
        if the packet's L4 layer is UDP, change it to SCTP;
        if the packet's L4 layer is SCTP, change it to TCP;

Subcase 1: MAC_IPV4_SCTP_L4_CHKSUM
----------------------------------

Subcase 2: MAC_IPV4_SCTP_IPV4_CHKSUM
------------------------------------

Test case: MAC_IPV6_UDP_L4_CHKSUM
=================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types l4-chksum  end queues end / end

2. basic hit pattern packet::

    p1 = Ether(src="52:00:00:00:00:00", dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/UDP(sport=22, dport=23, chksum=0x1)/("X"*48)

3. hit pattern/changed defined input set::

    p2 = Ether(src="52:00:00:00:00:00", dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/UDP(sport=22, dport=23, chksum=0x2)/("X"*48)

4. hit pattern/changed not defined input set::

    p3 = Ether(src="52:00:00:00:00:01", dst="00:11:22:33:44:53")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="ABAB:910A:2222:5498:8475:1111:3900:1011")/UDP(sport=32, dport=33, chksum=0x1)/("X"*48)

5. not hit pattern::

    p4 = Ether(src="52:00:00:00:00:00", dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=22, dport=23, chksum=0x1)/("X"*49)

Test case: MAC_IPV6_TCP_L4_CHKSUM
=================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types l4-chksum  end queues end / end

2. basic hit pattern packet::

    p1 = Ether(src="52:00:00:00:00:00", dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=22, dport=23, chksum=0x1)/("X"*48)

3. hit pattern/changed defined input set::

    p2 = Ether(src="52:00:00:00:00:00", dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=22, dport=23, chksum=0x2)/("X"*48)

4. hit pattern/changed not defined input set::

    p3 = Ether(src="52:00:00:00:00:01", dst="00:11:22:33:44:53")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="ABAB:910A:2222:5498:8475:1111:3900:1011")/TCP(sport=32, dport=33, chksum=0x1)/("X"*48)

5. not hit pattern::

    p4 = Ether(src="52:00:00:00:00:00", dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/SCTP(sport=22, dport=23, chksum=0x1)/("X"*49)

Test case: MAC_IPV6_SCTP_L4_CHKSUM
==================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types l4-chksum  end queues end / end

2. basic hit pattern packet::

    p1 = Ether(src="52:00:00:00:00:00", dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/SCTP(sport=22, dport=23, chksum=0xffffffff)/("X"*48)

3. hit pattern/changed defined input set::

    p2 = Ether(src="52:00:00:00:00:00", dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/SCTP(sport=22, dport=23, chksum=0xfffffffe)/("X"*48)

4. hit pattern/changed not defined input set::

    p3 = Ether(src="52:00:00:00:00:01", dst="00:11:22:33:44:53")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="ABAB:910A:2222:5498:8475:1111:3900:1011")/SCTP(sport=32, dport=33, chksum=0xffffffff)/("X"*48)

5. not hit pattern::

    p4 = Ether(src="52:00:00:00:00:00", dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/UDP(sport=22, dport=23, chksum=0x1)/("X"*49)

Test case: Checksum for different payload length
================================================
1. launch testpmd without "--disable-rss"::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c f -n 6 -- -i --rxq=16 --txq=16
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Send packets with different payload length::

    p1=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/("X"*48)
    p2=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/("X"*64)
    p3=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/UDP()/("X"*48)
    p4=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/UDP()/("X"*64)
    p5=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/TCP()/("X"*48)
    p6=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/TCP()/("X"*64)
    p7=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/SCTP()/("X"*48)
    p8=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/SCTP()/("X"*64)

   Check all the packets received have same hash value.

3. create RSS rule of 5-tuple inputset for each packet type::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp  end queues end / end
    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp  end queues end / end
    flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp  end queues end / end

4. Send packets of step 2.
   Check the received packets with same packet type have same hash value.

5. create RSS rule of l4-chksum inputset for each packet type::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l4-chksum  end queues end / end
    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types l4-chksum  end queues end / end
    flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types l4-chksum  end queues end / end

6. Send packets of step 2.
   Check the UDP/TCP/SCTP packets with different payload length have different hash value.

7. create RSS rule of ipv4-chksum inputset for each packet type::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-chksum  end queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-chksum  end queues end / end
    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-chksum  end queues end / end
    flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-chksum  end queues end / end

8. Send packets of step 2.
   Check the IPV4/UDP/TCP/SCTP packets with different payload length have different hash value.

Test case: Set HW csum, flow rule doesn’t impact RX checksum and TX checksum
============================================================================
1. launch testpmd without "--disable-rss"::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c f -n 6 -- -i --rxq=16 --txq=16

2. Set tx checksum::

    port stop all
    set fwd csum
    csum set ip hw 0
    csum set udp hw 0
    csum set tcp hw 0
    csum set sctp hw 0
    port start all
    set verbose 1
    start

3. Capture the tx packet at tester port::

    tcpdump -i enp216s0f0 -Q in -e -n -v -x

4. Send packets::

    p1=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1", chksum=0xfff3)/("X"*48)
    p2=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/TCP(sport=22, chksum=0xfff3)/("X"*48)
    p3=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/UDP(sport=22, chksum=0x1)/("X"*48)
    p4=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/SCTP(sport=22, chksum=0x1)/("X"*48)
    p5=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/TCP(sport=22, chksum=0xe38)/("X"*48)
    p6=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/UDP(sport=22, chksum=0xe38)/("X"*48)
    p7=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/SCTP(sport=22, chksum=0xf)/("X"*48)

   Check rx checksum good or bad, check if the tx checksum correct.

5. Create rss rules with chsum as inputset::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-chksum end queues end / end
    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types l4-chksum end queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l4-chksum end queues end / end
    flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types l4-chksum end queues end / end
    flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types l4-chksum end queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types l4-chksum end queues end / end
    flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types l4-chksum end queues end / end

6. Send the same packets, check the hash value changed, check rx and tx checksum, get the same result.

Test case: Combined case with fdir queue group
==============================================
1. start testpmd without "--disable-rss"::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c f -n 6 -- -i --rxq=16 --txq=16
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Create fdir rules to queue group::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / tcp / end actions rss queues 4 5 end / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / udp / end actions rss queues 6 7 end / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / sctp / end actions rss queues 8 9 end / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 / tcp / end actions rss queues 10 11 end / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 / udp / end actions rss queues 12 13 end / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 / sctp / end actions rss queues 14 15 end / end

3. Send packets::

    p1=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1", chksum=0xfff3)/("X"*48)
    p2=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/TCP(sport=22, chksum=0xfff3)/("X"*48)
    p3=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/UDP(sport=22, chksum=0x1)/("X"*48)
    p4=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/SCTP(sport=22, chksum=0x1)/("X"*48)
    p5=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/TCP(sport=22, chksum=0xe38)/("X"*48)
    p6=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/UDP(sport=22, chksum=0xe38)/("X"*48)
    p7=Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6(src="ABAB:910A:2222:5498:8475:1111:3900:1010")/SCTP(sport=22, chksum=0xf)/("X"*48)

   Check p2-p7 are distributed to specified queue group,
   p1 is distributed by RSS hash value.

4. Create rss rule with inputset checksum::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-chksum  end queues end / end
    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types l4-chksum  end queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l4-chksum  end queues end / end
    flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types l4-chksum  end queues end / end
    flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types l4-chksum  end queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types l4-chksum  end queues end / end
    flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types l4-chksum  end queues end / end

   Send same packets again. Check hash values of p2-p6 are changed, but queue group not changed.
   Check p1 hash value changed too, and distributed by RSS hash value.

5. Create fdir rule to queue group for ipv4 pattern::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / end actions rss queues 0 1 2 3 end / end

   Send p1, check the packet distributed to queue group without hash value changed.

Test case: Negative case
========================
1. create a rule with invalid inputset::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types l4-chksum end queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff0a9b9f80, Invalid input set: Invalid argument

2. create a rule with inputset not supported::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6-chksum  end queues end / end
    Bad arguments
