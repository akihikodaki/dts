.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2017 Intel Corporation

====================================================
82599 Media Access Control Security (MACsec) Tests
====================================================

Description
===========

This document provides test plan for testing the MACsec function of 82599:

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

MACsec was removed in Intel® Ethernet 700 Series since Data Center customers
don’t require it. MACsec can be used for LAN / VLAN, Campus, Cloud and NFV
environments (Guest and Overlay) to protect and encrypt data on the wire.
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

   * 1x 82599 NIC (2x 10G)
     ::

       port0:
         pci address: 07:00.0
         mac address: 00:00:00:00:00:01
       port1:
         pci address: 07:00.1
         mac address: 00:00:00:00:00:02

   * 2x IXIA ports (10G)

2. Software:

   * dpdk: http://dpdk.org/git/dpdk
   * scapy: http://www.secdev.org/projects/scapy/

3. Added command::

      testpmd> set macsec offload (port_id) on encrypt (on|off) replay-protect (on|off)
      " Enable MACsec offload. "
      testpmd> set macsec offload (port_id) off
      " Disable MACsec offload. "
      testpmd> set macsec sc (tx|rx) (port_id) (mac) (pi)
      " Configure MACsec secure connection (SC). "
      testpmd> set macsec sa (tx|rx) (port_id) (idx) (an) (pn) (key)
      " Configure MACsec secure association (SA). "


Test Case 1: MACsec packets send and receive
============================================

1. Connect the two ixgbe ports with a cable,
   and bind the two ports to dpdk driver::

      ./tools/dpdk-devbind.py -b igb_uio 07:00.0 07:00.1

2. Config the rx port

  1. Start the testpmd of rx port::

      ./<build_target>/app/dpdk-testpmd -c 0xf --socket-mem 1024,0 --file-prefix=rx -a 0000:07:00.1 \
      -- -i --port-topology=chained

  2. Set MACsec offload on::

      testpmd> set macsec offload 0 on encrypt on replay-protect on

     Show port port tx configuration::

      testpmd> show port 0 tx_offload configuration
      Tx Offloading Configuration of port 0 :
        Port : MACSEC_INSERT
        Queue[ 0] :

  3. Set MACsec parameters as rx_port::

      testpmd> set macsec sc rx 0 00:00:00:00:00:01 0
      testpmd> set macsec sa rx 0 0 0 0 00112200000000000000000000000000

  4. Set MACsec parameters as tx_port::

      testpmd> set macsec sc tx 0 00:00:00:00:00:02 0
      testpmd> set macsec sa tx 0 0 0 0 00112200000000000000000000000000

  5. Set rxonly::

      testpmd> set fwd rxonly

  6. Start::

      testpmd> set promisc all on
      testpmd> start

3. Config the tx port

  1. Start the testpmd of tx port::

      ./<build_target>/app/dpdk-testpmd -c 0xf0 --socket-mem 1024,0 --file-prefix=tx -a 0000:07:00.0 \
      -- -i --port-topology=chained

  2. Set MACsec offload on::

      testpmd> set macsec offload 0 on encrypt on replay-protect on

     Show port port tx configuration::

      testpmd> show port 0 tx_offload configuration
      Tx Offloading Configuration of port 0 :
        Port : MACSEC_INSERT
        Queue[ 0] : MACSEC_INSERT

  3. Set MACsec parameters as tx_port::

      testpmd> set macsec sc tx 0 00:00:00:00:00:01 0
      testpmd> set macsec sa tx 0 0 0 0 00112200000000000000000000000000

  4. Set MACsec parameters as rx_port::

      testpmd> set macsec sc rx 0 00:00:00:00:00:02 0
      testpmd> set macsec sa rx 0 0 0 0 00112200000000000000000000000000

  5. Set txonly::

      testpmd> set fwd txonly

  6. Start::

      testpmd> start

4. Check the result::

      testpmd> stop
      testpmd> show port xstats 0

   Stop the packet transmitting on tx_port first, then stop the packet receiving
   on rx_port.

   Check the rx data and tx data::

      out_pkts_protected == 0
      out_pkts_encrypted == in_pkts_ok == tx_good_packets == rx_good_packets !=0
      out_octets_encrypted == in_octets_decrypted != 0
      out_octets_protected == in_octets_validated != 0

   If you want to check the content of the packet, use the command::

      testpmd> set verbose 1

   The received packets are Decrypted.

   Check the ol_flags::

      PKT_RX_IP_CKSUM_GOOD

   Check the content of the packet::

      hw ptype: L2_ETHER L3_IPV4 L4_UDP  - sw ptype: L2_ETHER L3_IPV4 L4_UDP


Test Case 2: MACsec encrypt off and replay-protect off
======================================================

1. Start testpmd as test case 1, then set on tx port::

      testpmd> set macsec offload 0 on encrypt off replay-protect on

   Other settings are the same as test case 1.

2. Start packet transfer, check the rx data and tx data::

      out_pkts_encrypted == 0
      out_pkts_protected == in_pkts_ok == tx_good_packets == rx_good_packets != 0
      in_octets_decrypted == out_octets_encrypted == 0
      out_octets_protected == in_octets_validated != 0

3. Clear the port xstats, then set on tx port::

      testpmd> set macsec offload 0 on encrypt on replay-protect off

4. Start packet transfer, check the rx data and tx data.
   Get the same result as test case 1.


Test Case 3: MACsec send and receive with different parameters
==============================================================

1. Set "idx" to 1 on both rx and tx sides.
   Check the MACsec packets can be received correctly.

   Set "idx" to 2 on both rx and tx sides.
   It can't be set successfully.

2. Set "an" to 1/2/3 on both rx and tx sides.
   Check the MACsec packets can be received correctly.

   Set "an " to 4 on both rx and tx sides.
   It can't be set successfully.

3. Set "pn" to 0xffffffec on both rx and tx sides.
   Rx port can receive four packets.But the expected number
   of packets is 3/4/5 While the explanation that DPDK developers
   gave is that it's hardware's behavior.

   Set "pn" to 0xffffffed on both rx and tx sides.
   Rx port can receive three packets.But the expected number
   of packets is 3/4. While the explanation that DPDK developers
   gave is that it's hardware's behavior.

   Set "pn" to 0xffffffee/0xffffffef on both rx and tx sides.
   Rx port can receive three packets too. But the expected number
   of packets is 2/1. While the explanation that DPDK developers
   gave is that it's hardware's behavior.

   Once the "pn" reaches a value of 0xfffffff0, hardware clears
   the Enable Tx LinkSec field in the LSECTXCTRL register to 00b.
   So when "pn" get to 0xfffffff0, the number of packets received can't
   be expected.

   Set "pn" to 0x100000000 on both rx and tx sides.
   It can't be set successfully.

4. Set "key" to 00000000000000000000000000000000 and
   ffffffffffffffffffffffffffffffff on both rx and tx sides.
   Check the MACsec packets can be received correctly.

5. Set "pi" to 1/0xffff on both rx and tx sides.
   Check the MACsec packets can not be received.

   Set "pi" to 0x10000 on both rx and tx sides.
   It can't be set successfully.


Test Case 4: MACsec packets send and normal receive
===================================================

1. Disable MACsec offload on rx port::

      testpmd> set macsec offload 0 off

   Show port port tx configuration::

      testpmd> show port 0 tx_offload configuration
      Tx Offloading Configuration of port 0 :
        Port :
        Queue[ 0] :

2. Start the the packets transfer

3. Check the result::

      testpmd> stop
      testpmd> show port xstats 0

   Stop the testpmd on tx_port first, then stop the testpmd on rx_port.
   The received packets are encrypted.

   Check the content of the packet::

      hw ptype: L2_ETHER  - sw ptype: L2_ETHER

   You can't find L3 and L4 information in the packet
   in_octets_decrypted and in_octets_validated doesn't increase on data
   transfer.


Test Case 5: normal packet send and MACsec receive
==================================================

1. Enable MACsec offload on rx port::

      testpmd> set macsec offload 0 on encrypt on replay-protect on

2. Disable MACsec offload on tx port::

      testpmd> set macsec offload 0 off
      testpmd> show port 0 tx_offload configuration
      Tx Offloading Configuration of port 0 :
        Port :
        Queue[ 0] : MACSEC_INSERT

3. Start the the packets transfer::

      testpmd> start

4. Check the result::

      testpmd> stop
      testpmd> show port xstats 0

   Stop the testpmd on tx_port first, then stop the testpmd on rx_port.
   The received packets are not encrypted.

   Check the content of the packet::

      hw ptype: L2_ETHER L3_IPV4 L4_UDP  - sw ptype: L2_ETHER L3_IPV4 L4_UDP

   in_octets_decrypted and out_pkts_encrypted doesn't increase on data
   transfer.


Test Case 6: MACsec send and receive with wrong parameters
==========================================================

1. Set different pn on rx and tx port, then start the data transfer.

  1. Set the parameters as test case 1, start and stop the data transfer.
     Check the result, rx port can receive and decrypt the packets normally.

  2. Reset the pn of tx port to 0::

      testpmd> set macsec sa tx 0 0 0 0 00112200000000000000000000000000

     Rx port can receive the packets until the pn equals the pn of tx port::

      out_pkts_encrypted = in_pkts_late + in_pkts_ok

2. Set different keys on rx and tx port, then start the data transfer::

      the RX-packets=0,
      in_octets_decrypted == out_octets_encrypted,
      in_pkts_notvalid == out_pkts_encrypted,
      in_pkts_ok=0,
      rx_good_packets=0

3. Set different pi on rx and tx port, then start the data transfer::

      in_octets_decrypted == out_octets_encrypted,
      in_pkts_ok = 0,
      in_pkts_nosci == out_pkts_encrypted

   note: pi only support changed on rx side, if change pi on tx side,
         it will be omitted.

4. Set different an on rx and tx port, then start the data transfer::

      rx_good_packets=0,
      in_octets_decrypted == out_octets_encrypted,
      in_pkts_notusingsa == out_pkts_encrypted,
      in_pkts_ok=0,

5. Set different index on rx and tx port, then start the data transfer::

      in_octets_decrypted == out_octets_encrypted,
      in_pkts_ok == out_pkts_encrypted


Test Case 7: performance test of MACsec offload packets
=======================================================

1. Tx linerate

   Port0 connected to IXIA port5, port1 connected to IXIA port6, set port0
   MACsec offload on, set fwd mac::

      ./<build_target>/app/dpdk-testpmd -c 0xf --socket-mem 1024,0 -- -i \
      --port-topology=chained
      testpmd> set macsec offload 0 on encrypt on replay-protect on
      testpmd> set fwd mac
      testpmd> start

   On IXIA side, start IXIA port6 transmit, start the IXIA capture.
   View the IXIA port5 captured packet, the protocol is MACsec, the EtherType
   is 0x88E5, and the packet length is 96bytes, while the normal packet length
   is 32bytes.

   The valid frames received rate is 10.78Mpps, and the %linerate is 100%.

2. Rx linerate

   There are three ports 05:00.0 07:00.0 07:00.1. Connect 07:00.0 to 07:00.1
   with cable, connect 05:00.0 to IXIA. Bind the three ports to dpdk driver.
   Start two testpmd::

      ./<build_target>/app/dpdk-testpmd -c 0xf --socket-mem 1024,0 --file-prefix=rx -a 0000:07:00.1 \
      -- -i --port-topology=chained

      testpmd> set macsec offload 0 on encrypt on replay-protect on
      testpmd> set macsec sc rx 0 00:00:00:00:00:01 0
      testpmd> set macsec sa rx 0 0 0 0 00112200000000000000000000000000
      testpmd> set macsec sc tx 0 00:00:00:00:00:02 0
      testpmd> set macsec sa tx 0 0 0 0 00112200000000000000000000000000
      testpmd> set fwd rxonly

      ./<build_target>/app/dpdk-testpmd -c 0xf0 --socket-mem 1024,0 --file-prefix=tx -b 0000:07:00.1 \
      -- -i --port-topology=chained

      testpmd> set macsec offload 1 on encrypt on replay-protect on
      testpmd> set macsec sc rx 1 00:00:00:00:00:02 0
      testpmd> set macsec sa rx 1 0 0 0 00112200000000000000000000000000
      testpmd> set macsec sc tx 1 00:00:00:00:00:01 0
      testpmd> set macsec sa tx 1 0 0 0 00112200000000000000000000000000
      testpmd> set fwd mac

   Start on both two testpmd.
   Start data transmit from IXIA port, the frame size is 64bytes,
   the Ethertype is 0x0800. The rate is 14.88Mpps.

   Check the linerate on rxonly port::

      testpmd> show port stats 0

   It shows "Rx-pps:     10775697", so the rx %linerate is 100%.
   Check the MACsec packets number on tx side::

      testpmd> show port xstats 1

   On rx side::

      testpmd> show port xstats 0

   Check the rx data and tx data::

      in_pkts_ok == out_pkts_encrypted
