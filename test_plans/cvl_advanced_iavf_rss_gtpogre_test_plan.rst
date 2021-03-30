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

===============================
CVL IAVF: Advanced RSS For GTPU
===============================

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

3. Copy gtpogre pkg to /lib/firmware/updates/intel/ice/ddp/ice.pkg
   Then reload ice driver

4. create a VF from a PF in DUT, set mac address for thi VF::

    echo 1 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ip link set enp24s0f0 vf 0 mac 00:11:22:33:44:55

5. bind VF to vfio-pci::

    modprobe vfio-pci
    usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:18:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

6. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -c 0xff -n 4 -w 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd>set fwd rxonly
    testpmd>set verbose 1

7. For test case "parse PFCP over GRE packet", we need to add print log
   in testpmd to show the PFCP ptype, then compile DPDK again::

    diff --git a/drivers/net/iavf/iavf_rxtx.c b/drivers/net/iavf/iavf_rxtx.c
    index af5a28d84..37d996380 100644
    --- a/drivers/net/iavf/iavf_rxtx.c
    +++ b/drivers/net/iavf/iavf_rxtx.c
    @@ -1692,6 +1692,7 @@ iavf_rx_scan_hw_ring_flex_rxd(struct iavf_rx_queue *rxq)

                            mb->packet_type = ptype_tbl[IAVF_RX_FLEX_DESC_PTYPE_M &
                                    rte_le_to_cpu_16(rxdp[j].wb.ptype_flex_flags0)];
    +                       printf("ptype: %3d\n", IAVF_RX_FLEX_DESC_PTYPE_M & rte_le_to_cpu_16(rxdp[j].wb.ptype_flex_flags0));
                            iavf_flex_rxd_to_vlan_tci(mb, &rxdp[j]);
                            rxq->rxd_to_pkt_fields(rxq, mb, &rxdp[j]);
                            stat_err0 = rte_le_to_cpu_16(rxdp[j].wb.status_error0);
    @@ -2346,6 +2347,7 @@ iavf_set_rx_function(struct rte_eth_dev *dev)
                    IAVF_DEV_PRIVATE_TO_ADAPTER(dev->data->dev_private);
            struct iavf_info *vf = IAVF_DEV_PRIVATE_TO_VF(dev->data->dev_private);

    +#if 0
     #ifdef RTE_ARCH_X86
            struct iavf_rx_queue *rxq;
            int i;
    @@ -2425,6 +2427,7 @@ iavf_set_rx_function(struct rte_eth_dev *dev)

                    return;
            }
    +#endif
     #endif

            if (dev->data->scattered_rx) {

8. start scapy and configuration NVGRE and GTP profile in tester
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

6. destroy the rule and list rule. check the flow list has no rule.



Pattern: outer ipv4 + inner ipv4
--------------------------------

The Ptype of GTPoGRE is parsed same as GTP packet, so they match gtp RSS rule.
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

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_L3DST
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_L3SRC
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

UL case:

   basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

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

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

UL case

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

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

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

UL case

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

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
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_L3DST
::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_L3SRC
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.10.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

Test case: MAC_IPV4_GTPU_EH_IPV4_UDP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L4DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L4SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP
::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")


Test case: MAC_IPV4_GTPU_EH_IPV4_TCP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L4DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L4SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP
::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")


Test case: MAC_IPV4_GTPU_IPV4
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_L3DST
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_L3SRC
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4
:::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_gtpu
::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types gtpu end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123457)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.10.1", src="192.168.10.2")/("X"*480)],iface="enp134s0f0")

Test case: MAC_IPV4_GTPU_IPV4_UDP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L4DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L4SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3
::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP
:::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")


Test case: MAC_IPV4_GTPU_IPV4_TCP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L4DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L4SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.10.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3
::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=13)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_TCP
:::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=12, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=13)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp134s0f0")



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

          sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")


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

          sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")


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

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4 frag::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.3",dst="192.168.0.8",frag=6)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.8",dst="192.168.0.3",frag=6)/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_ICMP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/ICMP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/ICMP()/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_UDP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/UDP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/UDP()/("X"*480)], iface="enp134s0f0")


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

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")


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

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4 frag::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.3",dst="192.168.0.8",frag=6)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.8",dst="192.168.0.3",frag=6)/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_ICMP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/ICMP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/ICMP()/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_UDP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/UDP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/UDP()/("X"*480)], iface="enp134s0f0")


Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_UDP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set::
MAC_IPV4_GTPU_EH_DL_IPV4_UDP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_EH_UL_IPV4_UDP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")


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

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_IPV4 frag::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.3",dst="192.168.0.8",frag=6)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.8",dst="192.168.0.3",frag=6)/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_IPV4_ICMP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.10",dst="192.168.0.20")/ICMP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.20",dst="192.168.0.10")/ICMP()/("X"*480)], iface="enp134s0f0")

MAC_IPV4_GTPU_IPV4_UDP::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.10",dst="192.168.0.20")/UDP()/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.20",dst="192.168.0.10")/UDP()/("X"*480)], iface="enp134s0f0")

Test case: symmetric MAC_IPV4_GTPU_IPV4_UDP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.2", dst="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")


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
        change the packet's outer L3 layer from::

          IP(proto=0x2F)/GRE(proto=0x0800)/IP()

        to::

          IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()

        after Ether layer, before IP layer, just like::

          sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")


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

          sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")


inner L4 protocol hash case
===========================
Subcase: MAC_IPV4_GTPU_IPV4_UDP/TCP
-----------------------------------
1. create rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. check the two packets received with different hash values, and distributed to queue by RSS.

4. flush the rules, send the two packets again, check they are distributed to the same queue::

    testpmd> flow flush 0

Subcase: MAC_IPV6_GTPU_IPV4_UDP/TCP
-----------------------------------
1. create rules::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. check the two packets received with different hash values, and distributed to queue by RSS.

4. flush the rules, send the two packets again, check they are distributed to the same queue::

    testpmd> flow flush 0

Subcase: MAC_IPV4_GTPU_IPV6_UDP/TCP
-----------------------------------
1. create rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888",src="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888",src="2222:3333:4444:5555:6666:7777:8888:9999")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. check the two packets received with different hash values, and distributed to queue by RSS.

4. flush the rules, send the two packets again, check they are distributed to the same queue::

    testpmd> flow flush 0

Subcase: MAC_IPV6_GTPU_IPV6_UDP/TCP
-----------------------------------
1. create rules::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888",src="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=0x2F)/GRE(proto=0x86dd)/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888",src="2222:3333:4444:5555:6666:7777:8888:9999")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. check the two packets received with different hash values, and distributed to queue by RSS.

4. flush the rules, send the two packets again, check they are distributed to the same queue::

    testpmd> flow flush 0

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
