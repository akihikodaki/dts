.. Copyright (c) <2017>, Intel Corporation
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

====================================================
Niantic Media Access Control Security (MACsec) Tests
====================================================

Description
===========

This document provides test plan for testing the MACsec function of Niantic:

IEEE 802.1AE:  https://en.wikipedia.org/wiki/IEEE_802.1AE
Media Access Control Security (MACsec) is a Layer 2 security technology
that provides point-to-point security on Ethernet links between nodes.
MACsec, defined in the IEEE 802.1AE-2006 standard, is based on symmetric
cryptographic keys. MACsec Key Agreement (MKA) protocol, defined as part
of the IEEE 802.1x-2010 standard, operates at Layer 2 to generate and
distribute the cryptographic keys used by the MACsec functionality installed
in the hardware.
As a hop-to-hop Layer 2 security feature, MACsec can be combined with
Layer 3 security technologies such as IPsec for end-to-end data security.

MACsec was removed in Fortville since Data Center customers don’t require it.
MACsec can be used for LAN / VLAN, Campus, Cloud and NFV environments
(Guest and Overlay) to protect and encrypt data on the wire.
One benefit of a SW approach to encryption in the cloud is that the payload
is encrypted by the tenant, not by the tunnel provider, thus the tenant has
full control over the keys.

Admins can configure SC/SA/keys manually or use 802.1x with MACsec extensions.
The 802.1X is used for key distribution via the MACsec Key Agreement (MKA)
extension.

The driver interface MUST support basic primitives like
creation/deletion/enable/disable of SC/SA, Next_PN etc
(please do see the macsec_ops in Linux source).

The 82599 only supports GCM-AES-128.

Prerequisites
-------------

1. Hardware:

   * 1x Niantic NIC (2x 10G)
   * 2x IXIA ports (10G)

2. Software:

   * dpdk: http://dpdk.org/git/dpdk
   * scapy: http://www.secdev.org/projects/scapy/

3. Added command::

      testpmd>set macsec offload (port_id) on encrypt (on|off) replay-protect (on|off)
      " Enable MACsec offload. "
      testpmd>set macsec offload (port_id) off
      " Disable MACsec offload. "
      testpmd>set macsec sc (tx|rx) (port_id) (mac) (pi)
      " Configure MACsec secure connection (SC). "
      testpmd>set macsec sa (tx|rx) (port_id) (idx) (an) (pn) (key)
      " Configure MACsec secure association (SA). "


Test Case 1: MACsec packets send and receive
============================================

1. Connect the two ixgbe ports with a cable,
   and bind the two ports to dpdk driver::

      ./tools/dpdk-devbind.py -b igb_uio 07:00.0 07:00.1

2. Config the rx port

   1. Start the testpmd of rx port::

         ./testpmd -c 0xc --socket-mem 1024,1024 --file-prefix=rx -w 0000:07:00.1 \
         -- --port-topology=chained -i --crc-strip

   2. Set MACsec offload on::

         testpmd>set macsec offload 0 on encrypt on replay-protect on

   3. Set MACsec parameters as rx_port::

         testpmd>set macsec sc rx 0 00:00:00:00:00:01 0
         testpmd>set macsec sa rx 0 0 0 0 00112200000000000000000000000000

   4. Set MACsec parameters as tx_port::

         testpmd>set macsec sc tx 0 00:00:00:00:00:02 0
         testpmd>set macsec sa tx 0 0 0 0 00112200000000000000000000000000

   5. Set rxonly::

         testpmd>set fwd rxonly

   6. Start::

         testpmd>set promisc all on
         testpmd>start

3. Config the tx port

   1. Start the testpmd of tx port::

         ./testpmd -c 0x30 --socket-mem 1024,1024 --file-prefix=tx -w 0000:07:00.0 \
         -- --port-topology=chained -i --crc-strip --tx-offloads=0x8fff

   2. Set MACsec offload on::

         testpmd>set macsec offload 0 on encrypt on replay-protect on

   3. Set MACsec parameters as tx_port::

         testpmd>set macsec sc tx 0 00:00:00:00:00:01 0
         testpmd>set macsec sa tx 0 0 0 0 00112200000000000000000000000000

   4. Set MACsec parameters as rx_port::

         testpmd>set macsec sc rx 0 00:00:00:00:00:02 0
         testpmd>set macsec sa rx 0 0 0 0 00112200000000000000000000000000

   5. Set txonly::

         testpmd>set fwd txonly

   6. Start::

         testpmd>start

4. Check the result::

      testpmd>stop
      testpmd>show port xstats 0

   stop the packet transmitting on tx_port first, then stop the packet receiving
   on rx_port.

   check the rx data and tx data::

      tx_good_packets == rx_good_packets
      out_pkts_encrypted == in_pkts_ok == tx_good_packets == rx_good_packets
      out_octets_encrypted == in_octets_decrypted
      out_octets_protected == in_octets_validated

   if you want to check the content of the packet, use the command::

         testpmd>set verbose 1

   the received packets are Decrypted.

   check the ol_flags::

      PKT_RX_IP_CKSUM_GOOD

   check the content of the packet::

      type=0x0800, the ptype of L2,L3,L4: L2_ETHER L3_IPV4 L4_UDP


Test Case 2: MACsec send and receive with different parameters
==============================================================

1. Set "idx" to 1 on both rx and tx sides.
   check the MACsec packets can be received correctly.

   set "idx" to 2 on both rx and tx sides.
   it can't be set successfully.

2. Set "an" to 1/2/3 on both rx and tx sides.
   check the MACsec packets can be received correctly.

   set "an " to 4 on both rx and tx sides.
   it can't be set successfully.

3. Set "pn" to 0xffffffec on both rx and tx sides.
   rx port can receive four packets.

   set "pn" to 0xffffffed on both rx and tx sides.
   rx port can receive three packets.

   set "pn" to 0xffffffee/0xffffffef on both rx and tx sides.
   rx port can receive three packets too. But the expected number
   of packets is 2/1. While the explanation that DPDK developers
   gave is that it's hardware's behavior.

   Once the PN reaches a value of 0xFFFFFFF0, hardware clears
   the Enable Tx LinkSec field in the LSECTXCTRL register to 00b
   so when pn get to 0xfffffff0, the number of packets received can't
   be expected.

   set "pn" to 0x100000000 on both rx and tx sides.
   it can't be set successfully.

4. Set "key" to 00000000000000000000000000000000 and
   ffffffffffffffffffffffffffffffff on both rx and tx sides.
   check the MACsec packets can be received correctly.

5. Set "pi" to 1/0xffff on both rx and tx sides.
   check the MACsec packets can not be received.

   set "pi" to 0x10000 on both rx and tx sides.
   it can't be set successfully.


Test Case 3: MACsec packets send and normal receive
===================================================

1. Disable MACsec offload on rx port::

      testpmd>set macsec offload 0 off

2. Start the the packets transfer

3. Check the result::

      testpmd>stop
      testpmd>show port xstats 0

   stop the testpmd on tx_port first, then stop the testpmd on rx_port.
   the received packets are encrypted.

   check the content of the packet::

      type=0x88e5 sw ptype: L2_ETHER  - l2_len=14 - Receive queue=0x0

   you can't find L3 and L4 information in the packet
   in_octets_decrypted and in_octets_validated doesn't increase on last data
   transfer.


Test Case 4: normal packet send and MACsec receive
==================================================

1. Enable MACsec offload on rx port::

      testpmd>set macsec offload 0 on encrypt on replay-protect on

2. Disable MACsec offload on tx port::

      testpmd>set macsec offload 0 off

3. Start the the packets transfer::

      testpmd>start

4. Check the result::

      testpmd>stop
      testpmd>show port xstats 0

   stop the testpmd on tx_port first, then stop the testpmd on rx_port.
   the received packets are not encrypted.

   check the content of the packet::

      type=0x0800, the ptype of L2,L3,L4: L2_ETHER L3_IPV4 L4_UDP

   in_octets_decrypted and out_pkts_encrypted doesn't increase on last data
   transfer.


Test Case 5: MACsec send and receive with wrong parameters
==========================================================

1. Don't add "--tx-offloads=0x8fff" in the tx_port command line.
   the MACsec offload can't work. The tx packets are normal packets.

2. Set different pn on rx and tx port, then start the data transfer.

   1. Set the parameters as test case 1, start and stop the data transfer.
      check the result, rx port can receive and decrypt the packets normally.

   2. Reset the pn of tx port to 0::

        testpmd>set macsec sa tx 0 0 0 0 00112200000000000000000000000000

      rx port can receive the packets until the pn equals the pn of tx port::

        out_pkts_encrypted = in_pkts_late + in_pkts_ok

3. Set different keys on rx and tx port, then start the data transfer::

     the RX-packets=0,
     in_octets_decrypted == out_octets_encrypted,
     in_pkts_notvalid == out_pkts_encrypted,
     in_pkts_ok=0,
     rx_good_packets=0

4. Set different pi on rx and tx port(reset on rx_port), then start the data
   transfer::

     in_octets_decrypted == out_octets_encrypted,
     in_pkts_ok = 0,
     in_pkts_nosci == out_pkts_encrypted

5. Set different an on rx and tx port, then start the data transfer::

     rx_good_packets=0,
     in_octets_decrypted == out_octets_encrypted,
     in_pkts_notusingsa == out_pkts_encrypted,
     in_pkts_ok=0,

6. Set different index on rx and tx port, then start the data transfer::

     in_octets_decrypted == out_octets_encrypted,
     in_pkts_ok == out_pkts_encrypted


Test Case 6: performance test of MACsec offload packets
==========================================================

1. Tx linerate

   port0 connected to IXIA port5, port1 connected to IXIA port6, set port0
   MACsec offload on, set fwd mac::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xc -- -i \
     --port-topology=chained --crc-strip --tx-offloads=0x8fff

   on IXIA side, start IXIA port6 transmit, start the IXIA capture.
   view the IXIA port5 captured packet, the protocol is MACsec, the EtherType
   is 0x88E5, and the packet length is 96bytes, while the normal packet length
   is 32bytes.

   The valid frames received rate is 10.78Mpps, and the %linerate is 100%.

2. Rx linerate

   there are three ports 05:00.0 07:00.0 07:00.1. Connect 07:00.0 to 07:00.1
   with cable, connect 05:00.0 to IXIA. Bind the three ports to dpdk driver.
   start two testpmd::

         ./testpmd -c 0x3 --socket-mem 1024,1024 --file-prefix=rx -w 0000:07:00.1 \
         -- --port-topology=chained -i --crc-strip --tx-offloads=0x8fff

         testpmd>set macsec offload 0 on encrypt on replay-protect on
         testpmd>set macsec sc rx 0 00:00:00:00:00:01 0
         testpmd>set macsec sa rx 0 0 0 0 00112200000000000000000000000000
         testpmd>set macsec sc tx 0 00:00:00:00:00:02 0
         testpmd>set macsec sa tx 0 0 0 0 00112200000000000000000000000000
         testpmd>set fwd rxonly

         ./testpmd -c 0xc --socket-mem 1024,1024 --file-prefix=tx -b 0000:07:00.1 \
         -- --port-topology=chained -i --crc-strip --tx-offloads=0x8fff

         testpmd>set macsec offload 1 on encrypt on replay-protect on
         testpmd>set macsec sc rx 1 00:00:00:00:00:02 0
         testpmd>set macsec sa rx 1 0 0 0 00112200000000000000000000000000
         testpmd>set macsec sc tx 1 00:00:00:00:00:01 0
         testpmd>set macsec sa tx 1 0 0 0 00112200000000000000000000000000
         testpmd>set fwd mac

   start on both two testpmd.
   start data transmit from IXIA port, the frame size is 64bytes,
   the Ethertype is 0x0800. The rate is 14.88Mpps.

   check the linerate on rxonly port::

         testpmd>show port stats 0

   It shows "Rx-pps:     10775697", so the rx %linerate is 100%.
   check the MACsec packets number on tx side::

         testpmd>show port xstats 1

   on rx side::

         testpmd>show port xstats 0

   check the rx data and tx data::

     in_pkts_ok == out_pkts_encrypted
