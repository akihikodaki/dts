.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2016-2017 Intel Corporation

===========================
VLAN Ethertype Config Tests
===========================

Description
===========
for single vlan default TPID is 0x8100.
for QinQ, default S-Tag+C-Tag VLAN TPIDs 0x88A8 + 0x8100.
This feature implemented configuration of VLAN ethertype TPID,
such as changing single vlan TPID 0x8100 to 0xA100, or changing QinQ "0x88A8 + 0x8100" \
to "0x9100+0xA100" or "0x8100+0x8100"

Prerequisites
=============

1. Hardware:
   one Intel® Ethernet 700 Series NIC (4x 10G or 2x10G or 2x40G or 1x10G)

2. Software:

   * DPDK: http://dpdk.org/git/dpdk
   * Scapy: http://www.secdev.org/projects/scapy/

3. Assuming that DUT ports ``0`` and ``1`` are connected to the tester's port ``A`` and ``B``.

Test Case 1: change VLAN TPID
=============================

1. Start testpmd, start in rxonly mode::

      ./dpdk-testpmd -c 0xff -n 4 -- -i --portmask=0x3
      testpmd> set fwd rxonly
      testpmd> set verbose 1
      testpmd> start

2. Change VLAN TPIDs to 0xA100::

      testpmd> vlan set outer tpid 0xA100 0

3. send a packet with VLAN TPIDs = 0xA100, verify it can be recognized as vlan packet.

Test Case 2: test VLAN filtering on/off
=======================================

1. Start testpmd, setup vlan filter on, start in mac forwarding mode::

      ./dpdk-testpmd -c 0xff -n 4 -- -i --portmask=0x3
      testpmd> set fwd mac
      testpmd> vlan set filter on 0
      testpmd> start

      Due to the kernel enables Qinq and cannot be closed, the DPDK only add `extend on` to make the VLAN filter
      work normally. Therefore, if the i40e firmware version >= 8.4 the DPDK can only add `extend on` to make the VLAN filter work normally:
      testpmd> vlan set extend on 0

2. Send 1 packet with VLAN TPID 0xA100 and VLAN Tag 16 on port ``A``,
   Verify that the VLAN packet cannot be received in port ``B``.

3. Disable vlan filtering on port ``0``::

      testpmd> vlan set filter off 0

4. Change VLAN TPIDs to 0xA100 on port ``0``::

      testpmd> vlan set outer tpid 0xA100 0

5. Send 1 packet with VLAN TPID 0xA100 and VLAN Tag 16 on port ``A``,
   Verify that the VLAN packet can be received in port ``B`` and TPID is 0xA100

Test Case 3: test adding VLAN Tag Identifier with changing VLAN TPID
====================================================================

1. start testpmd, setup vlan filter on, start in mac forwarding mode::

      ./dpdk-testpmd -c 0xff -n 4 -- -i --portmask=0x3
      testpmd> set fwd mac
      testpmd> vlan set filter on 0
      testpmd> vlan set strip off 0
      testpmd> start

      Due to the kernel enables Qinq and cannot be closed, the DPDK only add `extend on` to make the VLAN filter
      work normally. Therefore, if the i40e firmware version >= 8.4 the DPDK can only add `extend on` to make the VLAN filter work normally:
      testpmd> vlan set extend on 0

2. Add a VLAN Tag Identifier ``16`` on port ``0``::

      testpmd> rx_vlan add 16 0

3. Send 1 packet with the VLAN Tag 16 on port ``A``,
   Verify that the VLAN packet can be received in port ``B`` and TPID is 0x8100

4. Change VLAN TPID to 0xA100 on port ``0``::

      testpmd> vlan set outer tpid 0xA100 0

5. Send 1 packet with VLAN TPID 0xA100 and VLAN Tag 16 on port ``A``,
   Verify that the VLAN packet can be received in port ``B`` and TPID is 0xA100

6. Remove the VLAN Tag Identifier ``16`` on port ``0``::

      testpmd> rx_vlan rm 16 0

7. Send 1 packet with VLAN TPID 0xA100 and VLAN Tag 16 on port ``A``,
   Verify that the VLAN packet cannot be received in port ``B``.

Test Case 4: test VLAN header stripping with changing VLAN TPID
===============================================================

1. start testpmd, setup vlan filter off, vlan strip on, start in mac forwarding mode::

      ./dpdk-testpmd -c 0xff -n 4 -- -i --portmask=0x3
      testpmd> set fwd mac
      testpmd> vlan set filter off 0
      testpmd> vlan set strip on 0
      testpmd> start

2. Send 1 packet with the VLAN Tag 16 on port ``A``.
   Verify that packet received in port ``B`` without VLAN Tag Identifier

3. Change VLAN TPID to 0xA100 on port ``0``::

      testpmd> vlan set outer tpid 0xA100 0

4. Send 1 packet with VLAN TPID 0xA100 and VLAN Tag 16 on port ``A``.
   Verify that packet received in port ``B`` without VLAN Tag Identifier

5. Disable vlan header stripping on port ``0``::

      testpmd> vlan set strip off 0

6. Send 1 packet with VLAN TPID 0xA100 and VLAN Tag 16 on port ``A``.
   Verify that packet received in port ``B`` with VLAN Tag Identifier.


Test Case 5: test VLAN header inserting with changing VLAN TPID
===============================================================

1. start testpmd, enable vlan packet forwarding, start in mac forwarding mode::

      ./dpdk-testpmd -c 0xff -n 4 -- -i --portmask=0x3
      testpmd> set fwd mac
      testpmd> vlan set filter off 0
      testpmd> vlan set strip off 0
      testpmd> start

2. Insert VLAN Tag Identifier ``16`` on port ``1``::

      testpmd> tx_vlan set 1 16

3. Send 1 packet without VLAN Tag Identifier on port ``A``.  Verify that
   packet received in port ``B`` with VLAN Tag Identifier 16 and TPID is
   0x8100

4. Change VLAN TPID to 0xA100 on port ``1``::

      testpmd> vlan set outer tpid 0xA100 1

5. Send 1 packet without VLAN Tag Identifier on port ``A``.  Verify that
   packet received in port ``B`` with VLAN Tag Identifier 16 and TPID is
   0xA100.

6. Delete the VLAN Tag Identifier ``16`` on port ``1``::

      testpmd> tx_vlan reset 1

7. Send 1 packet without VLAN Tag Identifier on port ``A``.  Verify that packet
   received in port ``B`` without VLAN Tag Identifier 16.


Test Case 6: Change S-Tag and C-Tag within QinQ
=================================================

1. Start testpmd, enable QinQ, start in rxonly mode::

      ./dpdk-testpmd -c 0xff -n 4 -- -i --portmask=0x3
      testpmd> vlan set qinq on 0
      testpmd> set fwd rxonly
      testpmd> set verbose 1
      testpmd> start

2. Change S-Tag+C-Tag VLAN TPIDs to 0x88A8 + 0x8100::

      testpmd> vlan set outer tpid 0x88A8 0
      testpmd> vlan set inner tpid 0x8100 0

3. Send a packet with set S-Tag+C-Tag VLAN TPIDs to 0x88A8 + 0x8100.
   verify it can be recognized as qinq packet.

4. Change S-Tag+C-Tag VLAN TPIDs to 0x9100+0xA100::

      testpmd> vlan set outer tpid 0x9100 0
      testpmd> vlan set inner tpid 0xA100 0

5. Send a packet with set S-Tag+C-Tag VLAN TPIDs to 0x9100+0xA100.
   verify it can be recognized as qinq packet.

6. Change S-Tag+C-Tag VLAN TPIDs to 0x8100+0x8100::

      testpmd> vlan set outer tpid 0x8100 0
      testpmd> vlan set inner tpid 0x8100 0

7. Send a packet with set S-Tag+C-Tag VLAN TPIDs to 0x8100+0x8100.
   verify it can be recognized as qinq packet.


Note:

Send packet with specific S-Tag+C-Tag VLAN TPID:

1. ``wrpcap("qinq.pcap",[Ether(dst="68:05:CA:3A:2E:58")/Dot1Q(type=0x8100,vlan=16)/Dot1Q(type=0x8100,vlan=1006)/IP(src="192.168.0.1", dst="192.168.0.2")])``.
2. hexedit qinq.pcap; change tpid field, "ctrl+w" to save, "ctrl+x" to exit.
3. sendp(rdpcap("qinq.pcap"), iface="ens260f0").

Send packet with specific VLAN TPID:

1. ``wrpcap("vlan.pcap",[Ether(dst="68:05:CA:3A:2E:58")/Dot1Q(type=0x8100,vlan=16)/IP(src="192.168.0.1", dst="192.168.0.2")])``.
2. hexedit vlan.pcap; change tpid field, "ctrl+w" to save, "ctrl+x" to exit.
3. sendp(rdpcap("vlan.pcap"), iface="ens260f0").
