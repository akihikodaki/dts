.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

==================
VLAN Offload Tests
==================

The support of VLAN offload features by Poll Mode Drivers consists in:

- the filtering of received VLAN packets,
- VLAN header stripping by hardware in received [VLAN] packets,
- VLAN header insertion by hardware in transmitted packets.

The filtering of VLAN packets is automatically enabled by the ``testpmd``
application for each port.
By default, the VLAN filter of each port is empty and all received VLAN packets
are dropped by the hardware.
To enable the receipt of VLAN packets tagged with the VLAN tag identifier
``vlan_id`` on the port ``port_id``, the following command of the ``testpmd``
application must be used::

  rx_vlan add vlan_id port_id

In the same way, the insertion of a VLAN header with the VLAN tag identifier
``vlan_id`` in packets sent on the port ``port_id`` can be enabled with the
following command of the ``testpmd`` application::

  tx_vlan set port_id vlan_id


The transmission of VLAN packets is done with the ``start tx_first`` command
of the ``testpmd`` application that arranges to first send a burst of packets
on all configured ports before starting the ``rxonly`` packet forwarding mode
that has been previously selected.

Prerequisites
=============

Assuming that ports ``0`` and ``1`` are connected to a traffic generator's port
``A`` and ``B``. Launch the ``testpmd`` with the following arguments::

  ./build/app/dpdk-testpmd -cffffff -n 3 -- -i --burst=1 --txpt=32 \
  --txht=8 --txwt=0 --txfreet=0 --rxfreet=64 --mbcache=250 --portmask=0x3

The -n command is used to select the number of memory channels. It should match the number of memory channels on that setup.

Set the verbose level to 1 to display information for each received packet::

  testpmd> set verbose 1
  testpmd> vlan set filter on

Test Case: Enable receipt of VLAN packets and disable VLAN header stripping
===========================================================================

Setup the ``mac`` forwarding mode::

  testpmd> set fwd mac
  Set mac packet forwarding mode

Enable the receipt of VLAN packets with VLAN Tag Identifier 1 on port 0::

  testpmd> rx_vlan add 1 0
  testpmd> vlan set strip off 0
  
  Due to the kernel enables Qinq and cannot be closed, the DPDK only add `extend on` to make the VLAN filter
  work normally. Therefore, if the i40e firmware version >= 8.4 the DPDK can only add `extend on` to make the VLAN filter work normally:
  testpmd> vlan set extend on 0
  
  testpmd> start
    rxonly packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Configure the traffic generator to send VLAN packets with the Tag Identifier
 ``1`` and send 1 packet on port ``A``.

Verify that the VLAN packet was correctly received on port ``B`` with VLAN tag ``1``.

Configure the traffic generator to send VLAN packets with not matched Tag
Identifier and send 1 packet on port ``A``.

Verify that the VLAN packet was not correctly received on port ``B`` with
this not matched VLAN Tag.

Test Case: Enable receipt of VLAN packets and VLAN header stripping
===================================================================

Setup the ``mac`` forwarding mode::

  testpmd> set fwd mac
  Set mac packet forwarding mode

Enable the receipt of VLAN packets with VLAN Tag Identifier 1 on port 0::

  testpmd> rx_vlan add 1 0
  testpmd> vlan set strip on 0
  testpmd> start
    rxonly packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Configure the traffic generator to send VLAN packets with the Tag Identifier
 ``1`` and send 1 packet on port ``A``.

Verify that the VLAN packet was correctly received on port ``B`` without VLAN tag ``1``.

Test Case: Disable receipt of VLAN packets
==========================================

Disable the receipt of VLAN packets with Tag Identifier ``1`` on port 0.
Send VLAN packets with the Tag Identifier ``1`` check that no packet is received
on port ``B``, meaning that VLAN packets are now dropped on port 0::
  
  Due to the kernel enables Qinq and cannot be closed, the DPDK only add `extend on` to make the VLAN filter
  work normally. Therefore, if the i40e firmware version >= 8.4 the DPDK can only add `extend on` to make the VLAN filter work normally:
  testpmd> vlan set extend on 0
  
  testpmd> rx_vlan rm 1 0
  testpmd> start
  rxonly packet forwarding - CRC stripping disabled - packets/burst=32
  nb forwarding cores=1 - nb forwarding ports=8
  RX queues=1 - RX desc=128 - RX free threshold=64
  RX threshold registers: pthresh=8 hthresh=8 wthresh=4
  TX queues=1 - TX desc=512 - TX free threshold=0
  TX threshold registers: pthresh=32 hthresh=8 wthresh=8
  testpmd> stop


Verify that no packet was received on port ``B``.


Test Case: Enable VLAN header insertion in transmitted packets
==============================================================
Arrange to only send packets on port 0::

  testpmd> set nbport 1
  Number of forwarding ports set to 1

Arrange to send one VLAN packet with VLAN Tag Identifier ``1`` on port ``0``::

  testpmd> tx_vlan set 1 0
  testpmd> start tx_first

Verify that the packet is correctly received on the traffic generator side
(with VLAN Tag Identifier ``1``)
