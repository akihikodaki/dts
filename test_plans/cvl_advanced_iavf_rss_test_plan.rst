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
CVL: iAvf Advanced RSS FOR CVL
==============================

Description
===========

iAVF Advanced RSS support columbiaville nic with ice , throught create rule include related pattern and input-set
to hash IP and ports domain, diversion the packets to the difference queues in VF.

* inner header hash for tunnel packets, including comms package.
* GTPU_DOWN and GTPU_UP rule creat and package
* symmetric hash by rte_flow RSS action.
* input set change by rte_flow RSS action.
  
Pattern and input set
---------------------
.. table::

    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | Default hash function: Non Symmetric_toeplitz                                                                                                |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | Packet Type                   | Pattern                   | Input Set                                                                        |
    +===============================+===========================+==================================================================================+
    | IPv4/IPv6 + TCP/UDP/SCTP/ICMP | MAC_IPV4_SRC_ONLY         | [Dest MAC]，[Source IP]                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_DST_ONLY_FRAG    | [Dest MAC]，[Dest IP]                                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_PAY              | [Dest MAC]，[Source IP], [Dest IP]                                                |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_SRC_ICMP         | [Dest MAC]，[Source IP]                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_DST_ICMP         | [Dest MAC]，[Source IP]                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_UDP_L3SRC_L4DST  | [Dest MAC]，[Source IP],[Dest Port]                                               |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_UDP              | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_TCP_L3SRC_L4DST  | [Dest MAC]，[Source IP],[Dest Port]                                               |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_TCP_L3DST_L4SRC  | [Dest MAC]，[Dest IP],[Source Port]                                               |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_TCP              | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_SCTP_L3SRC_L4DST | [Dest MAC]，[Source IP],[Dest Port]                                               |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_SCTP             | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_NVGRE_ICMP       | [Inner Source IP], [Inner Dest IP]                                               |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_NVGRE_L3SRC_ICMP | [Inner MAC][Inner Source IP]                                                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_NVGRE_L3DST_ICMP | [Inner MAC][Inner Dest IP]                                                       |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_NVGRE_TCP        | [Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]        |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_NVGRE_SCTP       | [Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]        |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_VXLAN_ICMP       | [Inner Source IP], [Inner Dest IP]                                               |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_VXLAN_L3SRC_ICMP | [Inner MAC][Inner Source IP]                                                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_VXLAN_L3DST_ICMP | [Inner MAC][Inner Dest IP]                                                       |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_VXLAN_TCP        | [Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]        |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_VXLAN_SCTP       | [Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]        |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_VXLAN_UDP        | [Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]        |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_SRC_ONLY         | [Dest MAC]，[Source IP]                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_DST_ONLY_FRAG    | [Dest MAC]，[Dest IP]                                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_PAY              | [Dest MAC]，[Source IP], [Dest IP],                                               |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_UDP              | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_TCP              | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_SCTP             | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_PPPOE_PPPOD      | [Dest MAC]，[Session ID],[Proto] ,[Source IP] ,[Dest IP]                          |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_PPPOE_TCP        | [Dest MAC]，[Session ID],[Proto],[Source IP],[Dest IP],[Source Port],[Dest Port]  |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_PPPOE_UDP        | [Dest MAC]，[Session ID],[Proto],[Source IP],[Dest IP],[Source Port],[Dest Port]  |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_PPPOE_TCP        | [Dest MAC]，[Session ID],[Proto],[Source IP],[Dest IP],[Source Port],[Dest Port]  |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_PPPOE_ICMP       | [Dest MAC]，[Session ID],[Proto],[Source IP],[Dest IP]                            |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_GTPUP       |  [TEID] |GTP_PDUSession_ExtensionHeader                                          |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_GTDWN       |  [TEID] |GTP_PDUSession_ExtensionHeader                                          |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_CVLAN            |  [VLAN ID]                                                                       |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+

.. table::

    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    | Hash function: Symmetric_toeplitz                                                                                                          |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    | Packet Type                   | Pattern                   | Input Set                                                                      |
    +===============================+===========================+================================================================================+
    |  IPV4/IPV6                    | MAC_IPV4_SRC_ONLY         | [Dest MAC]，[Source IP]                                                         |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_DST_ONLY_FRAG    | [Dest MAC]，[Dest IP]                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_PAY              | [Dest MAC]，[Source IP], [Dest IP]                                              |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+ 
    |                               | MAC_IPV4_SRC_ICMP         | [Dest MAC]，[Source IP]                                                         |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_DST_ICMP         | [Dest MAC]，[Source IP]                                                         |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_UDP_L3SRC_L4DST  | [Dest MAC]，[Source IP],[Dest Port]                                             |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_UDP              | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]   |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_TCP_L3SRC_L4DST  | [Dest MAC]，[Source IP],[Dest Port]                                             |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_TCP_L3DST_L4SRC  | [Dest MAC]，[Dest IP],[Source Port]                                             |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_TCP              | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]   |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_SCTP_L3SRC_L4DST | [Dest MAC]，[Source IP],[Dest Port]                                             |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_SCTP             | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]   |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_NVGRE_ICMP       | [Inner Source IP], [Inner Dest IP]                                             |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_NVGRE_L3SRC_ICMP | [Inner MAC][Inner Source IP]                                                   |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_NVGRE_L3DST_ICMP | [Inner MAC][Inner Dest IP]                                                     |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_NVGRE_TCP        | [Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]      |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_NVGRE_SCTP       | [Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]      |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_VXLAN_ICMP       | [Inner Source IP], [Inner Dest IP]                                             |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_VXLAN_L3SRC_ICMP | [Inner MAC][Inner Source IP]                                                   |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_VXLAN_L3DST_ICMP | [Inner MAC][Inner Dest IP]                                                     |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_VXLAN_TCP        | [Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]      |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_VXLAN_SCTP       | [Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]      |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_VXLAN_UDP        | [Inner Source IP], [Inner Dest IP],[Inner Source Port], [Inner Dest Port]      |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV6_SRC_ONLY         | [Dest MAC]，[Source IP]                                                         |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV6_DST_ONLY_FRAG    | [Dest MAC]，[Dest IP]                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV6_PAY              | [Dest MAC]，[Source IP], [Dest IP],                                             |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV6_UDP              | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]   |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV6_TCP              | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]   |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV6_SCTP             | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port]   |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_SIMPLE_XOR       | [Dest MAC]，[Source IP], [Dest IP]                                              |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV6_SIMPLE_XOR       | [Dest MAC]，[Source IP], [Dest IP]                                              |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV4_L2TPv3           | [Session ID]                                                                   |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV6_L2TPv3           | [Session ID]                                                                   |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+  
    |                               | MAC_IPV4_ESP              | [SPI]                                                                          |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV6_ESP              | [SPI]                                                                          |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+  
    |                               | MAC_IPV4_AH               | [SPI]                                                                          |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+    
    |                               | MAC_IPV6_AH               | [SPI]                                                                          |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+  


Default parameters
------------------

   MAC::

    VF0 [Dest MAC]: 00:11:22:33:44:55
    VF1 [Dest MAC]: 00:11:33:44:55:66
	
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

Create a VF interface from kernel PF interfaces, and then attach them to VM. Suppose PF is 0000:b1:00.0 . 
Generate a VF using commands below and make them in pci-stub mods.

NIC: 2x25G or 2x100G, several TC need breakout mode, then 2x100G is required
PF: The 1st PF's PCI address 0000:b1:00.0 , kernel interface name enp177s0f0 . The 2nd PF's PCI address 0000:b1:00.1 , kernel interface name enp177s0f1
VF: The VFs generated by 0000:b1:00.0 , are 0000:b1:02.x , The VFs generated by 0000:b1:00.1 , are 0000:b1:0a.x

Prepare test toplogoy, in the test case, it requires

- 1 Intel E810 interface
- 1 network interface for sending test packet,
  which could be connect to the E810 interface
- Directly connect the 2 interfaces
- Latest driver and comms pkgs of version
- DPDK: http://dpdk.org/git/dpdk
- scapy: http://www.secdev.org/projects/scapy/


Compile DPDK and testpmd::

  make install -j T=x86_64-native-linuxapp-gcc

1. Create 2 VFs from a PF::

      modprobe vfio-pci	
      echo 2 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
      ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55
      ip link set enp177s0f0 vf 1 mac 00:11:55:66:77:88
      
        
2. Bring up PFs::

      ifconfig enp177s0f1 up
      ifconfig enp177s0f0 up

3. Bind the pci device id of DUT in VFs::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0 0000:b1:01.1 0000:b1:01.2

.. note::

   The kernel must be >= 3.6+ and VT-d must be enabled in bios.

4. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -w b1:01.1 --file-prefix=vf -- -i --rxq=16 --txq=16  --nb-cores=2
    testpmd>set fwd rxonly
    testpmd>set verbose 1
    testpmd>rx_vxlan_port add 4789 0
   
5. start scapy and configuration NVGRE and GTP profile in tester
   scapy::

   >>> import sys
   >>> sys.path.append('~/dts/dep')
   >>> from nvgre import NVGRE
   >>> from scapy.contrib.gtp import *

Test case: MAC_IPV4_L3SRC
=========================

#. create rule for the rss type for l3 src only::

    testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end
    testpmd>start

#. send the 100 IP pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP())/("X"*480)], iface="enp177s0f1", count=100)
    testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value,and check the pkts typ is “L2_ETHER L3_IPV4 NONFRAG”

   Verbose log parses and check point example: 
   Once rule has created and receive related packets,
   Check the rss hash value and rss queue, make sure the different hash value and cause to related packets enter difference queue::
   
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x60994f6e - RSS queue=0x2e - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x2e ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
   
statistics log::

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
 
Test case: MAC_IPV4_L3SRC FRAG
==============================

#. create rule for the rss type for l3 src only::

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd> start

#. send the 100 IP +frag type pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP(),frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value,and check the pkts typ is L2_ETHER L3_IPV4 "FRAG"

#. No match case::
#. send the 100 IP change to l3-src-only packages and match to the rule::
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
		
#. Expected got a fixed Hash value.
#. send the 100 IP change to l3-src-only packages::

		sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.5",frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
		
#. Expected got a fixed Hash value, but hash value should different to previous hash value, because the l3 src has changed.
			
		sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8",frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
		
#. Expected got a fixed Hash value, but hash value should keep to first hash value, because the l3 src has no changed.
 
        testpmd> stop

#. Destory rule on port 0
         testpmd> flow flush 0

Test case: MAC_IPV4_L3DST:
==========================

#. create rule for the rss type for l3 dst only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd> start

#. send the 100 IP +frag type pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(dst=RandIP())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value,and check the pkts typ is L2_ETHER L3_IPV4 "FRAG"

#. No match case::
#. send the 100 IP change to l3-src-only packages and match to the rule::
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
		
#. Expected got a fixed Hash value.
#. send the 100 IP change to l3-src-only packages::
	
		sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.5",frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
		
#. Expected got a fixed Hash value, but hash value should keep to first hash value, because the l3 src has no changed.
			
		sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8",frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
		
#. Expected got a fixed Hash value, but hash value should different to previous hash value, because the l3 dst has changed.
  
        testpmd> stop

#. Destory rule on port 0
         testpmd> flow flush 0

Test case: MAC_IPV4_L3DST_FRAG:
=============================== 
#. create rule for the rss type for l3 dst only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd> start
   
#. send the 100 IP frag pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(dst=RandIP(), frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value,and check the pkts typ is L2_ETHER L3_IPV4 "FRAG"
   
#. Destory rule on port 0
         testpmd> flow flush 0

Test case: MAC_IPV4_L3SRC_FRAG_ICMP:
==================================== 
#. create rule for the rss type for l3 dst only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd> start

#. send the 100 IP pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), frag=5)/ICMP()/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0
   
Test case: MAC_IPV4_L3DST_FRAG_ICMP:
====================================
#. create rule for the rss type for l3 dst only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd> start

#. send the 100 IP pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(dst=RandIP(), frag=5)/ICMP()/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. No match case::
#. send the 100 IP change to l3-dst-only packages and match to the rule::
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",frag=5)/ICMP()/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value.		
#. send the 100 IP change to l3-src-only packages::   

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.5",frag=5)/ICMP()/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value, but hash value should keep to previous hash value, because the l3 dst has no changed.

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8",frag=5)/ICMP()/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value, but hash value should different to first hash value, because the l3 dst has changed.

        testpmd> stop

#. Destory rule on port 0 
         testpmd> flow flush 0   

Test case: MAC_IPV4_PAY:
========================
#. create rule for the rss type for l3 all keywords::

        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
        testpmd> start

#. send the 100 IP pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd>stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. Destory rule on port 0 
         testpmd> flow flush 0 
 
Test case: MAC_IPV4_PAY_FRAG_ICMP:
==================================
#. create rule for the rss type for IPV4 l3 all (src and dst) +frag+ICMP::

        flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
   
#. send the 100 IP pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/ICMP()/("X"*480)], iface="enp177s0f1", count=100)
        testpmd>stop
   
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. Destory rule on port 0 
         testpmd> flow flush 0 

Test case: MAC_IPV4_NVGRE_L3SRC:
================================
#. create rule for the rss type is IPV4 l3 src +NVGRE inner IPV4 +frag + ICMP::

        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd> start

#. send the 100 IP nvgre pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IP(src=RandIP(),dst=RandIP())/ICMP()/("X"*480)],iface="enp177s0f1",count=100)

        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. Destory rule on port 0
         testpmd> flow flush 0
  
Test case: MAC_IPV4_NVGRE_L3DST:
================================
#. create rule for the rss type is IPV4 l3 dst +NVGRE inner IPV4 +frag + ICMP::

        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd> start

#. send the 100 IP nvgre pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IP(dst=RandIP())/ICMP()/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value.

#. Destory rule on port 0 
         testpmd> flow flush 0         
  
Test case: MAC_IPV4_VXLAN_L3SRC:
================================
#. create rule for the rss type is IPV4 src VXLAN +frag +ICMP:: 

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd>start

#. send the 100 VXLAN pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src=RandIP(), frag=5)/ICMP()/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_VXLAN_L3DST:
================================
#. create rule for the rss type is IPV4 dst VXLAN +frag+ICMP::
   
        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd>start

#. send the 100 vxlan pkts::
   
        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(dst=RandIP(), frag=5)/ICMP()/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0
 
Test case: MAC_IPV4_VXLAN:
==========================
#. create rule for the rss type is IPV4 all VXLAN +frag +ICMP::

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss types end key_len 0 queues end / end
        testpmd>start
   
#. send the 100 vxlan pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src=RandIP(),dst=RandIP(),frag=5)/ICMP()/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value 

#. Destory rule on port 0 
         testpmd> flow flush 0

DCF-Test case: MAC_IPV6_L3SRC
==========================
#. create rule for the rss type is IPV6 L3 src::

        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd>start

#. send the 100 IPV6 pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src=RandIP6())/("X" * 80)], iface="enp177s0f1", count=100)

#. No match::
       flow flush 0
#. send the 100 IPV6 pkts::
       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src=RandIP6())/("X" * 80)], iface="enp177s0f1", count=100)
       then will not receive any rss packages

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV6_L3SRC_FRAG
===============================
#. create rule for the rss type is IPV6 L3 src +ExtHdrFragment::

        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd>start
   
#. send the 100 IPV6 pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src=RandIP6())/IPv6ExtHdrFragment()/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. No match case::
#. send the 100 IP change to l3-src-only packages and match to the rule::
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/IPv6ExtHdrFragment()/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value.
#. send the 100 IP change to l3-src-only packages::   

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="CDCD:910A:2222:5498:8475:1111:3900:8282",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
		
#. Expected got a fixed Hash value, but hash value should different to previous hash value, because the l3 src has changed.

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2626")/IPv6ExtHdrFragment()/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value, but hash value should keep to first hash value, because the l3 dst has changed.
 
        testpmd> stop

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV6_L3DST
=========================
#. create rule for the rss type is IPV6 L3 dst +ExtHdrFragment::

        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd>start

#. send the 100 IPV6 pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst=RandIP6())/IPv6ExtHdrFragment()/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. No match case::
#. send the 100 IP change to l3-src-only packages and match to the rule::
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/IPv6ExtHdrFragment()/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value.
#. send the 100 IP change to l3-src-only packages::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="CDCD:910A:2222:5498:8475:1111:3900:8282",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value, but hash value should keep to first hash value, because the l3 src changed but l3 dst no change.

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2626")/IPv6ExtHdrFragment()/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value, but hash value should different to previous hash value, because the l3 dst has changed.

#. Destory rule on port 0 
         testpmd> flow flush 0
 
Test case: MAC_IPV6_PAY
=======================
#. create rule for the rss type is IPV6 L3 all +ExtHdrFragment+ICMP::

        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end
        testpmd>start

#. send the 100 IPV6 pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src=RandIP6(),dst=RandIP6())/IPv6ExtHdrFragment()/ICMP()/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop
   
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_UDP: 
========================
#. create rule for the rss type is ipv4 UDP +l3 src and dst::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l3-src-only l4-dst-only end key_len 0 queues end / end
        testpmd>start
        
        flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l3-src-only l4-dst-only end key_len 0 queues end / end

#. send the 100 IP+UDP pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP())/UDP(dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)

        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. No match case::
#. send the 100 IP change to l3-src-only packages and match to the rule::
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",frag=5)/UDP(sport=22,dport=33)/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value.
#. send the 100 IP change to l3-src-only  and l4 dport packages::   

         sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.4",dst="192.168.0.5",frag=5)/UDP((sport=22,dport=55)/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value, but hash value should different to previous hash value, because the l3 src and l4 dst has changed.

          sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.9",frag=5)/UDP(sport=16,dport=33)/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value, but hash value should keep to first hash value, because the l3 src  and l4 dst has no changed.

        testpmd> stop  

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_UDP_FRAG:
=============================
#. create rule for the rss type is ipv4 +UDP +frag::

        testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
        testpmd> start

#. send the 100 IP src IP +UDP port pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
   
#. send the 100 IP +UDP port pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)

#. send the 100 IP src and dst IP  +UDP port pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/UDP()/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop
   
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. Destory rule on port 0 
         testpmd> flow flush 0
      
   
Test case: MAC_NVGRE_IPV4_UDP_FRAG:
===================================  
#. create rule for the rss type is ipv4 + inner IP and UDP:: 

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
        testpmd>start
   
#. send the 100 NVGRE IP pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_VXLAN_IPV4_UDP_FRAG:
=================================== 
#. create rule for the rss type is ipv4 + vxlan UDP:: 

        testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
        testpmd> start

#. To send VXLAN pkts with IP src and dst,UDP port::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV6_UDP:
========================
#. create rule for the rss type is IPV6 + UDP src and dst type hash::

        testpmd> flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
        testpmd> start
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src=RandIP6())/UDP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV6_UDP_FRAG:   
=============================
#. To send IPV6 pkts with IPV6 src +frag +UDP port::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src=RandIP6())/IPv6ExtHdrFragment()/UDP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_TCP_FRAG:
=============================
#. create rule for the rss type is IPV4 + TCP L3 src and  L4 dst type hash::

        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types l3-src-only l4-dst-only end key_len 0 queues end / end


#. To send IPV4 pkts with scr IP and TCP dst port::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP())/TCP(dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. No match case::
#. send the 100 IP change to l3-src-only packages and match to the rule::
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",frag=5)/TCP(sport=22,dport=33)/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value.
#. send the 100 IP change to l3-src-only  and l4 dport packages::   

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.4",dst="192.168.0.5",frag=5)/TCP((sport=22,dport=55)/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value, but hash value should different to previous hash value, because the l3 src and l4 dst has changed.

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.9",frag=5)/TCP(sport=16,dport=33)/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value, but hash value should keep to first hash value, because the l3 src  and l4 dst has no changed.

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_TCP_PAY
===========================
#. Create rule for the rss type is IPV4 +tcp and hash tcp src and dst ports::

        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end
        testpmd>start

#. To send IPV4 pkts with IP src and dst ip and TCP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)

#. To send IPV4 pkts without IP src and dst ip and includ TCP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)

#. To send IPV4 pkts with IP src and dst ip and without TCP port::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/TCP()/("X"*480)], iface="enp177s0f1", count=100)

#. To send IPV4 pkts with IP src and dst +frag and without TCP port::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP(),frag=4)/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0
   
 
Test case: MAC_IPV6_UDP_FRAG:   
=============================
#. Create rule for the RSS type nvgre IP src dst ip and TCP::

        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end
        testpmd>start

#. To send NVGRE ip pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IP(src=RandIP(),dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_VXLAN_IPV4_TCP
=============================  
#. Create rule for the rss type is IPV4 +tcp and hash tcp src and dst ports::

        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end
        testpmd>start

#. To send VXLAN pkts includ src and dst ip and TCP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/TCP()/VXLAN()/Ether()/IP(src=RandIP(),dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV6_TCP
======================= 
#. Create rule for the rss IPV6 tcp:: 

       testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end
       testpmd>start

#. To send IPV6 pkts include TCP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src=RandIP6())/TCP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV6_TCP_FRAG:
=============================
#. Create rule for the rss IPV6 tcp:: 

        testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end
        testpmd>start

#. To send ipv6 pkts and IPV6 frag::
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src=RandIP6(),dst=RandIP6())/IPv6ExtHdrFragment()/TCP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_SCTP:
=========================
#. Create rule for the rss type IPV4 and SCTP, hash keywords with ipv4 sctp and l3 src port l4 dst port::

        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types l3-src-only l4-dst-only end key_len 0 queues end / end
        testpmd>start

#. To send IP pkts includ SCTP dport::

         sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP())/SCTP(dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. No match case::
#. send the 100 IP change to l3-src-only packages and match to the rule::
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",frag=5)/SCTP(sport=22,dport=33)/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value.
#. send the 100 IP change to l3-src-only  and l4 dport packages::   
         sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.4",dst="192.168.0.5",frag=5)/SCTP((sport=22,dport=55)/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value, but hash value should different to previous hash value, because the l3 src and l4 dst has changed.

         sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.9",frag=5)/SCTP(sport=16,dport=33)/("X" * 80)], iface="enp177s0f1", count=100)

#. Expected got a fixed Hash value, but hash value should keep to first hash value, because the l3 src  and l4 dst has no changed.
        testpmd> stop  

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_SCTP_FRAG:
==============================
#. Create rule for the rss type IPV4 and SCTP, hash keywords with ipv4 sctp::

        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end
        testpmd>start

#. To send IPV4 pkt include SCTP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP()/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/SCTP()/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_NVGRE_IPV4_SCTP:
===============================
#. Create rule for the rss type IPV4 and hash keywords ipv4 sctp src and dst type::   

        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end
        testpmd>start

#. To send NVGRE ip pkts and sctp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IP(src=RandIP(),dst=RandIP())/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_VXLAN_IPV4_SCTP:
===============================
#. create rule for the rss type IPV4 and hash keywords ipv4 sctp src and dst type::

        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end
        testpmd>start

#. To send VXLAN ip pkts and sctp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/SCTP()/VXLAN()/Ether()/IP(src=RandIP(),dst=RandIP())/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV6_SCTP_PAY:
=============================
#. Create rule for the rss type IPV6 and hash keywords ipv4 sctp src and dst type::

        testpmd>flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end key_len 0 queues end / end
        testpmd>start

#. To send IPV6 pkts and sctp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src=RandIP6())/SCTP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
        MAC IPV6 SCTP all+frag:

#. to send IPV6 pkts includ frag::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src=RandIP6())/IPv6ExtHdrFragment()/SCTP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_PPPOD_PPPOE:
================================
#. Create rule for the rss type pppoes type::

        testpmd>flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
        testpmd>start

#. To send pppoe 100pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/PPPoE(sessionid=RandShort())/PPP(proto=0x21)/IP(src=RandIP())/UDP(sport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_PPPOD_PPPOE:
================================
#. Create rule for the rss type pppoes::

        testpmd>flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
        testpmd>start

#. To send pppoe pkts::

        sendp([Ether(dst="00:11:22:33:44:55")/PPPoE(sessionid=RandShort())/PPP(proto=0x21)/IP(src=RandIP())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. Verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_PPPOD_PPPOE_UDP:
====================================
#. Create rule for the rss type pppoes and hash l3 src , l4 dst port::

        testpmd>flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end
        testpmd>start

#. To send pppoe pkt and include the UPD ports::

        sendp([Ether(dst="00:11:22:33:44:55")/PPPoE(sessionid=RandShort())/PPP(proto=0x21)/IP(src=RandIP())/UDP(dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. Verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value

Test case: MAC_IPV4_PPPOD_PPPOE_SCTP:
=====================================
#. Create rule for the rss type pppoe and hash sctp keywords::

        testpmd>flow create 0 ingress pattern eth / pppoes / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end
        testpmd>start

#. To send pppoe pkt and include the SCTP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/PPPoE(sessionid=RandShort())/PPP(proto=0x21)/IP(src=RandIP())/SCTP(dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. Verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0


Test case: MAC_IPV4_PPPOD_PPPOE_ICMP:
=====================================
#. Create rule for the rss type pppoe and hash icmp keywords::

        testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
        testpmd>start

#. To send pppoe pkt and include the ICMP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/PPPoE(sessionid=RandShort())/PPP(proto=0x21)/IP(src=RandIP())/ICMP()/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. Verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0   

Test case: MAC_IPV4_GTPU_GTPUP_L3SRC_ONLY_MATCH and NO MATCHED:
==============================================================
Matched package case :
#. Create rule for the rss type GTPU UP and hash l3 src keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd>start

#. To send matched GTPU_UP pkts::

        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP())/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. Verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

NO Matched package case :
#. Create rule for the rss type GTPU UP and hash l3 src package keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd>start

#. To send no matched GTPU_UP pkts::
        sendp([Ether(src="00:00:00:00:01:01", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(dst=RandIP())/("X"*480)],iface="enp177s0f01", count=100) 

        sendp([Ether(src="00:00:00:00:01:01", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(dst=RandIP())/("X"*480)],iface="enp177s0f1", count=100) 

        sendp([Ether(src="00:00:00:00:01:01", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(src=RandIP())/("X"*480)],iface="enp177s0f1", count=100) 
        testpmd> stop

#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue 

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_GTPU_GTPDOWN_L3SRC_ONLY_MATCH and NO MATCHED:
================================================================
Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_DOWN pkts::	
        sendp([Ether(src="00:00:00:00:01:01", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(dst=RandIP())/("X"*480)],iface="enp177s0f1", count=100) 	
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

NO Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 dst keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_DOWN pkts:
        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP())/("X"*480)],iface="enp177s0f1", count=100) 
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue 

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_GTPU_UP_IPV4_FRAG_MATCH and NO MATCHED:
===========================================================
Matched package case:
#. Create rule for the rss type GTPU UP and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end 
        testpmd>start
#. To send matched GTPU_UP pkts::
        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP(),frag=6)/("X"*480)],iface="enp177s0f01", count=100)  
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

NO Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end 
        testpmd>start
#. To send matched GTPU_DOWN pkts::
         sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(dst=RandIP(),frag=6)/("X"*480)],iface="enp177s0f01", count=100) 
         testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue 

#. Destory rule on port 0 
         testpmd> flow flush 0
   
Test case: MAC_IPV4_GTPU_DOWN_IPV4_FRAG_MATCH and NO MATCHED:
============================================================
Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end 
        testpmd>start
#. To send matched GTPU_DOWN pkts::	
        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(dst=RandIP(),frag=6)/("X"*480)],iface="enp177s0f01", count=100)  
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

NO Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 dst keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end 
        testpmd>start
#. To send matched GTPU_DOWN pkts::
        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(src=RandIP(),frag=6)/("X"*480)],iface="enp177s0f01", count=100)  
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue 

#. Destory rule on port 0 
         testpmd> flow flush 0


Test case: MAC_IPV4_GTPU_UP_UDP_FRAG_MATCH and NO MATCHED:
=======================================================
Matched package case:
#. Create rule for the rss type GTPU UP and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_UP pkts::
        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP())/UDP(dport=RandShort())/("X"*480)],iface="enp177s0f01", count=100)  
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

NO Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 dst keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_DOWN pkts::
         sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(dst=RandIP())/UDP(dport=RandShort())/("X"*480)],iface="enp177s0f01", count=100)
         testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue 

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_GTPU_DOWN_UDP_FRAG_MATCH and NO MATCHED:
===========================================================
Matched package case:
#. Create rule for the rss type GTPU UP and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_UP pkts::
        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(dst=RandIP())/UDP(dport=RandShort())/("X"*480)],iface="enp177s0f01", count=100)  
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

NO Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 dst keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_DOWN pkts::
         sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(dst=RandIP())/UDP(dport=RandShort())/("X"*480)],iface="enp177s0f01", count=100)
         testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue 

#. Destory rule on port 0 
         testpmd> flow flush 0
   
Test case: MAC_IPV4_GTPU_UP_TCP_FRAG_MATCH and NO MATCHED:
===========================================================
Matched package case:
#. Create rule for the rss type GTPU UP and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types l3-src-only end key_len 0 queues end / end
#. To send matched GTPU_UP pkts::
        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)()/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP())/TCP(dport=RandShort())/("X"*480)],iface="enp177s0f1",count=100)  
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

NO Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_DOWN pkts::
         sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(dst=RandIP())/TCP(dport=RandShort())/("X"*480)],iface="enp177s0f01", count=100)
         testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue 

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_GTPU_DOWN_TCP_MATCH and NO MATCHED:
=======================================================
Matched package case:
#. Create rule for the rss type GTPU UP and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types l3-dst-only end key_len 0 queues end / end
#. To send matched GTPU_UP pkts::
        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(dst=RandIP())/TCP(dport=RandShort())/("X"*480)],iface="enp177s0f01", count=100)  
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

NO Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 dst keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_DOWN pkts::
         sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(src=RandIP())/TCP(dport=RandShort())/("X"*480)],iface="enp177s0f01", count=100)
         testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue 

#. Destory rule on port 0 
         testpmd> flow flush 0
   

Test case: MAC_IPV4_GTPU_UP_ICMP_MATCH and NO MATCHED:
======================================================
Matched package case:
#. Create rule for the rss type GTPU UP and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end
#. To send matched GTPU_UP pkts::
        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP())/ICMP()/("X"*480)],iface="enp177s0f01", count=100)  
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

NO Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_DOWN pkts::
         sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(dst=RandIP())/ICMP()/("X"*480)],iface="enp177s0f1", count=100)
         testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue 

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_GTPU_DOWN_ICMP_MATCH and NO MATCHED:
========================================================
Matched package case:
#. Create rule for the rss type GTPU UP and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
#. To send matched GTPU_UP pkts::
        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(dst=RandIP())/ICMP()/("X"*480)],iface="enp177s0f1", count=100)  
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

NO Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 dst keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_DOWN pkts::
         sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(src=RandIP())/ICMP()/("X"*480)],iface="enp177s0f1", count=100)
         testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_GTPU_UP_SCTP_MATCH and NO MATCHED:
===========================================================
Matched package case:
#. Create rule for the rss type GTPU UP and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end
#. To send matched GTPU_UP pkts::
        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP())/SCTP()/("X"*480)],iface="enp177s0f1", count=100)  
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

NO Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_DOWN pkts::
         sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(dst=RandIP())/SCTP()/("X"*480)],iface="enp177s0f1", count=100)
         testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue 

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_GTPU_DOWN_SCTP_MATCH and NO MATCHED:
===========================================================
Matched package case:
#. Create rule for the rss type GTPU UP and hash l3 src keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
#. To send matched GTPU_UP pkts::
        sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(dst=RandIP())/SCTP()/("X"*480)],iface="enp177s0f1", count=100) 
        testpmd> stop
#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue

NO Matched package case:
#. Create rule for the rss type GTPU DOWN and hash l3 dst keywords::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
        testpmd>start
#. To send matched GTPU_DOWN pkts::
         sendp([Ether(src="00:00:00:00:01:01",dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(src=RandIP())/SCTP()/("X"*480)],iface="enp177s0f1", count=100)
         testpmd> stop

#. Verify 100 pkts has sent, but the RSS hash with fix value and not enter to differently queue 

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_CVLAN:
==========================
#. Create rule for the rss type cVLAN and hash l3 src keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss types c-vlan end key_len 0 queues end / end
        testpmd>start

#. To send C-VLAN pkts WITH CTAG8100::

         sendp([Ether()/Dot1Q(vlan=2)/IP(src=RandIP())/UDP()/("X"*480)], iface="enp177s0f1", count=100)

        testpmd> stop
#. To send C-VLAN pkts WITH CTAG8100+CTA8100::

         sendp([Ether(type=0x8100)/Dot1Q(vlan=23)/Dot1Q(vlan=56)/IP(src=RandIP())/UDP()/("X"*480)], iface="enp177s0f1", count=100)

        testpmd> stop
#. To send C-VLAN pkts WITH STAG (88a8) + CTAG (8100)::

         sendp([Ether()/Dot1AD(vlan=56)/Dot1Q(vlan=23)/IP()/UDP()], iface="enp177s0f1",loop=1,inter=0.3) 

        testpmd> stop

#. Verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV4_PAY: 
=======================================
#. create rule for the rss type symmetric_toeplitz and hash ipv4 src and dst keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IP::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp177s0f1", count=100)

#. to send ip pkts with fix IP and switch src and dst ip address::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp177s0f1", count=100)

Verbos log:: 

    src=A4:BF:01:68:D2:03 - dst=00:11:22:33:44:55 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xf84ccd9b - RSS queue=0x1b - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x1b ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    src=A4:BF:01:68:D2:03 - dst=00:11:22:33:44:55 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xf84ccd9b - RSS queue=0x1b - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x1b ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

#. To verify the hash value keep with a same value when the IP has exchanged::

        hash=0xf84ccd9b - RSS queue=0
        hash=0xf84ccd9b - RSS queue=0
   
#. to send ip pkts with fix IP::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="8.8.8.2",dst="5.6.7.8")/("X"*480)], iface="enp177s0f1", count=100)

#. to send ip pkts with fix IP and switch src and dst ip address::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="5.6.7.8",dst="8.8.8.2")/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

verify 100 pkts has sent, and check the has value has fixed, verify the has value keep with a same value, when the IP has exchanged
Verbose log::

        src=A4:BF:01:68:D2:03 - dst=00:11:22:33:44:55 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x772baed3 - RSS queue=0x13 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x13 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
        src=A4:BF:01:68:D2:03 - dst=00:11:22:33:44:55 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x772baed3 - RSS queue=0x13 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x13 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

#. To verify the hash value keep with a same value when the IP has exchanged::

        0x772baed3 - RSS queue=0x19
        0x772baed3 - RSS queue=0x19

statistics log::

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


#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV4_PAY_FRAG:
============================================
#. create rule for the rss type symmetric_toeplitz and hash ipv4 src and dst keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IP includ frag::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/("X"*480)], iface="enp177s0f1", count=100)

#. to send ip pkts with fix IP includ frag and switch src and dst ip address::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss has has fixed with a same value.

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV4_UDP:
=======================================
#. create rule for the rss type symmetric_toeplitz and hash UDP src and dst keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IP includ frag and UDP::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/UDP(sport=20,dport=22)/("X"*480)], iface="enp177s0f1", count=100)

#. to send ip pkts with fix IP include frag and switch src and dst ip address and UDP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/UDP(sport=22,dport=20)/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV4_UDP_L3SRC_L3DST_L4SRC_L4DST:
===============================================================
#. create rule for the rss type symmetric_toeplitz and hash l3 l4 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp l3-src-only l3-dst-only l4-src-only l4-dst-only end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IP includ frag and UDP::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.4.1",dst="2.2.2.3")/UDP(sport=20,dport=22)/("X"*480)], iface="enp177s0f1", count=100)

#. to send ip pkts with fix IP includ frag and switch src and dst ip address and UDP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="2.2.2.3",dst="1.1.4.1")/UDP(sport=22,dport=20)/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV4_TCP:
=======================================
#. create rule for the rss type symmetric_toeplitz and hash TCP keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IP includ frag and TCP::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/TCP(sport=20,dport=22)/("X"*480)], iface="enp177s0f1", count=100)

#. to send ip pkts with fix IP includ frag and switch src and dst ip address and tcp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/TCP(sport=22,dport=20)/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
#. Destory rule on port 0 
         testpmd> flow flush 0      
 
Test case: SYMMETRIC_TOEPLITZ_IPV4_SCTP:
========================================
#. create rule for the rss type symmetric_toeplitz and hash SCTP keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss func symmetric_toeplitz types ipv4-sctp end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IP includ frag and SCTP::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/SCTP(sport=20,dport=22)/("X"*480)], iface="enp177s0f1", count=100)

#. to send ip pkts with fix IP includ frag and switch src and dst ip address and sctp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/SCTP(sport=22,dport=20)/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the has rssh hash keep a fixed value.

#. Destory rule on port 0
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV4_ICMP:
========================================
#. create rule for the rss type symmetric_toeplitz and hash ICMP keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IP includ frag and ICMP::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/ICMP()/("X"*480)], iface="enp177s0f1", count=100)

#. to send ip pkts with fix IP includ frag and switch src and dst ip address and ICMP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/ICMP()/("X"*480)], iface="enp177s0f1", count=100) 
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash value with a fixed value .

#. Destory rule on port 0
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV6:
===================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IPV6  pkts with fixed address::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)], iface="enp177s0f1", count=100)

#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)], iface="enp177s0f1", count=100)

#. to send ip pkts with fix IPV6  pkts with fixed address without MAC address::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)], iface="enp177s0f1", count=100)

#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address without mac address::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rssh hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV6_PAY:
==========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IPV6  pkts with fixed address and includ IPV6 frag::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/IPv6ExtHdrFragment()/("X" * 80)], iface="enp177s0f1", count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV6_UDP:
=======================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IPV6  pkts with fixed address and includ IPV6 frag and UDP port::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=30,dport=32)/("X" * 80)], iface="enp177s0f1", count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=30)/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV6_TCP:
=======================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IPV6  pkts with fixed address and includ IPV6 frag and tcp port::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=30,dport=32)/("X" * 80)], iface="enp177s0f1", count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=30)/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV6_SCTP:
========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IPV6  pkts with fixed address and includ IPV6 frag and sctp port::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/SCTP(sport=30,dport=32)/("X" * 80)], iface="enp177s0f1", count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=30)/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_IPV6_ICMP:
========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix IPV6  pkts with fixed address and includ IPV6 frag and ICMP port::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/ICMP()/("X" * 80)], iface="enp177s0f1", count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV4:
=========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end 
        testpmd>start

#. to send ip pkts with fix nvgre pkts with fixed address and includ frag::

        sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.8",dst="192.168.0.69",frag=6)/("X"*480)], iface="enp177s0f1", count=100)
        sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.69",dst="192.168.0.8",frag=6)/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV4:
=========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end 
        testpmd>start

#. to send ip pkts with fix vxlan pkts with fixed address and includ frag::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/("X"*480)], iface="enp177s0f1", count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV4_UDP:
=============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix nvgre pkts with fixed address and includ frag and udp ports::

       sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether(dst="00:11:22:33:44:55")/IP(src="8.8.8.1",dst="5.6.8.2")/UDP(sport=20,dport=22)/("X"*480)],iface="enp177s0f1",count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether(dst="00:11:22:33:44:55")/IP(src="5.6.8.2",dst="8.8.8.1")/UDP(sport=22,dport=20)/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_NVGRE_SCTP:
=========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss func symmetric_toeplitz types ipv4-sctp end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix nvgre pkts with fixed address and includ frag and sctp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether(dst="00:11:22:33:44:55")/IP(src="8.8.8.1",dst="5.6.8.2")/SCTP(sport=20,dport=22)/("X"*480)],iface="enp177s0f1",count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether(dst="00:11:22:33:44:55")/IP(src="5.6.8.2",dst="8.8.8.1")/SCTP(sport=22,dport=20)/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
#. Destory rule on port 0 
         testpmd> flow flush 0      

Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV4_TCP:
=============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix nvgre pkts with fixed address and includ frag and tcp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether(dst="00:11:22:33:44:55")/IP(src="8.8.8.1",dst="5.6.8.2")/TCP(sport=20,dport=22)/("X"*480)],iface="enp177s0f1",count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether(dst="00:11:22:33:44:55")/IP(src="5.6.8.2",dst="8.8.8.1")/TCP(sport=22,dport=20)/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV4_ICMP:
==============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV4 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end
        testpmd>start

#. to send ip pkts with fix nvgre pkts with fixed address and includ frag and icmp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IP(src="8.8.8.1",dst="5.6.8.2")/ICMP()/("X"*480)],iface="enp177s0f1",count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IP(src="5.6.8.2",dst="8.8.8.1")/ICMP()/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0      
 
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV6:
=========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start

#. to send ipv6 pkts with fix nvgre pkts with fixed address::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X"*480)],iface="enp177s0f1",count=100)

#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0      
 
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV6_UDP:
================================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end
        testpmd>start

#. to send ipv6 pkts with fix nvgre pkts with fixed address and includ ipv6 frag and UDP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=30,dport=32)/("X"*480)],iface="enp177s0f1",count=100)

#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address and udp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.
 
#. Destory rule on port 0 
         testpmd> flow flush 0      
   
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV6_TCP:
=============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end
        testpmd>start

#. to send ipv6 pkts with fix nvgre pkts with fixed address and includ ipv6 frag and tcp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=30,dport=32)/("X"*480)],iface="enp177s0f1",count=100)

#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address and tcp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=33)/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop
        verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0      

 
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV6_SCTP
==============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end
        testpmd>start

#. to send ipv6 pkts with fix nvgre pkts with fixed address and includ ipv6 frag and SCTP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/SCTP(sport=30,dport=32)/("X"*480)],iface="enp177s0f1",count=100)

#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address and SCTP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=33)/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0      
   
  
Test case: SYMMETRIC_TOEPLITZ_NVGRE_IPV6_ICMP:
==============================================
#.  create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start

#. to send ipv6 pkts with fix nvgre pkts with fixed address and includ ipv6 frag and ICMP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/ICMP()/("X"*480)],iface="enp177s0f1",count=100)

#. to send ip pkts with fix IPv6 includ frag and switch src and dst ip address and ICMP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.
 
#. Destory rule on port 0 
         testpmd> flow flush 0      

Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV6_UDP:
=============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end
        testpmd>start

#. to send ipv6 pkts with fix vxlan pkts with fixed address and includ ipv6 frag and UDP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=30,dport=32)/("X"*480)],iface="enp177s0f1",count=100)

#. to send VXLAN pkts with fix IPv6 includ frag and switch src and dst ip address and UDP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0      
   
   
Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV6:
=========================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start

#. to send ipv6 pkts with fix vxlan pkts with fixed address and includ ipv6 frag::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X"*480)],iface="enp177s0f1",count=100)

#. to send VXLAN pkts with fix IPv6 includ frag and switch src and dst ip address::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0     

Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV6_TCP:
=============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end
        testpmd>start

#. to send ipv6 pkts with fix vxlan pkts with fixed address and includ ipv6 frag and tcp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=30,dport=32)/("X"*480)],iface="enp177s0f1",count=100)

#. to send VXLAN pkts with fix IPv6 includ frag and switch src and dst ip address and tcp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=33)/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0 
 
Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV6_SCTP:
==============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end
        testpmd>start

#. to send ipv6 pkts with fix vxlan pkts with fixed address and includ ipv6 frag and sctp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/SCTP(sport=30,dport=32)/("X"*480)],iface="enp177s0f1",count=100)

#. to send VXLAN pkts with fix IPv6 includ frag and switch src and dst ip address and sctp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=30)/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.

#. Destory rule on port 0 
         testpmd> flow flush 0
   
Test case: SYMMETRIC_TOEPLITZ_VXLAN_IPV6_ICMP:
==============================================
#. create rule for the rss type symmetric_toeplitz and hash IPV6 keywords::

        testpmd>flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
        testpmd>start

#. to send ipv6 pkts with fix vxlan pkts with fixed address and includ ipv6 frag and ICMP ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/ICMP()/("X"*480)],iface="enp177s0f1",count=100)

#. to send VXLAN pkts with fix IPv6 includ frag and switch src and dst ip address and icmp ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp177s0f1",count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_IPV4_L2TPv3:
===========================
#. DUT create rule for the RSS type for MAC_IPV4_L2TPv3::

        testpmd>flow create 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end
        testpmd>start

#. Tester use scapy to send the 100 MAC_IPV4_L2TPv3 pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3", proto=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in differently 16 queues evenly with differently RSS hash value::

        testpmd> stop

#. check the flow can be listed and destory rule on port 0::

        testpmd> flow list 0
        ID      Group   Prio    Attr    Rule
        0       0       0       i--     ETH IPV4 L2TPV3OIP => RSS
        testpmd> flow flush 0

#. Tester use scapy to send the 100 MAC_IPV4_L2TPv3 pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3", proto=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in the same queue.

Test case: MAC_IPV6_L2TPv3:
===========================
#. DUT create rule for the RSS type for MAC_IPV6_L2TPv3::

        testpmd>flow create 0 ingress pattern eth / ipv6 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end
        testpmd>start

#. Tester use scapy to send the 100 MAC_IPV6_L2TPv3 pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in differently 16 queues evenly with differently RSS hash value::

        testpmd> stop

#. check the flow can be listed and destory rule on port 0::

        testpmd> flow list 0
        ID      Group   Prio    Attr    Rule
        0       0       0       i--     ETH IPV6 L2TPV3OIP => RSS
        testpmd> flow flush 0

#. Tester use scapy to send the 100 MAC_IPV6_L2TPv3 pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in the same queue.

Test case: MAC_IPV4_ESP:
========================
#. DUT create rule for the RSS type for MAC_IPV4_ESP::

        testpmd>flow create 0 ingress pattern eth / ipv4 / esp / end actions rss types esp end key_len 0 queues end / end
        testpmd>start

#. Tester use scapy to send the 100 MAC_IPV4_ESP pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=50)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in differently 16 queues evenly with differently RSS hash value::

        testpmd> stop

#. check the flow can be listed and destory rule on port 0::

        testpmd> flow list 0
        ID      Group   Prio    Attr    Rule
        0       0       0       i--     ETH IPV4 ESP => RSS
        testpmd> flow flush 0

#. Tester use scapy to send the 100 MAC_IPV4_ESP pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=50)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in the same queue.

Test case: MAC_IPV6_ESP:
========================
#. DUT create rule for the RSS type for MAC_IPV6_ESP::

        testpmd>flow create 0 ingress pattern eth / ipv6 / esp / end actions rss types esp end key_len 0 queues end / end
        testpmd>start

#. Tester use scapy to send the 100 MAC_IPV6_ESP pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=50)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in differently 16 queues evenly with differently RSS hash value::

        testpmd> stop

#. check the flow can be listed and destory rule on port 0::

        testpmd> flow list 0
        ID      Group   Prio    Attr    Rule
        0       0       0       i--     ETH IPV6 ESP => RSS
        testpmd> flow flush 0

#. Tester use scapy to send the 100 MAC_IPV6_ESP pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=50)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in the same queue.

Test case: MAC_IPV4_AH:
=======================
#. DUT create rule for the RSS type for MAC_IPV4_AH::

        testpmd>flow create 0 ingress pattern eth / ipv4 / ah / end actions rss types esp end key_len 0 queues end / end
        testpmd>start

#. Tester use scapy to send the 100 MAC_IPV4_AH pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=51)/AH(spi=11)/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in differently 16 queues evenly with differently RSS hash value::

        testpmd> stop

#. check the flow can be listed and destory rule on port 0::

        testpmd> flow list 0
        ID      Group   Prio    Attr    Rule
        0       0       0       i--     ETH IPV4 AH => RSS
        testpmd> flow flush 0

#. Tester use scapy to send the 100 MAC_IPV4_AH pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=51)/AH(spi=11)/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in the same queue.

Test case: MAC_IPV6_AH:
=======================
#. DUT create rule for the RSS type for MAC_IPV6_AH::

        testpmd>flow create 0 ingress pattern eth / ipv6 / ah / end actions rss types esp end key_len 0 queues end / end
        testpmd>start

#. Tester use scapy to send the 100 MAC_IPV6_AH pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=51)/AH(spi=11)/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in differently 16 queues evenly with differently RSS hash value::

        testpmd> stop

#. check the flow can be listed and destory rule on port 0::

        testpmd> flow list 0
        ID      Group   Prio    Attr    Rule
        0       0       0       i--     ETH IPV6 AH => RSS
        testpmd> flow flush 0

#. Tester use scapy to send the 100 MAC_IPV6_AH pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=51)/AH(spi=11)/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in the same queue.

Test case: SIMPLE_XOR:
======================
#. create rule for the rss type simple_xor::

        testpmd>flow create 0 ingress pattern end actions rss func simple_xor key_len 0 queues end / end
        testpmd>start
   
SIMPLE_XOR_IPV4:
===========================
#. to send IPV4 pkt with fixed IP and switch IP src and dst address and switch the upd, tcp, sctp, icpm ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.4.1",dst="2.2.2.3")/("X"*480)], iface="enp177s0f1", count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="2.2.2.3",dst="1.1.4.1")/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
Verbose log::

   src=A4:BF:01:68:D2:03 - dst=00:11:22:33:44:55 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x3030602 - RSS queue=0x2 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x2 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

   src=A4:BF:01:68:D2:03 - dst=00:11:22:33:44:55 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x3030602 - RSS queue=0x2 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x2 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
   
Check the RSS value wiht a same value and the packets enter to a queue
 
statistics log::

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

#. Destory rule on port 0 
         testpmd> flow flush 0
SIMPLE_XOR_IPV6:
================
#. to send IPV6 pkt with fixed IP and switch IP src and dst address and switch the upd, tcp, sctp, icpm ports::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)], iface="enp177s0f1", count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and check the rss hash with a fixed value.
   
Verbose log::

    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x86dd - length=134 - nb_segs=1 - RSS hash=0x5c24be5 - RSS queue=0x25 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV6  - l2_len=14 - l3_len=40 - Receive queue=0x25 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x86dd - length=134 - nb_segs=1 - RSS hash=0x5c24be5 - RSS queue=0x25 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV6  - l2_len=14 - l3_len=40 - Receive queue=0x25 ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

statistics log::

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
   
#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: Check different inputset between the VF and PF for the MAC_IPV4_TCP with valid MAC address:
=====================================================================================================
To check MAC_IPV4_TCP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs

        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1
        testpmd>port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
   
4. start scapy
#. create rule for the rss type is ipv4 UDP +l3 src and dst::

    Create ipv4 TCP +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with tcp4 sdfn , 
        ethtool -N enp177s0f0 rx-flow-hash tcp4 sdfn

2. Check the settings, the kernel PF has setting with IP L3 SA+DA and L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash tcp4

        TCP over IPV4 flows use these fields for computing Hash flow key:
        IP SA
        IP DA
        L4 bytes 0 & 1 [TCP/UDP src port]
        L4 bytes 2 & 3 [TCP/UDP dst port]


3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+TCP pkts to the VF with valid AVF MAC::
      
    Send the 100 IP+TCP pkts in VF
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   but to check the Kernel PF with "command ethtool -S enp177s0f0", then should does not receive these 100 packages in rx queue

#. send the 100 IP+TCP pkts to the PF with valid PF MAC::   
    Send the 100 IP+UDP pkts in VF
        sendp([Ether(dst="68:05:ca:a3:1a:78")/IP(src=RandIP(),dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   but the VF should does not receive these 100 packages.
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806


#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: Check different inputset between the VF and PF for the MAC_IPV4_TCP with broadcast MAC address:
==========================================================================================================
To check MAC_IPV4_UDP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1
        testpmd>port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
   
4. start scapy
#. create rule for the rss type is ipv4 UDP +l3 src and dst::

    Create ipv4 TCP +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with tcp4 fn , 
        ethtool -N enp177s0f0 rx-flow-hash tcp4 fn

2. Check the settings, the kernel PF has setting with L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash tcp4

        TCP over IPV4 flows use these fields for computing Hash flow key:
        L4 bytes 0 & 1 [TCP/UDP src port]
        L4 bytes 2 & 3 [TCP/UDP dst port]


3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+TCP pkts to the VF with default MAC::
      
    Send the 100 IP+TCP pkts in VF
        sendp([Ether()/IP()/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   and check the Kernel PF with "command ethtool -S enp177s0f0", should receive these 100 packages in rx queue too

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: Check different inputset between the VF and PF for the MAC_IPV4_UDP with valid MAC address:
=====================================================================================================
To check MAC_IPV4_UDP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs

        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1
        testpmd>port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
   
4. start scapy
#. create rule for the rss type is ipv4 UDP +l3 src and dst::

    Create ipv4 udp +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with udp4 sdfn , 
        ethtool -N enp177s0f0 rx-flow-hash udp4 sdfn

2. Check the settings, the kernel PF has setting with IP L3 SA+DA and L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash udp4

        udp over IPV4 flows use these fields for computing Hash flow key:
        IP SA
        IP DA
        L4 bytes 0 & 1 [udp/UDP src port]
        L4 bytes 2 & 3 [udp/UDP dst port]


3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+udp pkts to the VF with valid AVF MAC::
      
    Send the 100 IP+udp pkts in VF
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   but to check the Kernel PF with "command ethtool -S enp177s0f0", then should does not receive these 100 packages in rx queue

#. send the 100 IP+udp pkts to the PF with valid PF MAC::   
    Send the 100 IP+UDP pkts in VF
        sendp([Ether(dst="68:05:ca:a3:1a:78")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   but the VF should does not receive these 100 packages.
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806


#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: Check different inputset between the VF and PF for the MAC_IPV4_udp with broadcast MAC address:
==========================================================================================================
To check MAC_IPV4_UDP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1
        testpmd>port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
   
4. start scapy
#. create rule for the rss type is ipv4 UDP +l3 src and dst::

    Create ipv4 udp +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with udp4 fn , 
        ethtool -N enp177s0f0 rx-flow-hash udp4 fn

2. Check the settings, the kernel PF has setting with L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash udp4

        udp over IPV4 flows use these fields for computing Hash flow key:
        L4 bytes 0 & 1 [udp/UDP src port]
        L4 bytes 2 & 3 [udp/UDP dst port]


3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+udp pkts to the VF with default MAC::
      
    Send the 100 IP+udp pkts in VF
        sendp([Ether()/IP()/udp(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   and check the Kernel PF with "command ethtool -S enp177s0f0", should receive these 100 packages in rx queue too

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: Check different inputset between the VF and PF for the MAC_IPV6_TCP with valid MAC address:
=====================================================================================================
To check MAC_IPV6_TCP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1
        testpmd>port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
   
4. start scapy
#. create rule for the rss type is ipv6-tcp +l3 src and dst::

    Create ipv6 TCP +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with tcp6 sdfn , 
        ethtool -N enp177s0f0 rx-flow-hash tcp6 sdfn

2. Check the settings, the kernel PF has setting with IP L3 SA+DA and L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash tcp6

        TCP over IPV6 flows use these fields for computing Hash flow key:
        IP SA
        IP DA
        L4 bytes 0 & 1 [TCP/UDP src port]
        L4 bytes 2 & 3 [TCP/UDP dst port]


3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+TCP pkts to the VF with valid AVF MAC::
      
    Send the 100 IP+TCP pkts in VF
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src=RandIP6())/TCP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   but to check the Kernel PF with "command ethtool -S enp177s0f0", then should does not receive these 100 packages in rx queue

#. send the 100 IP+TCP pkts to the PF with valid PF MAC::   
    Send the 100 IP+UDP pkts in VF
        sendp([Ether(dst="68:05:ca:a3:1a:78")/IPv6(src=RandIP6())/TCP(sport=RandShort(),dport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   but the VF should does not receive these 100 packages.
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806

#. Destory rule on port 0 
         testpmd> flow flush 0
   
Test case: Check different inputset between the VF and PF for the MAC_IPV6_TCP with broadcast MAC address:
==========================================================================================================
To check MAC_IPV6_TCP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1
        testpmd>port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
   
4. start scapy
#. create rule for the rss type is ipv6 TCP +l3 src and dst::

    Create ipv4 TCP +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with tcp4 fn , 
        ethtool -N enp177s0f0 rx-flow-hash tcp6 fn

2. Check the settings, the kernel PF has setting with L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash tcp6

        TCP over IPV6 flows use these fields for computing Hash flow key:
        L4 bytes 0 & 1 [TCP/UDP src port]
        L4 bytes 2 & 3 [TCP/UDP dst port]


3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+TCP pkts to the VF with default MAC::
      
    Send the 100 IP+TCP pkts in VF
        sendp([Ether()/IPv6()/TCP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   and check the Kernel PF with "command ethtool -S enp177s0f0", should receive these 100 packages in rx queue too

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: Check different inputset between the VF and PF for the MAC_IPV6_UDP with valid MAC address:
=====================================================================================================
To check MAC_IPV6_UDP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs

        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1
        testpmd>port config 0 rss-hash-key IPV6 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
   
4. start scapy
#. create rule for the rss type is IPV6 UDP +l3 src and dst::

    Create IPV6 udp +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types IPV6-udp end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with udp6 sdfn , 
        ethtool -N enp177s0f0 rx-flow-hash udp6 sdfn

2. Check the settings, the kernel PF has setting with IP L3 SA+DA and L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash udp6

        udp over IPV6 flows use these fields for computing Hash flow key:
        IP SA
        IP DA
        L4 bytes 0 & 1 [udp/UDP src port]
        L4 bytes 2 & 3 [udp/UDP dst port]


3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+udp pkts to the VF with valid AVF MAC::
      
    Send the 100 IP+udp pkts in VF
        sendp([Ether(dst="00:11:22:33:44:55")/IP6(src=RandIP6(),dst=RandIP6())/udp(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   but to check the Kernel PF with "command ethtool -S enp177s0f0", then should does not receive these 100 packages in rx queue

#. send the 100 IP+udp pkts to the PF with valid PF MAC::   
    Send the 100 IP+UDP pkts in VF
        sendp([Ether(dst="68:05:ca:a3:1a:78")/IPv6(src=RandIP6(),dst=RandIP6())/udp(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   but the VF should does not receive these 100 packages.
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806

#. Destory rule on port 0 
         testpmd> flow flush 0
   
Test case: Check different inputset between the VF and PF for the MAC_IPV6_udp with broadcast MAC address:
==========================================================================================================
To check MAC_IPV6_UDP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1
        testpmd>port config 0 rss-hash-key IPV6 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
   
4. start scapy
#. create rule for the rss type is IPV6 UDP +l3 src and dst::

    Create IPV6 udp +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / IPV6 / udp / end actions rss types IPV6-udp end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with udp6 fn , 
        ethtool -N enp177s0f0 rx-flow-hash udp6 fn

2. Check the settings, the kernel PF has setting with L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash udp6

        udp over IPV6 flows use these fields for computing Hash flow key:
        L4 bytes 0 & 1 [udp/UDP src port]
        L4 bytes 2 & 3 [udp/UDP dst port]


3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+udp pkts to the VF with default MAC::
      
    Send the 100 IP+udp pkts in VF
        sendp([Ether()/IP()/udp(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   and check the Kernel PF with "command ethtool -S enp177s0f0", should receive these 100 packages in rx queue too

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: Check different inputset between the VF and PF for the MAC_IPV4_SCTP with valid MAC address:
=======================================================================================================
To check MAC_IPV4_SCTP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs

        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1
   
4. start scapy
#. create rule for the rss type is ipv4 SCTP +l3 src and dst::

    Create ipv4 SCTP +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp4 end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with sctp4sdfn , 
        ethtool -N enp177s0f0 rx-flow-hash sctp4 sd

2. Check the settings, the kernel PF has setting with IP L3 SA+DA and L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash tcp4

        SCTP over IPV4 flows use these fields for computing Hash flow key:
        IP SA
        IP DA

3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+SCTP pkts to the VF with valid AVF MAC::
      
    Send the 100 IP+SCTP pkts in VF
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   but to check the Kernel PF with "command ethtool -S enp177s0f0", then should does not receive these 100 packages in rx queue

#. send the 100 IP+SCTP pkts to the PF with valid PF MAC::   
    Send the 100 IP+UDP pkts in VF
        sendp([Ether(dst="68:05:ca:a3:1a:78")/IP(src=RandIP(),dst=RandIP())/SCTP()/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   but the VF should does not receive these 100 packages.
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806

#. Destory rule on port 0 
         testpmd> flow flush 0
   
Test case: Check different inputset between the VF and PF for the MAC_IPV4_SCTP with broadcast MAC address:
==========================================================================================================
To check MAC_IPV4_UDP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1
   
4. start scapy
#. create rule for the rss type is ipv4 UDP +l3 src and dst::

    Create ipv4 SCTP +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with sctp4fn , 
        ethtool -N enp177s0f0 rx-flow-hash sctp4 sd

2. Check the settings, the kernel PF has setting with L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash tcp4

        SCTP over IPV4 flows use these fields for computing Hash flow key:
        IP SA
        IP DA


3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+SCTP pkts to the VF with default MAC::
      
    Send the 100 IP+SCTP pkts in VF
        sendp([Ether()/IP(src=RandIP(),dst=RandIP())/SCTP()/("X"*480)], iface="enp177s0f1", count=100)

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   and check the Kernel PF with "command ethtool -S enp177s0f0", should receive these 100 packages in rx queue too

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: Check different inputset between the VF and PF for the MAC_IPV6_SCTP with valid MAC address:
=======================================================================================================
To check MAC_IPV6_SCTP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs

        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1         
   
4. start scapy
#. create rule for the rss type is IPV6 SCTP +l3 src and dst::

    Create IPV6 sctp +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types IPV6-sctp end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with sctp6 sd, 
        ethtool -N enp177s0f0 rx-flow-hash sctp6 sd

2. Check the settings, the kernel PF has setting with IP L3 SA+DA and L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash sctp6

        sctp over IPV6 flows use these fields for computing Hash flow key:
        IP SA
        IP DA

3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+sctp pkts to the VF with valid AVF MAC::
      
    Send the 100 IP+sctp pkts in VF
        sendp([Ether(dst="00:11:22:33:44:55")/IP6(src=RandIP6(),dst=RandIP6())/sctp()/("X"*480)], iface="enp177s0f1", count=100)
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   but to check the Kernel PF with "command ethtool -S enp177s0f0", then should does not receive these 100 packages in rx queue

#. send the 100 IP+sctp pkts to the PF with valid PF MAC::   
    Send the 100 IP+SCTP pkts in VF
        sendp([Ether(dst="68:05:ca:a3:1a:78")/IPv6(src=RandIP6(),dst=RandIP6())/sctp()/("X"*480)], iface="enp177s0f1", count=100)
        testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   but the VF should does not receive these 100 packages.
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806

#. Destory rule on port 0 
         testpmd> flow flush 0
   
Test case: Check different inputset between the VF and PF for the MAC_IPV6_sctp with broadcast MAC address:
==========================================================================================================
To check MAC_IPV6_SCTP in PF with a fix IP address and port
IAVF domain settings:   
1. Create A VF from a PF::
        modprobe vfio-pci
        echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
        VF 0000\:b1\:01.0 have been created::
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
        ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd in the PF with below command::
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1
   
4. start scapy
#. create rule for the rss type is IPV6 SCTP +l3 src and dst::

    Create IPV6 sctp +l3 SA+DA and sport+dport in AVF::
        testpmd>flow create 0 ingress pattern eth / IPV6 / sctp / end actions rss types ipv6-sctp end key_len 0 queues end / end
        testpmd>start

PF KERNEL domain settings:
1. To set RSS rule with sctp6 fn , 
        ethtool -N enp177s0f0 rx-flow-hash sctp6 sd

2. Check the settings, the kernel PF has setting with L4 sport+dport 
        ethtool -n enp177s0f0 rx-flow-hash sctp6

        sctp over IPV6 flows use these fields for computing Hash flow key:
        IP SA
        IP DA

3.  To set queme number 10 for rx and tx in kernel PF
        ethtool -L enp177s0f0 rx 10 tx 10

4.  To check the queue number 10 has set finished 

        ethtool -l enp177s0f0
        Channel parameters for enp177s0f0:
        Pre-set maximums:
        RX:             112
        TX:             112
        Other:          1
        Combined:       112
        Current hardware settings:
        RX:             0
        TX:             0
        Other:          1
        Combined:       10

#. send the 100 IP+sctp pkts to the VF with default MAC::
      
    Send the 100 IP+sctp pkts in VF
        sendp([Ether()/IP()/sctp(src=RandIP6(),dst=RandIP6())/("X"*480)], iface="enp177s0f1", count=100)

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with differently RSS random value in VF
   and check the Kernel PF with "command ethtool -S enp177s0f0", should receive these 100 packages in rx queue too

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 10 queues evenly with differently RSS random value in PF with command command ethtool -S enp177s0f0"
   PF Kerne show below info:
            rx_queue_0_packets: 12
            rx_queue_0_bytes: 6408
            rx_queue_1_packets: 9
            rx_queue_1_bytes: 4806
            rx_queue_2_packets: 10
            rx_queue_2_bytes: 5340
            rx_queue_3_packets: 14
            rx_queue_3_bytes: 7476
            rx_queue_4_packets: 9
            rx_queue_4_bytes: 4806
            rx_queue_5_packets: 7
            rx_queue_5_bytes: 3738
            rx_queue_6_packets: 6
            rx_queue_6_bytes: 3204
            rx_queue_7_packets: 15
            rx_queue_7_bytes: 8010
            rx_queue_8_packets: 9
            rx_queue_8_bytes: 4806
            rx_queue_9_packets: 9
            rx_queue_9_bytes: 4806

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case 1: Check different inputset between the VF1 and VF2 for the MAC_IPV4_UDP:
===================================================================================
To check MAC_IPV4_UDP in VF1 with a fix IP address and port
1. Create 2 VFs from a PF::

        echo 2 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
        ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55
        ip link set enp177s0f0 vf 1 mac 00:11:55:66:77:88
   
2. Bind the pci device id of DUT in VFs::
       modprobe vfio-pci
       ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0 0000:b1:01.1

.. note::

   The kernel must be >= 3.6+ and VT-d must be enabled in bios.
   
3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT for VFs start::

    Launch the testpmd to configuration queue of rx and tx number 16 in DUT in VF0
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 --file-prefix=vf0 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1

    Launch the testpmd to configuration queue of rx and tx number 16 in DUT in VF0
        testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.1 --file-prefix=vf1 -- -i --rxq=16 --txq=16  --nb-cores=2
        testpmd>set fwd rxonly
        testpmd>set verbose 1

4. start scapy 
   
#. create rule for the rss type is ipv4 UDP +l3 src and dst::
      
    Create rule for the rss type is ipv4 UDP +l3 src and l4 dst in VF0::
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l3-src-only l4-dst-only end key_len 0 queues end / end
        testpmd>start
    Create rule for the rss type is ipv4 UDP +l3 dst and l4 src in VF1:
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l3-dst-only l4-src-only end key_len 0 queues end / end
        testpmd>start

#. send the 100 IP+UDP pkts::

    Send 100 IP+UDP pkts with IP src and UDP dport in VF0::
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP())/UDP(dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
    testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value in VF0
   
    Send 100 IP+UDP pkts with IP dst and UDP sport in VF1::
        sendp([Ether(dst="00:11:55:66:77:88")/IP(dst=RandIP())/UDP(sport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
    testpmd> stop
#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value in VF1
   
#. send the 100 IP+UDP with broadcast  pkts::   

    Send 100 IP+UDP pkts with IP src and UDP dport in VF0::
        sendp([Ether()/IP(src=RandIP())/UDP(dport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value in VF0
   
    Send 100 IP+UDP pkts with IP dst and UDP sport in VF1::

        sendp([Ether()/IP(dst=RandIP())/UDP(sport=RandShort())/("X"*480)], iface="enp177s0f1", count=100)
    testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value in VF	
   
#. Destory rule on port 0 
         testpmd> flow flush 0   

Test case: Error handle MAC_IPV4_UDP for the invalid pattern:
====================================================================
#. create rule for the rss type for l3 dst only::

    testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

#. Expected fail, 
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

Test case: Error handle MAC_IPV4_TCP for the invalid pattern:
=====================================================================
#. create rule for the rss type is IPV4 l3 src +NVGRE inner IPV4 +frag + ICMP::

    testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end

#. Expected fail with below log, 
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

Test case 2: VF reset on set RSS case MAC_IPV4_L3DST_FRAG:
=========================================================
#. Generate 1 VFs on PF
    modprobe vfio-pci	
    echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
    ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

#. Set a VF as trust
    ip link set enp177s0f0 vf 0 trust on

#. Launch dpdk on the VF, request DCF mode
    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0
    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 --file-prefix=vf -- -i --rxq=16 --txq=16  --nb-cores=2
    set verbose 1
    set fwd rxonly

#. create rule for the rss type for l3 dst only::

    testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
    testpmd> start
    testpmd> show port 0 rss-hash
             RSS functions:
             all ipv4-frag ipv4-tcp ipv4-udp ipv4-sctp ipv4-other ip udp tcp sctp

#. send the 100 IP frag pkts::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(dst=RandIP(), frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)

    testpmd> stop

#. vf reset::
    
    testpmd> port stop 0
             Stopping ports...
             Checking link statuses...
             Done
    testpmd> port reset 0
             Resetting ports...
             Device with port_id=0 already stopped
             iavf_read_msg_from_pf(): command mismatch, expect 44, get 17
             Done
    testpmd> port start
    testpmd> start

#. Expected the port can be stop/reset/start normally without error message.
#. send the 100 IP frag pkts::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(dst=RandIP(), frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
    testpmd> stop


#. check the verify 100 pkts has received in VF0, and the RSS hash value should work, due to the after reset mac  to the rss has set to default enable status.

#. pf trigger vf reset::

    ip link set enp177s0f0 vf 0 mac 00:11:33:44:66:77

#. vf reset::
    
    testpmd> port stop 0
             Stopping ports...
             Checking link statuses...
             Done
    testpmd> port reset 0
             Resetting ports...
             Device with port_id=0 already stopped
             iavf_read_msg_from_pf(): command mismatch, expect 44, get 17
             Done
    testpmd> port start
    testpmd> start
#. to check the port can be stop/reset/start normally without error message.
check the rule status is valid
#. send the 100 IP frag pkts::

     sendp([Ether(dst="000:11:33:44:66:77")/IP(dst=RandIP(), frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)
    testpmd> stop
#. check the verify 100 pkts has received in VF0, and the RSS hash value should work, due to the after reset mac  to the rss has set to default enable status.

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case : Check PF reset vf on RSS MAC_IPV4_UDP:
===================================================
To check MAC_IPV4_UDP in VF1 with a fix IP address and port
1. Create 2 VFs from a PF::

    modprobe vfio-pci
    echo 2 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
    ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55
    ip link set enp177s0f0 vf 1 mac 00:11:55:66:77:88

    pf0 is mac: 68:05:ca:a3:1a:78
    pf1 is mac: 68:05:ca:a3:1a:79

   ip link set enp177s0f1 vf 0 mac 00:11:22:33:44:55
   ip link set enp177s0f1 vf 1 mac 00:11:33:44:55:66

2. Bind the pci device id of DUT in VFs::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0 0000:b1:01.1
.. note::

   The kernel must be >= 3.6+ and VT-d must be enabled in bios.

3. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    Launch the testpmd to configuration queue of rx and tx number 16 in DUT in VF0
    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 -w b1:01.1 --file-prefix=vf -- -i --rxq=16 --txq=16  --nb-cores=2
    testpmd>set fwd rxonly
    testpmd>set verbose 1

4. start scapy

#. create rule for the rss type is ipv4 UDP +l3 src and dst::

   Create rule for the rss type is ipv4 UDP +l3 src and l4 dst in VF0::
      testpmd>flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end
      testpmd>start
      Create rule for the rss type is ipv4 UDP +l3 dst and l4 src in VF1:
      testpmd>flow create 1 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end
      testpmd>start

#. send the 100 IP+UDP pkts::

      Send 100 IP+UDP pkts with IP src and UDP dport in VF0::
      sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20")/UDP(dport=20)/("X"*480)], iface="enp177s0f1", count=100)
      Send 100 IP+UDP pkts with IP dst and UDP sport in VF1::
      sendp([Ether(dst="00:11:55:66:77:88")/IP(dst="192.168.0.21")/UDP(sport=22)/("X"*480)], iface="enp177s0f1", count=100)
      testpmd> stop

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with
   differently RSS random value in VF

#. Reset PF by ip link set enp177s0f0 vf 0 mac 00:11:77:88:99:66
      
     ip link set enp177s0f0 vf 0 mac 00:11:77:88:99:66

#. send the 100 IP+UDP pkts vf0::
      Send 100 IP+UDP pkts with IP src and UDP dport in VF0::
      sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20")/UDP(dport=20)/("X"*480)], iface="enp177s0f1", count=100)
 
      sendp([Ether(dst="00:11:77:88:99:66")/IP(src="192.168.0.20")/UDP(dport=20)/("X"*480)], iface="enp177s0f1", count=100)

#. Expect: VF0 can't receive the rss packet on vf 0, because the port 0 does not reset, the default rule can not enable.

#. send the 100 IP+UDP pkts vf1:: 
      Send 100 IP+UDP pkts with IP dst and UDP sport in VF1::
      sendp([Ether(dst="00:11:55:66:77:88")/IP(dst="192.168.0.21")/UDP(sport=22)/("X"*480)], iface="enp177s0f1", count=100)
      testpmd> stop   

   Expect: VF1 should  receive the rss packet, because the vf1 does not triger mac reset.

#. Destory rule on port 0 
         testpmd> flow flush 0   
Test case: Use OS default package for the MAC_IPV4_GTPU_FRAG and IPV4 L3 src only :
===================================================================================
#. Load OS package
#. Create rule for the rss type GTPU and hash l3 src keywords::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end

#. failed to create, the error message should be correct, maybe not support this pattern.
        iavf_execute_vf_cmd(): No response or return failure (-5) for cmd 45
        iavf_add_del_rss_cfg(): Failed to execute command of OP_ADD_RSS_CFG
        iavf_hash_create(): fail to add RSS configure
        iavf_flow_create(): Failed to create flow
        port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

Test case: Use OS default package for the MAC_IPV4_L2TPv3:
==========================================================
#. Load OS package

#. Create rule for the rss type MAC_IPV4_L2TPv3::

        testpmd>flow create 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end

#. Tester use scapy to send the 100 MAC_IPV4_L2TPv3 pkts with different session ID::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3", proto=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in the same queue.

Test case: Use OS default package for the MAC_IPV6_ESP:
==========================================================
#. Load OS package

#. Create rule for the rss type MAC_IPV6_ESP::

        testpmd>flow create 0 ingress pattern eth / ipv6 / esp / end actions rss types l2tpv3 end key_len 0 queues end / end

#. Tester use scapy to send the 100 MAC_IPV6_ESP pkts with different spi::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=50)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0") 
        ...

#. Verify 100 pkts has been sent, and check the 100 pkts has been recieved by DUT in the same queue.

Test case: Check rssh hash in mutil VFS
=======================================
1. Generate 2 VFs on PF0 and set mac address for each VF::

    modprobe vfio-pci	
    echo 2 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
    ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55
    ip link set enp177s0f0 vf 1 mac 00:11:55:66:77:88


2. Launch dpdk  2VFs on port 0::

   ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0 0000:b1:01.1
   
   ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 --file-prefix=vf -- -i --rxq=16 --txq=16  --nb-cores=2
   
   ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.1 --file-prefix=vf2 -- -i --rxq=16 --txq=16  --nb-cores=2    
   
   create rule on vf0 on port 0:: 
   testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end
   
   create rule on vf1 on port 0:: 
   testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end


3. to send 100 packages to the VF1 with VF1 mac
    sendp([Ether(dst="00:11:55:66:77:88")/IP(dst=RandIP(), frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)

    sendp([Ether(dst="00:11:55:66:77:88")/IP(src=RandIP(), frag=5)/SCTP(sport=RandShort())/("X" * 80)], iface="enp177s0f1", count=100)

   Expect: RSS should work in VF1 and VF1 should received these 100 RSS hash packages , because the rss hash has enable default on VF1
   But VF0 should not recevied rss pakcages.

#. Destory rule on port 0 
         testpmd> flow flush 0

Test case: MAC_ETH:
===================
#. create rule for the rss type is MAC ::
        testpmd>flow create 0 ingress pattern eth / ipv4  / end actions rss types l2-src-only end key_len 0 queues end / end
        testpmd>start
        

#. send the 100 IP pkts::
        sendp(Ether(src="00:11:22:33:44:55")/IP(),iface="enp177s0f1", count=100)
        sendp(Ether(src=RandMAC())/IP(),iface="enp177s0f1", count=100)
       
#. create rule for the rss type is MAC ::
        testpmd> flow create 0 ingress pattern eth / ipv4  / end actions rss types l2-dst-only end key_len 0 queues end / end
        testpmd> start

#. send the 100 IP pkts::
        sendp(Ether(dst="00:11:22:33:44:55")/IP(),iface="enp177s0f1", count=100)

        sendp(Ether(dst=RandMAC())/IP(),iface="enp177s0f1", count=100)

#. verify 100 pkts has sent, and to check the 100 pkts has send to differently totaly 16 queues evenly with 
   differently RSS random value
   
#. Destory rule on port 0 
         testpmd> flow flush 0

==========================================
CVL Support RSS for PFCP in advanced iavf
==========================================

Description
===========

For PFCP protocal, the destination port value of the outer UDP header is equal to 8805(0x2265)
PFCP Node headers shall be identified when the Version field is equal to 001 and the S field is equal 0.
PFCP Session headers shall be identified when the Version field is equal to 001 and the S field is equal 1.

CVL supports PFCP protocols in advanced iavf, the supported pattern as below::
    
    +-------------------------+------------------------+
    |    Packet type          |     RSS input set      |
    +-------------------------+------------------------+
    |  MAC_IPV4_PFCP_NODE     |           -            |
    +-------------------------+------------------------+
    |  MAC_IPV4_PFCP_SESSION  |          SEID          |
    +-------------------------+------------------------+
    |  MAC_IPV6_PFCP_NODE     |           -            |
    +-------------------------+------------------------+
    |  MAC_IPV6_PFCP_SESSION  |          SEID          |
    +-------------------------+------------------------+

Prerequisites
=============

Create a VF interface from kernel PF interfaces, and then attach them to VM. Suppose PF is 0000:18:00.0 . 
Generate a VF using commands below and make them in pci-stub mods.

NIC: 4x25G or 2x100G, several TC need breakout mode, then 2x100G is required
PF: The 1st PF's PCI address 0000:18:00.0 , kernel interface name enp24s0f0 . The 2nd PF's PCI address 0000:18:00.1 , kernel interface name enp24s0f1
VF: The VFs generated by 0000:18:00.0 , are 0000:18:02.x , The VFs generated by 0000:18:00.1 , are 0000:18:0a.x

Copy correct ``ice.pkg`` into ``/usr/lib/firmware/intel/ice/ddp/``, 
For the test cases, comms package is expected.

Prepare test toplogoy, in the test case, it requires

- 1 Intel E810 interface
- 1 network interface enp134s0f0 for sending test packet, which could be connect to the E810 interface
- Directly connect the 2 interfaces
- Latest driver and comms pkgs of version

Compile DPDK and testpmd::

    make install -j T=x86_64-native-linuxapp-gcc

1. Create 1 VF from a PF, and set VF mac address::

    echo 1 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ip link set enp24s0f0 vf 0 mac 00:11:22:33:44:55
          
2. Bind VF to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:02.0 

3. Bring up PF and tester port::

    ifconfig enp24s0f0 up
    ifconfig enp134s0f0 up

4. Launch the testpmd::

    ./x86_64-native-linux-gcc/app/testpmd -l 6-9 -n 4 -w 18:02.0 -- -i --rxq=16 --txq=16 --portmask=0x1 --nb-cores=2
    testpmd>set verbose 1
    testpmd>set fwd rxonly
    testpmd>start

5. on tester side, add pfcp.py to "scapy/layers", and copy it to "/root".
   add "pfcp" to "load_layers" in "scapy/config.py", then start scapy::
 
    >>> import sys
    >>> sys.path.append('/root)
    >>> from pfcp import PFCP
    >>>from scapy.contrib.pfcp import *  

Test Case 01: RSS support MAC_IPV4_PFCP_SESSION
===============================================

1. DUT create rule for RSS type of MAC_IPV4_PFCP_SESSION::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end 

3. Tester use scapy to send the 100 MAC_IPV4_PFCP_SESSION pkts with different SEID::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=1, SEID=12)/Raw('x' * 80)],iface="enp177s0f1,count=100")
    
4. Verify 100 pkts has been sent, 
and check the 100 pkts has been recieved by DUT in differently 16 queues evenly with differently RSS hash value::

5. send MAC_IPV4_PFCP_NODE and MAC_IPV6_PFCP_SESSION pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=0)/Raw('x' * 80)],iface="enp177s0f1", count=100)
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=1, SEID=12)/Raw('x' * 80)],iface="enp177s0f1",count=100)

   check the packet is distributed to queue 0.

6. DUT verify rule can be listed and destroyed::

    testpmd> flow list 0
    
7. destroy the rule::

    testpmd> flow destroy 0 rule 0

8. Verify 100 pkts has been sent, 
and check the 100 pkts has been recieved by DUT in queue 0::


Test Case 02: RSS support MAC_IPV6_PFCP_SESSION
===============================================

1. DUT create rule for the RSS type for MAC_IPV6_PFCP_SESSION::

    flow create 0 ingress pattern eth / ipv6 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end  

2. Tester use scapy to send the 100 MAC_IPV6_PFCP_SESSION pkts with different SEID::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=1, SEID=12)/Raw('x' * 80)],iface="enp177s0f1",count=100)

3. Verify 100 pkts has been sent, 
and check the 100 pkts has been recieved by DUT in differently 16 queues evenly with differently RSS hash value::

4. send MAC_IPV6_PFCP_NODE and MAC_IPV4_PFCP_SESSION pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=0)/Raw('x' * 80)],iface="enp177s0f1, count=100")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=1, SEID=12)/Raw('x' * 80)],iface="enp177s0f1, count=100")

   check the packet is distributed to different queue.

6. DUT verify rule can be listed and destroyed::

    testpmd> flow list 0
    
7. destroy the rule::

    testpmd> flow destroy 0 rule 0

8. Verify 100 pkts has been sent, 
and check the 100 pkts has been recieved by DUT in queue 0::

Test Case 03: RSS Negative test with OS default
====================================================

1. load OS package, and rmmod ice driver. insmod ice driver

2. run the pre-steps

3. create rule for the RSS type for MAC_IPV4_PFCP_SESSION/MAC_IPV6_PFCP_SESSION::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end  
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end

both of the rules can't be created successfully.
#. failed to create, the error message should be correct, maybe not support this pattern.
   iavf_execute_vf_cmd(): No response or return failure (-5) for cmd 45
   iavf_add_del_rss_cfg(): Failed to execute command of OP_ADD_RSS_CFG
   iavf_hash_create(): fail to add RSS configure
   iavf_flow_create(): Failed to create flow
   port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument













  
   
