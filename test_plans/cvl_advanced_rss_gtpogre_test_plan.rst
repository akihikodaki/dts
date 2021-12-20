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

=============================
CVL: Advanced RSS FOR GTPoGRE
=============================

Description
===========
GTP over GRE feature enhances packet core performance in 4G LTE and 5G networks.
In GTP over GRE market segment package the parse graph is expanded to look for
a GTP or PFCP header after parsing a GRE header. GTP over GRE packets contain
two tunnel protocols.
The next header after the GRE header may be IPv4 or IPv6.  If an IPv6 header
is present, extension headers may be present. Then unlike in other types of
packages in case of finding UDP header parser does not assume UDP_LAST protocol
after GRE tunnel, but looks for GTP or PFCP headers. In case of finding those
headers the GRE header and the next IP header found in the packet after the
GRE header shall not be reported. Parser reports one of the already existing
GTP or PFCP ptypes.

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

.. note::

   The ptype of GTPoGRE is parsed the same as GTP packet,
   so they match gtpu RSS rule.

Prerequisites
=============

1. Hardware:

   - Intel E810 series ethernet cards: columbiaville_25g/columbiaville_100g/

2. Software:

   - dpdk: http://dpdk.org/git/dpdk
   - scapy: http://www.secdev.org/projects/scapy/

.. note::

   This rss feature designed for CVL NIC 25G and 100g, so below the case only support CVL nic.

3. Copy gtpogre pkg to /lib/firmware/updates/intel/ice/ddp/ice.pkg
   Then reload ice driver

4. bind the CVL port to dpdk driver in DUT::

    modprobe vfio-pci
    usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:3b:00.0

.. note::

   The kernel must be >= 3.6+ and VT-d must be enabled in bios.

5. Launch the testpmd to configuration queue of rx and tx number 64 in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -c 0xff -n 4 -- -i --rxq=64 --txq=64 --disable-rss --port-topology=loop
    testpmd>set fwd rxonly
    testpmd>set verbose 1

6. For test case "parse PFCP over GRE packet", we need to add print log
   in testpmd to show the PFCP ptype, then compile DPDK again::

    diff --git a/drivers/net/ice/ice_rxtx.c b/drivers/net/ice/ice_rxtx.c
    index 4136d045e..17e588f5f 100644
    --- a/drivers/net/ice/ice_rxtx.c
    +++ b/drivers/net/ice/ice_rxtx.c
    @@ -1573,6 +1573,7 @@ ice_rx_scan_hw_ring(struct ice_rx_queue *rxq)
                            pkt_flags = ice_rxd_error_to_pkt_flags(stat_err0);
                            mb->packet_type = ptype_tbl[ICE_RX_FLEX_DESC_PTYPE_M &
                                    rte_le_to_cpu_16(rxdp[j].wb.ptype_flex_flags0)];
    +                       printf("ptype: %3d\n", ICE_RX_FLEX_DESC_PTYPE_M & rte_le_to_cpu_16(rxdp[j].wb.ptype_flex_flags0));
                            ice_rxd_to_vlan_tci(mb, &rxdp[j]);
                            rxq->rxd_to_pkt_fields(rxq, mb, &rxdp[j]);

    @@ -3048,6 +3049,7 @@ ice_set_rx_function(struct rte_eth_dev *dev)
            PMD_INIT_FUNC_TRACE();
            struct ice_adapter *ad =
                    ICE_DEV_PRIVATE_TO_ADAPTER(dev->data->dev_private);
    +#if 0
     #ifdef RTE_ARCH_X86
            struct ice_rx_queue *rxq;
            int i;
    @@ -3126,7 +3128,7 @@ ice_set_rx_function(struct rte_eth_dev *dev)
                    }
                    return;
            }
    -
    +#endif
     #endif

7. start scapy and configuration NVGRE and GTP profile in tester
   scapy::

    >>> import sys
    >>> from scapy.contrib.gtp import *

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
The Ptype of GTPoGRE is parsed same as GTP packet, so they match gtp RSS rule.
We just need to add the GTPoGRE packet to the packets check.
we need to add GTPoGRE packet to "basic hit pattern packets",
"hit pattern/defined input set" and "hit pattern/not defined input set".
the GTPoGRE packet format in this pattern is to add::

    IP(proto=0x2F)/GRE(proto=0x0800)/

after Ether layer, before IP layer, just like::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")


Test case: MAC_IPV4_GTPU_EH_IPV4 with UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

DL case

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

all the DL cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_L3DST
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_L3SRC
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_GTPU
::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")


UL case

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

all the UL cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

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

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

all the DL cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_IPV4
::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_GTPU
::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

UL case

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

all the UL cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

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
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

all the cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_L3DST
::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_L3SRC
::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4
::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_GTPU
:::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

Test case: MAC_IPV4_GTPU_EH_IPV4_UDP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

all the cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L4DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L4SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_IPV4
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP
::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_GTPU
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

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
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

all the cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_L3DST
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_L3SRC
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4
:::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_GTPU
::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

Test case: MAC_IPV4_GTPU_IPV4_UDP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

all the cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L4DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L4SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_IPV4
::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP
:::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_GTPU
::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32,dport=33)/("X"*480)],iface="enp216s0f0")


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
        change the packet's outer L3 layer from::

          IP(proto=0x2F)/GRE(proto=0x0800)/IP()

        to::

          IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()

        after Ether layer, before IP layer, just like::

          sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Pattern: outer ipv6 + inner ipv6
--------------------------------

reconfig all the cases of "Pattern: outer ipv4 + inner ipv4"

    rule:
        change outer ipv4 to ipv6.
        change inner ipv4 to ipv6, change ipv4-udp to ipv6-udp, change ipv4-tcp to ipv6-tcp.
    packets:
        change the packet's inner L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.
        change the packet's outer L3 layer from::

          IP(proto=0x2F)/GRE(proto=0x0800)/IP()

        to::

          IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()

        after Ether layer, before IP layer, just like::

          sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

inner L4 protocal hash case
===========================
Subcase: MAC_IPV4_GTPU_IPV4_UDP/TCP
-----------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

3. send packets::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

4. check the two packets received with different hash values, and distributed to queue by RSS.

5. flush the rules, send the two packets again, check they are distributed to the same queue.

Subcase: MAC_IPV4_GTPU_EH_IPV6_UDP/TCP
--------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end

3. send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

4. check the two packets received with different hash values, and distributed to queue by RSS.

5. flush the rules, send the two packets again, check they are distributed to the same queue.

Subcase: MAC_IPV6_GTPU_IPV4_UDP/TCP
-----------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create rules::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

3. send packets::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

4. check the two packets received with different hash values, and distributed to queue by RSS.

5. flush the rules, send the two packets again, check they are distributed to the same queue.

Subcase: MAC_IPV6_GTPU_EH_IPV6_UDP/TCP
--------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create rules::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end

3. send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

4. check the two packets received with different hash values, and distributed to queue by RSS.

5. flush the rules, send the two packets again, check they are distributed to the same queue.


symmetric cases
===============

start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

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
MAC_IPV4_GTPU_EH_DL_IPV4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_EH_UL_IPV4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_DL_IPV6::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

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

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_EH_UL_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_DL_IPV6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

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
MAC_IPV4_GTPU_EH_IPV4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.3",src="192.168.0.4")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.4",src="192.168.0.3")/("X"*480)],iface="enp216s0f0")

not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_EH_IPV6::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_UDP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set:
MAC_IPV4_GTPU_EH_DL_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_UL_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_EH_IPV4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_IPV6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

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
MAC_IPV4_GTPU_IPV4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_IPV6::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_IPV4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

Test case: symmetric MAC_IPV4_GTPU_IPV4_UDP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set:
MAC_IPV4_GTPU_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_EH_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

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
        change the packet's outer L3 layer from::

          IP(proto=0x2F)/GRE(proto=0x0800)/IP()

        to::

          IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()

        after Ether layer, before IP layer, just like::

          sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Pattern: symmetric outer ipv6 + inner ipv6
------------------------------------------

reconfig all the cases of "Pattern: symmetric outer ipv4 + inner ipv4"

    rule:
        change outer ipv4 to ipv6.
        change inner ipv4 to ipv6, change ipv4-udp to ipv6-udp, change ipv4-tcp to ipv6-tcp.
    packets:
        change the packet's inner L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.
        change the packet's outer L3 layer from::

          IP(proto=0x2F)/GRE(proto=0x0800)/IP()

        to::

          IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()

        after Ether layer, before IP layer, just like::

          sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

parse PFCP over GRE packet
==========================
Send packet::

    sendp(Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(sport=22, dport=8805)/PFCP(Sfield=0),iface="enp216s0f0")
    sendp(Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(sport=22, dport=8805)/PFCP(Sfield=1, SEID=123),iface="enp216s0f0")
    sendp(Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(sport=22, dport=8805)/PFCP(Sfield=0),iface="enp216s0f0")
    sendp(Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(sport=22, dport=8805)/PFCP(Sfield=1, SEID=256),iface="enp216s0f0")

It can be parsed as MAC_IPV4_PFCP_NODE::

    ptype: 351
    port 0/queue 0: received 1 packets
      src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=82 - nb_segs=1 - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x0
      ol_flags: PKT_RX_L4_CKSUM_UNKNOWN PKT_RX_IP_CKSUM_UNKNOWN PKT_RX_OUTER_L4_CKSUM_UNKNOWN

Send packet::

    sendp(Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(sport=22, dport=8805)/PFCP(Sfield=1, SEID=123),iface="enp216s0f0")

It can be parsed as MAC_IPV4_PFCP_SESSION::

    ptype: 352
    port 0/queue 0: received 1 packets
      src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=82 - nb_segs=1 - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x0
      ol_flags: PKT_RX_L4_CKSUM_UNKNOWN PKT_RX_IP_CKSUM_UNKNOWN PKT_RX_OUTER_L4_CKSUM_UNKNOWN

Send packet::

    sendp(Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(sport=22, dport=8805)/PFCP(Sfield=0),iface="enp216s0f0")

It can be parsed as MAC_IPV6_PFCP_NODE::

    ptype: 353
    port 0/queue 0: received 1 packets
      src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x86dd - length=122 - nb_segs=1 - sw ptype: L2_ETHER L3_IPV6 TUNNEL_GRE INNER_L3_IPV6 INNER_L4_UDP  - l2_len=14 - l3_len=40 - tunnel_len=4 - inner_l3_len=40 - inner_l4_len=8 - Receive queue=0x0
      ol_flags: PKT_RX_L4_CKSUM_UNKNOWN PKT_RX_IP_CKSUM_UNKNOWN PKT_RX_OUTER_L4_CKSUM_UNKNOWN

Send packet::

    sendp(Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(sport=22, dport=8805)/PFCP(Sfield=1, SEID=256),iface="enp216s0f0")

It can be parsed as MAC_IPV6_PFCP_SESSION::

    ptype: 354
    port 0/queue 0: received 1 packets
      src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x86dd - length=122 - nb_segs=1 - sw ptype: L2_ETHER L3_IPV6 TUNNEL_GRE INNER_L3_IPV6 INNER_L4_UDP  - l2_len=14 - l3_len=40 - tunnel_len=4 - inner_l3_len=40 - inner_l4_len=8 - Receive queue=0x0
      ol_flags: PKT_RX_L4_CKSUM_UNKNOWN PKT_RX_IP_CKSUM_UNKNOWN PKT_RX_OUTER_L4_CKSUM_UNKNOWN
