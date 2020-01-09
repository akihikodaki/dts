.. Copyright (c) <2019>, Intel Corporation
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

Advanced RSS only support columbiaville nic with ice , throught create rule include related pattern and input-set
to hash IP and ports domain, diversion the packets to the difference queues.

* inner header hash for tunnel packets, including comms package.
* symmetric hash by rte_flow RSS action.
* input set change by rte_flow RSS action.
  
Pattern and input set
---------------------
Table 1: 

    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    | Default hash function: Non Symmetric_toeplitz                                                                                                        |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |    Packet Type                |        Pattern                     |            Input Set                                                            |
    +===============================+====================================+=================================================================================+
    | IPv4/IPv6 + TCP/UDP/SCTP/ICMP |    MAC_IPV4_SRC_ONLY               |[Dest MAC]，[Source IP]                                                          |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_DST_ONLY_FRAG          |[Dest MAC]，[Dest IP]                                                            |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_PAY                    |[Dest MAC]，[Source IP], [Dest IP]                                               |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_SRC_ICMP               |[Dest MAC]，[Source IP]                                                          |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_DST_ICMP               |[Dest MAC]，[Source IP]                                                          |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_UDP_L3SRC_L4DST        |[Dest MAC]，[Source IP],[Dest Port]                                              |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_UDP                    |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]    |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_TCP_L3SRC_L4DST        |[Dest MAC]，[Source IP],[Dest Port]                                              |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_TCP_L3DST_L4SRC        |[Dest MAC]，[Dest IP],[Source Port]                                              |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_TCP                    |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]    |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_SCTP_L3SRC_L4DST       |[Dest MAC]，[Source IP],[Dest Port]                                              |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_SCTP                   |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]    |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_NVGRE_ICMP             |[Inner Source IP], [Inner Dest IP]                                               |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_NVGRE_L3SRC_ICMP       |[Inner MAC][Inner Source IP]                                                     |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_NVGRE_L3DST_ICMP       |[Inner MAC][Inner Dest IP]                                                       |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_NVGRE_TCP              |[Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]        |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_NVGRE_SCTP             |[Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]        |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_VXLAN_ICMP             |[Inner Source IP], [Inner Dest IP]                                               |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_VXLAN_L3SRC_ICMP       |[Inner MAC][Inner Source IP]                                                     |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_VXLAN_L3DST_ICMP       |[Inner MAC][Inner Dest IP]                                                       |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_VXLAN_TCP              |[Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]        |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_VXLAN_SCTP             |[Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]        |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_VXLAN_UDP              |[Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]        |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV6_SRC_ONLY               |[Dest MAC]，[Source IP]                                                          |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV6_DST_ONLY_FRAG          |[Dest MAC]，[Dest IP]                                                            |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV6_PAY                    |[Dest MAC]，[Source IP], [Dest IP],                                              |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV6_UDP                    |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]    |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV6_TCP                    |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]    |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV6_SCTP                   |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]    |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_PPPOE_PPPOD            |[Dest MAC]，[Session ID],[Proto] ,[Source IP] ,[Dest IP]                         |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_PPPOE_TCP              |[Dest MAC]，[Session ID],[Proto],[Source IP],[Dest IP],[Source Port],[Dest Port] |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_PPPOE_UDP              |[Dest MAC]，[Session ID],[Proto],[Source IP],[Dest IP],[Source Port],[Dest Port] |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_PPPOE_TCP              |[Dest MAC]，[Session ID],[Proto],[Source IP],[Dest IP],[Source Port],[Dest Port] |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_PPPOE_ICMP             |[Dest MAC]，[Session ID],[Proto],[Source IP],[Dest IP]                           |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_GTP                    | [TEID]                                                                          |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_GTPU_IPV4_TCP          | [TEID]                                                                          |
    +-------------------------------+------------------------------------+---------------------------------------------------------------------------------+

Table 2:
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+
    | Hash function: Symmetric_toeplitz                                                                                                                  |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+
    |    Packet Type                |        Pattern                     |            Input Set                                                          |
    +===============================+====================================+===============================================================================+
    |  IPV4/IPV6                    |    MAC_IPV4_SRC_ONLY               |[Dest MAC]，[Source IP]                                                        |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_DST_ONLY_FRAG          |[Dest MAC]，[Dest IP]                                                          |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_PAY                    |[Dest MAC]，[Source IP], [Dest IP]                                             |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+ 
    |                               |    MAC_IPV4_SRC_ICMP               |[Dest MAC]，[Source IP]                                                        |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+
    |                               |    MAC_IPV4_DST_ICMP               |[Dest MAC]，[Source IP]                                                        |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_UDP_L3SRC_L4DST        |[Dest MAC]，[Source IP],[Dest Port]                                            |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_UDP                    |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]  |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_TCP_L3SRC_L4DST        |[Dest MAC]，[Source IP],[Dest Port]                                            |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_TCP_L3DST_L4SRC        |[Dest MAC]，[Dest IP],[Source Port]                                            |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_TCP                    |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]  |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_SCTP_L3SRC_L4DST       |[Dest MAC]，[Source IP],[Dest Port]                                            |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_SCTP                   |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]  |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_NVGRE_ICMP             |[Inner Source IP], [Inner Dest IP]                                             |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_NVGRE_L3SRC_ICMP       |[Inner MAC][Inner Source IP]                                                   |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_NVGRE_L3DST_ICMP       |[Inner MAC][Inner Dest IP]                                                     |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_NVGRE_TCP              |[Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]      |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_NVGRE_SCTP             |[Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]      |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_VXLAN_ICMP             |[Inner Source IP], [Inner Dest IP]                                             |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_VXLAN_L3SRC_ICMP       |[Inner MAC][Inner Source IP]                                                   |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_VXLAN_L3DST_ICMP       |[Inner MAC][Inner Dest IP]                                                     |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_VXLAN_TCP              |[Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]      |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_VXLAN_SCTP             |[Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]      |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_VXLAN_UDP              |[Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]      |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV6_SRC_ONLY               |[Dest MAC]，[Source IP]                                                        |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV6_DST_ONLY_FRAG          |[Dest MAC]，[Dest IP]                                                          |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV6_PAY                    |[Dest MAC]，[Source IP], [Dest IP],                                            |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV6_UDP                    |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]  |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV6_TCP                    |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]  |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV6_SCTP                   |[Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]  |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV4_SIMPLE_XOR             |[Dest MAC]，[Source IP], [Dest IP]                                             |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	
    |                               |    MAC_IPV6_SIMPLE_XOR             |[Dest MAC]，[Source IP], [Dest IP]                                             |
    +-------------------------------+------------------------------------+-------------------------------------------------------------------------------+	

Default parameters
------------------

   MAC::

    [Dest MAC]: 68:05:ca:a3:28:94

   IPv4-Symmetric_toeplitz and simplexor::

    [Source IP]: 192.168.0.20
    [Dest IP]: 192.168.0.21
    [IP protocol]: 255
    [TTL]: 2
    [DSCP]: 4

   IPv6--Symmetric_toeplitz and simplexor::

    [Source IPv6]: 2001::2
    [Dest IPv6]: CDCD:910A:2222:5498:8475:1111:3900:2020
    [IP protocol]: 1
    [TTL]: 2
    [TC]: 1

   UDP/TCP/SCTP::
    [Source IP]: RandIP
    [Dest IP]: RandIP
    [Source Port]: Randport
    [Dest Port]: Randport

   VXLAN inner only---Symmetric_toeplitz::

    [Inner Source IP]: 192.168.0.20
    [Inner Dest IP]: 192.168.0.21
    [Inner Source Port]: 22
    [Inner Dest Port]: 23

   GTP-U data packet::

    [TEID]: 0x12345678

	
Prerequisites
=============

1. Hardware:
   Intel E810 series ethernet cards: columbiaville_25g/columbiaville_100g/

2. Software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/
 
Note: This rss feature designed for CVL NIC 25G and 100g, so below the case only support CVL nic.

3. bind the CVL port to dpdk driver in DUT::
   modprobe vfio-pci
   usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:18:00.0

Note: The kernel must be >= 3.6+ and VT-d must be enabled in bios.
   
4. Launch the testpmd to configuration queue of rx and tx number 64 in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd  -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop
    testpmd>set fwd rxonly
    testpmd>set verbose 1
    testpmd>rx_vxlan_port add 4789 0
   
3. start scapy and configuration NVGRE and GTP profile in tester
   scapy::
   >>> import sys
   >>> sys.path.append('~/dts/dep')
   >>> from nvgre import NVGRE
   >>> from scapy.contrib.gtp import * 

Test case: MAC_IPV4_L3SRC
=========================
#. create rule for the rss type for l3 src only::

    testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
    testpmd>start

#. send the 100 IP pkts::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP())/("X"*480)], iface="enp175s0f0", count=100)
    testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value,and check the pkts typ is “L2_ETHER L3_IPV4 NONFRAG”
   
   Verbose log parses and check point example: 
   Once rule has created and receive related packets, 
   Check the rss hash value and rss queue, make sure the different hash value and cause to related packets enter difference queue::
   
    src=00:00:00:00:00:00 - dst=68:05:CA:A3:28:94 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x60994f6e - RSS queue=0x2e - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV   4  - l2_len=14 - l3_len=20 - Receive queue=0x2e ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
   
   statistics log:
   ------- Forward Stats for RX Port= 0/Queue= 0 -> TX Port= 0/Queue= 0 -------
   RX-packets: 1              TX-packets: 0              TX-dropped: 0
   
   ------- Forward Stats for RX Port= 0/Queue= 1 -> TX Port= 0/Queue= 1 -------
   RX-packets: 2              TX-packets: 0              TX-dropped: 0
   ......
   
  ------- Forward Stats for RX Port= 0/Queue=63 -> TX Port= 0/Queue=63 -------
  RX-packets: 4              TX-packets: 0              TX-dropped: 0

   ---------------------- Forward statistics for port 0  ----------------------
   RX-packets: 100            RX-dropped: 0             RX-total: 100
   TX-packets: 0              TX-dropped: 0             TX-total: 0
   ----------------------------------------------------------------------------
   
   +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
   RX-packets: 100            RX-dropped: 0             RX-total: 100
   TX-packets: 0              TX-dropped: 0             TX-total: 0
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 
Test case: MAC_IPV4_L3SRC_FRAG
==============================
#. create rule for the rss type for l3 src only::

    testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
    testpmd> start

#. send the 100 IP +frag type pkts::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(), frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp175s0f0", count=100)
    testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value,and check the pkts typ is L2_ETHER L3_IPV4 "FRAG"
 
Test case: MAC_IPV4_L3DST:   
==========================
#. create rule for the rss type for l3 dst only::
       testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
       testpmd> start
#. send the 100 IP +frag type pkts::

       sendp([Ether(dst="68:05:ca:a3:28:94")/IP(dst=RandIP())/("X"*480)], iface="enp175s0f0", count=100)
       testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with
   differently RSS random value,and check the pkts typ is L2_ETHER L3_IPV4 "FRAG"


Test case: MAC_IPV4_L3DST_FRAG:
=============================== 
#. create rule for the rss type for l3 dst only::
       testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
       testpmd> start
   
#. send the 100 IP frag pkts::
       sendp([Ether(dst="68:05:ca:a3:28:94")/IP(dst=RandIP(), frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp175s0f0", count=100)
   
       testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value,and check the pkts typ is L2_ETHER L3_IPV4 "FRAG"
   
 
   
Test case: MAC_IPV4_L3SRC_FRAG_ICMP:
==================================== 
#. create rule for the rss type for l3 dst only::
       testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
       testpmd> start
#. send the 100 IP pkts::
       sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(), frag=5)/ICMP()/("X" * 80)], iface="enp175s0f0", count=100)
   
       testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
   
Test case: MAC_IPV4_L3DST_FRAG_ICMP:
====================================
#. create rule for the rss type for l3 dst only::
       testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
       testpmd> start
#. send the 100 IP pkts::
       sendp([Ether(dst="68:05:ca:a3:28:94")/IP(dst=RandIP(), frag=5)/ICMP()/("X" * 80)], iface="enp175s0f0", count=100)
   
       testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value

Test case: MAC_IPV4_PAY:
========================
#. create rule for the rss type for l3 all keywords::

       testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
       testpmd> start
#. send the 100 IP pkts::

       sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(),dst=RandIP())/("X"*480)], iface="enp175s0f0", count=100)
       testpmd>stop   
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
 
Test case: MAC_IPV4_PAY_FRAG_ICMP:
==================================
#. create rule for the rss type for IPV4 l3 all (src and dst) +frag+ICMP::
       flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
   
#. send the 100 IP pkts::

       sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(),dst=RandIP())/ICMP()/("X"*480)], iface="enp175s0f0", count=100)
       testpmd>stop
   
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value

Test case: MAC_IPV4_NVGRE_L3SRC:
================================
#. create rule for the rss type is IPV4 l3 src +NVGRE inner IPV4 +frag + ICMP::
       testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
       testpmd> start
#. send the 100 IP nvgre pkts::

       sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src=RandIP())/ICMP()/("X"*480)],iface="enp175s0f0",count=100)
       testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
  
Test case: MAC_IPV4_NVGRE_L3DST:
================================
#. create rule for the rss type is IPV4 l3 dst +NVGRE inner IPV4 +frag + ICMP::
       testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
       testpmd> start
#. send the 100 IP nvgre pkts::

       sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(dst=RandIP())/ICMP()/("X"*480)],iface="enp175s0f0",count=100)
       testpmd> stop
   
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value  
   
  
Test case: MAC_IPV4_VXLAN_L3SRC:
================================
#. create rule for the rss type is IPV4 src VXLAN +frag +ICMP:: 
       testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
       testpmd>start
#. send the 100 VXLAN pkts::
       sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src=RandIP(), frag=5)/ICMP()/("X" * 80)], iface="enp175s0f0", count=100)
       testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
  
Test case: MAC_IPV4_NVGRE_L3DST:
================================
#. create rule for the rss type is IPV4 dst VXLAN +frag+ICMP::
   
       testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
       testpmd>start
#. send the 100 vxlan pkts::
   
       sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(dst=RandIP(), frag=5)/ICMP()/("X" * 80)], iface="enp175s0f0", count=100)
       testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
 
Test case: MAC_IPV4_NVGRE:
==========================
#. create rule for the rss type is IPV4 all VXLAN +frag +ICMP::
   
       testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
       testpmd>start
   
#. send the 100 vxlan pkts::
       sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src=RandIP(),dst=RandIP(),frag=5)/ICMP()/("X" * 80)], iface="enp175s0f0", count=100)
   
       testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value 
   
  
Test case: MAC_IPV6_L3SRC
==========================
#. create rule for the rss type is IPV6 L3 src::
   
       testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end
       testpmd>start
#. send the 100 IPV6 pkts::
       sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src=RandIP6())/("X" * 80)], iface="enp175s0f0", count=100)
	   
Test case: MAC_IPV6_L3SRC_FRAG
===============================
#. create rule for the rss type is IPV6 L3 src +ExtHdrFragment::
       testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end
       testpmd>start
   
#. send the 100 IPV6 pkts::
       sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src=RandIP6())/IPv6ExtHdrFragment()/("X" * 80)], iface="enp175s0f0", count=100)
   
       testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
  
Test case: MAC_IPV6_L3DST
=========================
#. create rule for the rss type is IPV6 L3 dst +ExtHdrFragment::
       testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end
       testpmd>start
#. send the 100 IPV6 pkts::
       sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(dst=RandIP6())/IPv6ExtHdrFragment()/("X" * 80)], iface="enp175s0f0", count=100)
       testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
 
Test case: MAC_IPV6_PAY
=======================
#. create rule for the rss type is IPV6 L3 all +ExtHdrFragment+ICMP::
      testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end
      testpmd>start
#. send the 100 IPV6 pkts::
      sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src=RandIP6(),dst=RandIP6())/IPv6ExtHdrFragment()/ICMP()/("X" * 80)], iface="enp175s0f0", count=100)
      testpmd> stop
   
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
Test case: MAC_IPV4_UDP: 
========================
#. create rule for the rss type is ipv4 UDP +l3 src and dst::
      testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end
      testpmd>start
#. send the 100 IP+UDP pkts::

      sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP())/UDP(dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
      testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
 
Test case: MAC_IPV4_UDP_FRAG:
=============================
#. create rule for the rss type is ipv4 +UDP +frag::
      testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
      testpmd> start
#. send the 100 IP src IP +UDP port pkts::

      sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
   
#. send the 100 IP +UDP port pkts::

     sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
#. send the 100 IP src and dst IP  +UDP port pkts::

     sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(),dst=RandIP())/UDP()/("X"*480)], iface="enp175s0f0", count=100)
     testpmd> stop
   
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
Test case: MAC_NVGRE_IPV4_UDP_FRAG:
===================================  
#. create rule for the rss type is ipv4 + inner IP and UDP:: 
     testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
     testpmd>start
   
#. send the 100 NVGRE IP pkts::

     sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
     testpmd> stop   
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
Test case: MAC_VXLAN_IPV4_UDP_FRAG:
=================================== 
#. create rule for the rss type is ipv4 + vxlan UDP:: 
     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
     testpmd> start
#. To send VXLAN pkts with IP src and dst,UDP port::

     sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
     testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
Test case: MAC_IPV6_UDP:
========================
#. create rule for the rss type is IPV6 + UDP src and dst type hash::
     testpmd> flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
     testpmd> start
     sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src=RandIP6())/UDP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp175s0f0", count=100)
     testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value

Test case: MAC_IPV6_UDP_FRAG:   
=============================
#. To send IPV6 pkts with IPV6 src +frag +UDP port::
     sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src=RandIP6())/IPv6ExtHdrFragment()/UDP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp175s0f0", count=100)
     testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
Test case: MAC_IPV4_TCP_FRAG:   
============================= 
#. create rule for the rss type is IPV4 + TCP L3 src and  L4 dst type hash::
     testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end
#. To send IPV4 pkts with scr IP and TCP dst port::

     sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP())/TCP(dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
     testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end
#. To send IPV4 pkts with scr IP and TCP src port::

     sendp([Ether(dst="68:05:ca:a3:28:94")/IP(dst=RandIP())/TCP(sport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
     testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
  
Test case: MAC_IPV4_TCP_PAY
===========================
#. Create rule for the rss type is IPV4 +tcp and hash tcp src and dst ports::
     testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end
     testpmd>start
#. To send IPV4 pkts with IP src and dst ip and TCP ports::

     sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(),dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
#. To send IPV4 pkts without IP src and dst ip and includ TCP ports::

     sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
#. To send IPV4 pkts with IP src and dst ip and without TCP port::

     sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(),dst=RandIP())/TCP()/("X"*480)], iface="enp175s0f0", count=100)
#. To send IPV4 pkts with IP src and dst +frag and without TCP port::

     sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(),dst=RandIP(),frag=4)/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
     testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
 
Test case: MAC_IPV6_UDP_FRAG:   
=============================
#. Create rule for the RSS type nvgre IP src dst ip and TCP::
     testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end
     testpmd>start
#. To send NVGRE ip pkts::

     sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src=RandIP(),dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
     testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
Test case: MAC_VXLAN_IPV4_TCP
=============================  
#. Create rule for the rss type is IPV4 +tcp and hash tcp src and dst ports::
      testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end
      testpmd>start
#. To send VXLAN pkts includ src and dst ip and TCP ports::

      sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/TCP()/VXLAN()/Ether()/IP(src=RandIP(),dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
      testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
Test case: MAC_IPV6_TCP
======================= 
#. Create rule for the rss IPV6 tcp:: 
       testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end
       testpmd>start
#. To send IPV6 pkts include TCP ports::
       sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src=RandIP6())/TCP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp175s0f0", count=100)
       testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
Test case: MAC_IPV6_TCP_FRAG:
=============================
#. Create rule for the rss IPV6 tcp:: 
       testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end
       testpmd>start
#. To send ipv6 pkts and IPV6 frag::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src=RandIP6())/IPv6ExtHdrFragment()/TCP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
 
Test case: MAC_IPV4_SCTP:
=========================
#. Create rule for the rss type IPV4 and SCTP, hash keywords with ipv4 sctp and l3 src port l4 dst port::
        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l4-dst-only end key_len 0 queues end / end
        testpmd>start
#. To send IP pkts includ SCTP dport::

         sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP())/SCTP(dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
#. To send IP pkts includ SCTP sport::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(dst=RandIP())/SCTP(sport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
 
Test case: MAC_IPV4_SCTP_FRAG:
==============================
#. Create rule for the rss type IPV4 and SCTP, hash keywords with ipv4 sctp::
        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end
        testpmd>start
#. To send IPV4 pkt include SCTP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(),dst=RandIP())/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(),dst=RandIP())/SCTP()/("X"*480)], iface="enp175s0f0", count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src=RandIP(),dst=RandIP(),frag=4)/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
 
Test case: MAC_NVGRE_IPV4_SCTP:
===============================
#. Create rule for the rss type IPV4 and hash keywords ipv4 sctp src and dst type::   
        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end
        testpmd>start
#. To send NVGRE ip pkts and sctp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src=RandIP(),dst=RandIP())/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
   
Test case: MAC_VXLAN_IPV4_SCTP:
===============================
#. create rule for the rss type IPV4 and hash keywords ipv4 sctp src and dst type::
        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end
        testpmd>start
#. To send VXLAN ip pkts and sctp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/SCTP()/VXLAN()/Ether()/IP(src=RandIP(),dst=RandIP())/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value

Test case: MAC_IPV6_SCTP_PAY:
=============================
#. Create rule for the rss type IPV6 and hash keywords ipv4 sctp src and dst type::
        testpmd>flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end key_len 0 queues end / end
        testpmd>start
#. To send IPV6 pkts and sctp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src=RandIP6())/SCTP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp175s0f0", count=100)
        MAC IPV6 SCTP all+frag:
#. to send IPV6 pkts includ frag::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src=RandIP6())/IPv6ExtHdrFragment()/SCTP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
   
Test case: MAC_IPV4_PPPOD_PPPOE:
================================
#. Create rule for the rss type pppoes type::
        testpmd>flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
        testpmd>start
#. To send pppoe 100pkts::

        sendp([Ether(dst="68:05:ca:a3:28:94")/PPPoE(sessionid=RandShort())/PPP(proto=0x21)/IP(src=RandIP())/UDP(sport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
  
Test case: MAC_IPV4_PPPOD_PPPOE:
================================
#. Create rule for the rss type pppoes::
        testpmd>flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
        testpmd>start
#. To send pppoe pkts::

        sendp([Ether(dst="68:05:ca:a3:28:94")/PPPoE(sessionid=RandShort())/PPP(proto=0x21)/IP(src=RandIP())/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. Verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
 
   
Test case: MAC_IPV4_PPPOD_PPPOE_UDP:
====================================
#. Create rule for the rss type pppoes and hash l3 src , l4 dst port::
        testpmd>flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end
        testpmd>start
#. To send pppoe pkt and include the UPD ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/PPPoE(sessionid=RandShort())/PPP(proto=0x21)/IP(src=RandIP())/UDP(dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. Verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   

Test case: MAC_IPV4_PPPOD_PPPOE_SCTP:
=====================================
#. Create rule for the rss type pppoe and hash sctp keywords::
        testpmd>flow create 0 ingress pattern eth / pppoes / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end
        testpmd>start
#. To send pppoe pkt and include the SCTP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/PPPoE(sessionid=RandShort())/PPP(proto=0x21)/IP(src=RandIP())/SCTP(dport=RandShort())/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. Verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
   
Test case: MAC_IPV4_PPPOD_PPPOE_ICMP:
=====================================
#. Create rule for the rss type pppoe and hash icmp keywords::
        testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
        testpmd>start
#. To send pppoe pkt and include the ICMP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/PPPoE(sessionid=RandShort())/PPP(proto=0x21)/IP(src=RandIP())/ICMP()/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. Verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
 
Test case: MAC_IPV4_GTPU_FRAG:
==============================
#. Create rule for the rss type GTPU and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
        testpmd>start
#. To send GTPU pkts::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x123456)/IP(src=RandIP())/ICMP()/("X"*480)],iface="enp175s0f0",count=100) 
#. To send GTPU PKTS and IPV4 frag::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x123456)/IP(src=RandIP(),frag=6)/("X"*480)],iface="enp175s0f0",count=100) 
        testpmd> stop
#. Verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
  
Test case: MAC_IPV4_GTPU_FRAG_UDP:
==================================
#. create rule for the rss type GTPU and hash l3 src and dst keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end
        testpmd>start
#. to send GTP pkts and include IP pkts and UDP::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x123456)/IP(src=RandIP(),frag=6)/UDP(dport=RandShort())/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
   
  
Test case: MAC_IPV4_GTPU_FRAG_TCP:
==================================
#. create rule for the rss type GTPU and hash l3 src and dst keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
        testpmd>start
#. to send GTP pkts and include IP pkts and tcp::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x123456)/IP(src=RandIP(),frag=6)/TCP(dport=RandShort())/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with 
   differently RSS random value
 
   
Test case: MAC_IPV4_GTPU_FRAG_ICMP:
===================================
#. create rule for the rss type GTPU and hash l3 src and dst keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
        testpmd>start
#. to send GTP pkts and include IP pkts and ICMP::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x123456)/IP(src=RandIP(),frag=6)/ICMP()/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
        verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 64 queues evenly with
        differently RSS random value

Test case: SYMMETRIC_TOEPLITZ_IPV4_PAY: 
=======================================
#. create rule for the rss type symmetric_toeplitz and hash ipv4 src and dst keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IP::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp175s0f0", count=100)
#. to send ip pkts with fix IP and switch src and dst ip address::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp175s0f0", count=100)

   Verbos log:  
   src=A4:BF:01:68:D2:03 - dst=68:05:CA:A3:28:94 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xf84ccd9b - RSS queue=0x1b - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x1b ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

   src=A4:BF:01:68:D2:03 - dst=68:05:CA:A3:28:94 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xf84ccd9b - RSS queue=0x1b - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x1b ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

#. To verify the hash value keep with a same value when the IP has exchanged.

   hash=0xf84ccd9b - RSS queue=0
   hash=0xf84ccd9b - RSS queue=0
   
#. to send ip pkts with fix IP::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="8.8.8.2",dst="5.6.7.8")/("X"*480)], iface="enp175s0f0", count=100)
#. to send ip pkts with fix IP and switch src and dst ip address::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="5.6.7.8",dst="8.8.8.2")/("X"*480)], iface="enp175s0f0", count=100)

   testpmd> stop
   verify 100 pkts has sent, and check the has value has fixed, verify the has value keep with a same value, when the IP has exchanged
   
   		
   Verbose log:
   src=A4:BF:01:68:D2:03 - dst=68:05:CA:A3:28:94 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x772baed3 - RSS queue=0x13 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x13 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
   src=A4:BF:01:68:D2:03 - dst=68:05:CA:A3:28:94 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x772baed3 - RSS queue=0x13 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x13 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
   
#. To verify the hash value keep with a same value when the IP has exchanged.

   0x772baed3 - RSS queue=0x19
   0x772baed3 - RSS queue=0x19
   
    statistics log:
    ------- Forward Stats for RX Port= 0/Queue=19 -> TX Port= 0/Queue=19 -------
    RX-packets: 200            TX-packets: 0              TX-dropped: 0
    
    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 200            RX-dropped: 0             RX-total: 200
    TX-packets: 0              TX-dropped: 0             TX-total: 0
    ----------------------------------------------------------------------------
    
    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 200            RX-dropped: 0             RX-total: 200
    TX-packets: 0              TX-dropped: 0             TX-total: 0
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Test case: SYMMETRIC_TOEPLITZ_IPV4_PAY_FRAG:
============================================
#. create rule for the rss type symmetric_toeplitz and hash ipv4 src and dst keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IP includ frag::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/("X"*480)], iface="enp175s0f0", count=100)
#. to send ip pkts with fix IP includ frag and switch src and dst ip address::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss has has fixed with a same value.
   

Test case: SYMMETRIC_TOEPLITZ_IPV4_UDP:
=======================================
#. create rule for the rss type symmetric_toeplitz and hash UDP src and dst keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IP includ frag and UDP::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/UDP(sport=20,dport=22)/("X"*480)], iface="enp175s0f0", count=100)
#. to send ip pkts with fix IP includ frag and switch src and dst ip address and UDP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/UDP(sport=22,dport=20)/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
Test case: SYMMETRIC_TOEPLITZ_IPV4_UDP_L3SRC_L3DST_L4SRC_L4DST:
===============================================================
#. create rule for the rss type symmetric_toeplitz and hash l3 l4 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp l3-src-only l3-dst-only l4-src-only l4-dst-only end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IP includ frag and UDP::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="1.1.4.1",dst="2.2.2.3")/UDP(sport=20,dport=22)/("X"*480)], iface="enp175s0f0", count=100)
#. to send ip pkts with fix IP includ frag and switch src and dst ip address and UDP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="2.2.2.3",dst="1.1.4.1")/UDP(sport=22,dport=20)/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
Test case: SYMMETRIC_TOEPLITZ_IPV4_TCP:
=======================================
#. create rule for the rss type symmetric_toeplitz and hash TCP keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IP includ frag and TCP::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/TCP(sport=20,dport=22)/("X"*480)], iface="enp175s0f0", count=100)
#. to send ip pkts with fix IP includ frag and switch src and dst ip address and tcp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/TCP(sport=22,dport=20)/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
 
Test case: SYMMETRIC_TOEPLITZ_IPV4_SCTP:
========================================
#. create rule for the rss type symmetric_toeplitz and hash SCTP keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss func symmetric_toeplitz types ipv4-sctp end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IP includ frag and SCTP::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/SCTP(sport=20,dport=22)/("X"*480)], iface="enp175s0f0", count=100)
#. to send ip pkts with fix IP includ frag and switch src and dst ip address and sctp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/SCTP(sport=22,dport=20)/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the has rssh hash keep a fixed value.
   
Test case: SYMMETRIC_TOEPLITZ_IPV4_ICMP:
========================================
#. create rule for the rss type symmetric_toeplitz and hash ICMP keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IP includ frag and ICMP::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/ICMP()/("X"*480)], iface="enp175s0f0", count=100)
#. to send ip pkts with fix IP includ frag and switch src and dst ip address and ICMP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/ICMP()/("X"*480)], iface="enp175s0f0", count=100) 
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash value with a fixed value .
   

Test case: SYMMETRIC_TOEPLITZ_IPV6:
===================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IPV6  pkts with fixed address::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)], iface="enp175s0f0", count=100)
#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)], iface="enp175s0f0", count=100)

#. to send ip pkts with fix IPV6  pkts with fixed address without MAC address::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)], iface="enp175s0f0", count=100)
#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address without mac address::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rssh hash with a fixed value .

Test case: SYMMETRIC_TOEPLITZ_IPV6_PAY:
==========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IPV6  pkts with fixed address and includ IPV6 frag::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/IPv6ExtHdrFragment()/("X" * 80)], iface="enp175s0f0", count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X" * 80)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
   
Test case: SYMMETRIC_TOEPLITZ_IPV6_UDP:
=======================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IPV6  pkts with fixed address and includ IPV6 frag and UDP port::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=30,dport=32)/("X" * 80)], iface="enp175s0f0", count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=30)/("X" * 80)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
 
Test case: SYMMETRIC_TOEPLITZ_IPV6_TCP:
=======================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IPV6  pkts with fixed address and includ IPV6 frag and tcp port::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=30,dport=32)/("X" * 80)], iface="enp175s0f0", count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=30)/("X" * 80)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
   
Test case: SYMMETRIC_TOEPLITZ_IPV6_SCTP:
========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IPV6  pkts with fixed address and includ IPV6 frag and sctp port::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/SCTP(sport=30,dport=32)/("X" * 80)], iface="enp175s0f0", count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=30)/("X" * 80)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   

Test case: SYMMETRIC_TOEPLITZ_IPV6_ICMP:
========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix IPV6  pkts with fixed address and includ IPV6 frag and ICMP port::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/ICMP()/("X" * 80)], iface="enp175s0f0", count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X" * 80)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   

Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV4:
=========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end 
        testpmd>start
#. to send ip pkts with fix nvgre pkts with fixed address and includ frag::

        sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.8",dst="192.168.0.69",frag=6)/("X"*480)], iface="enp175s0f0", count=100)
        sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.69",dst="192.168.0.8",frag=6)/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV4:
=========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end 
        testpmd>start
#. to send ip pkts with fix vxlan pkts with fixed address and includ frag::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/("X"*480)], iface="enp175s0f0", count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/("X"*480)], iface="enp175s0f0", count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
 
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV4_UDP:
=============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix nvgre pkts with fixed address and includ frag and udp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="8.8.8.1",dst="5.6.8.2")/UDP(sport=20,dport=22)/("X"*480)],iface="enp175s0f0",count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="5.6.8.2",dst="8.8.8.1")/UDP(sport=22,dport=20)/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
Test case: SYMMETRIC_TOEPLITZ_NVGRE_SCTP:
=========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss func symmetric_toeplitz types ipv4-sctp end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix nvgre pkts with fixed address and includ frag and sctp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="8.8.8.1",dst="5.6.8.2")/SCTP(sport=20,dport=22)/("X"*480)],iface="enp175s0f0",count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="5.6.8.2",dst="8.8.8.1")/SCTP(sport=22,dport=20)/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV4_TCP:
=============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix nvgre pkts with fixed address and includ frag and tcp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="8.8.8.1",dst="5.6.8.2")/TCP(sport=20,dport=22)/("X"*480)],iface="enp175s0f0",count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="5.6.8.2",dst="8.8.8.1")/TCP(sport=22,dport=20)/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV4_ICMP:
==============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end
        testpmd>start
#. to send ip pkts with fix nvgre pkts with fixed address and includ frag and icmp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src="8.8.8.1",dst="5.6.8.2")/ICMP()/("X"*480)],iface="enp175s0f0",count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src="5.6.8.2",dst="8.8.8.1")/ICMP()/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
 
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV6:
=========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start
#. to send ipv6 pkts with fix nvgre pkts with fixed address::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X"*480)],iface="enp175s0f0",count=100)
#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
 
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV6_UDP:
================================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end
        testpmd>start
#. to send ipv6 pkts with fix nvgre pkts with fixed address and includ ipv6 frag and UDP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=30,dport=32)/("X"*480)],iface="enp175s0f0",count=100)
#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address and udp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
 
   
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV6_TCP:
=============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end
        testpmd>start
#. to send ipv6 pkts with fix nvgre pkts with fixed address and includ ipv6 frag and tcp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=30,dport=32)/("X"*480)],iface="enp175s0f0",count=100)
#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address and tcp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=33)/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
        verify 100 pkts has sent, and check the rss hash with a fixed value.
 
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV6_SCTP
==============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end
        testpmd>start
#. to send ipv6 pkts with fix nvgre pkts with fixed address and includ ipv6 frag and SCTP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/SCTP(sport=30,dport=32)/("X"*480)],iface="enp175s0f0",count=100)
#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address and SCTP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=33)/("X"*480)],iface="enp175s0f0",count=100)
    testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
  
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV6_ICMP:
==============================================
#.  create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start
#. to send ipv6 pkts with fix nvgre pkts with fixed address and includ ipv6 frag and ICMP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/ICMP()/("X"*480)],iface="enp175s0f0",count=100)
#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address and ICMP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
 
Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV6_UDP:
=============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end
        testpmd>start
#. to send ipv6 pkts with fix vxlan pkts with fixed address and includ ipv6 frag and UDP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=30,dport=32)/("X"*480)],iface="enp175s0f0",count=100)
#. to send VXLAN pkts with fix IPv6 includ frag and switch src and dst ip address and UDP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV6:
=========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start
#. to send ipv6 pkts with fix vxlan pkts with fixed address and includ ipv6 frag::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X"*480)],iface="enp175s0f0",count=100)
#. to send VXLAN pkts with fix IPv6 includ frag and switch src and dst ip address::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.

Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV6_TCP:
=============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end
        testpmd>start
#. to send ipv6 pkts with fix vxlan pkts with fixed address and includ ipv6 frag and tcp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=30,dport=32)/("X"*480)],iface="enp175s0f0",count=100)
#. to send VXLAN pkts with fix IPv6 includ frag and switch src and dst ip address and tcp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=33)/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
 
Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV6_SCTP:
==============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end
        testpmd>start
#. to send ipv6 pkts with fix vxlan pkts with fixed address and includ ipv6 frag and sctp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/SCTP(sport=30,dport=32)/("X"*480)],iface="enp175s0f0",count=100)
#. to send VXLAN pkts with fix IPv6 includ frag and switch src and dst ip address and sctp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=30)/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV6_ICMP:
==============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::
        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start
#. to send ipv6 pkts with fix vxlan pkts with fixed address and includ ipv6 frag and ICMP ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/ICMP()/("X"*480)],iface="enp175s0f0",count=100)
#. to send VXLAN pkts with fix IPv6 includ frag and switch src and dst ip address and icmp ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp175s0f0",count=100)
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value
   
 
Test case: SIMPLE_XOR:
======================
#. create rule for the rss type simple_xor::
        testpmd>flow create 0 ingress pattern end actions rss func simple_xor key_len 0 queues end / end
        testpmd>start
   
Test case: SIMPLE_XOR_IPV4:
===========================
#. to send IPV4 pkt with fixed IP and switch IP src and dst address and switch the upd, tcp, sctp, icpm ports::

        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="1.1.4.1",dst="2.2.2.3")/("X"*480)], iface="enp175s0f0", count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="2.2.2.3",dst="1.1.4.1")/("X"*480)], iface="enp175s0f0", count=100)

        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
   Verbose log:
   src=A4:BF:01:68:D2:03 - dst=68:05:CA:A3:28:94 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x3030602 - RSS queue=0x2 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x2 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
	 
   src=A4:BF:01:68:D2:03 - dst=68:05:CA:A3:28:94 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x3030602 - RSS queue=0x2 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x2 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
   
   Chheck the RSS value wiht a same value and the packets enter to a queue
	 
   statistics log: 
   ------- Forward Stats for RX Port= 0/Queue= 2 -> TX Port= 0/Queue= 2 -------
   RX-packets: 200            TX-packets: 0              TX-dropped: 0
   
   ---------------------- Forward statistics for port 0  ----------------------
   RX-packets: 200            RX-dropped: 0             RX-total: 200
   TX-packets: 0              TX-dropped: 0             TX-total: 0
   ----------------------------------------------------------------------------
   
   +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
   RX-packets: 200            RX-dropped: 0             RX-total: 200
   TX-packets: 0              TX-dropped: 0             TX-total: 0
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


SIMPLE_XOR_IPV6:
================
#. to send IPV6 pkt with fixed IP and switch IP src and dst address and switch the upd, tcp, sctp, icpm ports::
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)], iface="enp175s0f0", count=100)
        sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)], iface="enp175s0f0", count=100)
 
        testpmd> stop
#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
   Verbose log:
   src=00:00:00:00:00:00 - dst=68:05:CA:A3:28:94 - type=0x86dd - length=134 - nb_segs=1 - RSS hash=0x5c24be5 - RSS queue=0x25 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV6  - l2_len=14 - l3_len=40 - Receive queue=0x25 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
	 
   src=00:00:00:00:00:00 - dst=68:05:CA:A3:28:94 - type=0x86dd - length=134 - nb_segs=1 - RSS hash=0x5c24be5 - RSS queue=0x25 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV6  - l2_len=14 - l3_len=40 - Receive queue=0x25 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    statistics log: 
    ------- Forward Stats for RX Port= 0/Queue=37 -> TX Port= 0/Queue=37 -------
    RX-packets: 200            TX-packets: 0              TX-dropped: 0
    
    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 200            RX-dropped: 0             RX-total: 200
    TX-packets: 0              TX-dropped: 0             TX-total: 0
    ----------------------------------------------------------------------------
    
    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 200            RX-dropped: 0             RX-total: 200
    TX-packets: 0              TX-dropped: 0             TX-total: 0
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
