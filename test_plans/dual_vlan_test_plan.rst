.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

=======================
Dual VLAN Offload Tests
=======================

The support of Dual VLAN offload features by Poll Mode Drivers consists in:

- Dynamically enable/disable inner VLAN filtering on an interface on x7xx series, 82576/82599,
- Dynamically enable/disable extended VLAN mode on 82576/82599,
- Dynamically configure outer VLAN TPID value, i.e. S-TPID value, on 82576/82599.

Prerequisites
=============

In this feature, x7xx series, Intel® Ethernet 800 Series, 82576 and 82599 are supported.

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

Assuming that ports ``0`` and ``1`` are connected to the traffic generator's port ``A`` and ``B``,
launch the ``testpmd`` with the following arguments::

  ./<build>/app/dpdk-testpmd -c ffffff -n 3 -- -i --burst=1 --txpt=32 \
      --txht=8 --txwt=0 --txfreet=0 --rxfreet=64 --mbcache=250 --portmask=0x3

The -n command is used to select the number of memory channels. It should match the number of memory channels on that setup.

Test Case: Enable/Disable VLAN packets filtering
================================================

Due to the kernel enables Qinq and cannot be closed, the DPDK only add `extend on` to make the VLAN filter
work normally. Therefore, if the i40e firmware version >= 8.4 the DPDK can only add `extend on` to make the VLAN filter work normally::

    testpmd> vlan set extend on 0

Setup the ``mac`` forwarding mode::

    testpmd> set fwd mac
    Set mac packet forwarding mode

Enable vlan filtering on port 0::

    testpmd> vlan set filter on 0

Disable extend on port 0::

    testpmd> vlan set extend off 0

Check whether the mode is set successful::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    MAC address: 90:E2:BA:1B:DF:60
    Link status: up
    Link speed: 10000 Mbps
    Link duplex: full-duplex
    Promiscuous mode: enabled
    Allmulticast mode: disabled
    Maximum number of MAC addresses: 127
    VLAN offload:
        strip off, filter on, extend on, qinq strip off

start forwarding packets::

    testpmd> start
    mac packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Configure the traffic generator to send VLAN packets with the Tag Identifier
 ``1`` and send 1 packet on port ``A``.Verify that the VLAN packet cannot
 been received in port ``B``.

Disable vlan filtering on port ``0``::

    testpmd> vlan set filter off 0

Check whether the mode is set successful::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    MAC address: 90:E2:BA:1B:DF:60
    Link status: up
    Link speed: 10000 Mbps
    Link duplex: full-duplex
    Promiscuous mode: enabled
    Allmulticast mode: disabled
    Maximum number of MAC addresses: 127
    VLAN offload:
      strip off
      filter off
      qinq(extend) off

Configure the traffic generator to send VLAN packets with the Tag Identifier
 ``1`` and send 1 packet on port ``A``.Verify that the VLAN packet can been
 received in port ``B`` with VLAN Tag Identifier ``1``.

Test Case: Add/Remove VLAN Tag Identifier pass VLAN filtering
=============================================================

Disable VLAN packet extend and strip port ``0``::

    testpmd> vlan set extend off 0
    testpmd> vlan set strip off 0

Due to the kernel enables Qinq and cannot be closed, the DPDK only add `extend on` to make the VLAN filter
work normally. Therefore, if the i40e firmware version >= 8.4 the DPDK can only add `extend on` to make the VLAN filter work normally::

    testpmd> vlan set extend on 0

Enable VLAN filtering on port ``0``::

    testpmd> vlan set filter on 0

Add a VLAN Tag Identifier ``1`` on port ``0``::

    testpmd> rx_vlan add 1 0

Configure the traffic generator to send VLAN packets with the Tag Identifier
 ``1`` and send 1 packet on port ``A``.Verify that the VLAN packet can been
 received in port ``B``.

Remove the VLAN Tag Identifier ``1`` on port ``0``::

    testpmd> rx_vlan rm 1 0

Configure the traffic generator to send VLAN packets with the Tag Identifier
 ``1`` and send 1 packet on port ``A``.Verify that the VLAN packet cannot been
 received in port ``B``.

Test Case: Enable/Disable VLAN header stripping
===============================================

Enable vlan packet forwarding on port ``0`` first::

    testpmd> vlan set filter off 0

Enable vlan header stripping on port ``0``::

    testpmd> vlan set strip on 0

Check whether the mode is set successful::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    MAC address: 90:E2:BA:1B:DF:60
    Link status: up
    Link speed: 10000 Mbps
    Link duplex: full-duplex
    Promiscuous mode: enabled
    Allmulticast mode: disabled
    Maximum number of MAC addresses: 127
    VLAN offload:
      strip on
      filter off
      qinq(extend) off

Configure the traffic generator to send VLAN packets with the Tag Identifier
``1`` and send 1 packet on port ``A``. Verify that the packet without VLAN Tag
Identifier can been received in port ``B``.

Disable vlan header stripping on port ``0``::

    testpmd> vlan set strip off 0

Check whether the mode is set successfully::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    MAC address: 90:E2:BA:1B:DF:60
    Link status: up
    Link speed: 10000 Mbps
    Link duplex: full-duplex
    Promiscuous mode: enabled
    Allmulticast mode: disabled
    Maximum number of MAC addresses: 127
    VLAN offload:
      strip off
      filter off
      qinq(extend) off

Configure the traffic generator to send VLAN packets with the Tag Identifier
``1`` and send 1 packet on port ``A``. Verify that the packet with VLAN Tag
Identifier ``1`` can been received in port ``B``.

Test Case: Enable/Disable VLAN header stripping in queue
========================================================

Enable vlan packet forwarding on port ``0`` first::

    testpmd> vlan set filter off 0

Disable vlan header stripping on port ``0``::

    testpmd> vlan set strip off 0

Disable vlan header stripping in queue 0 on port ``0``::

    testpmd> vlan set stripq off 0,0

Configure the traffic generator to send VLAN packets with the Tag Identifier
``1`` and send 1 packet on port ``A``. Verify that the packet with VLAN Tag
Identifier ``1`` can been received in port ``B``.


Enable vlan header stripping in queue 0 on port ``0``::

    testpmd> vlan set stripq on 0,0

Configure the traffic generator to send VLAN packets with the Tag Identifier
``1`` and send 1 packet on port ``A``. Verify that the packet without VLAN Tag
Identifier ``1`` can been received in port ``B``.

Enable vlan header stripping on port ``0``.

    MISSING COMMAND

Configure the traffic generator to send VLAN packets with the Tag Identifier
``1`` and send 1 packet on port ``A``. Verify that the packet without VLAN Tag
Identifier ``1`` can been received in port ``B``.

Test Case: Enable/Disable VLAN header inserting
===============================================

Enable vlan packet forwarding on port ``0`` first::

    testpmd> vlan set filter off 0

Insert VLAN Tag Identifier ``1`` on port ``1``::

    testpmd> port stop all
    testpmd> tx_vlan set 1 1
    testpmd> port start all

Configure the traffic generator to send VLAN packet without VLAN Tag Identifier
and send 1 packet on port ``A``. Verify that the packet can been received on port
``B`` with VLAN Tag Identifier ``1``.

Delete the VLAN Tag Identifier ``1`` on port ``1``::

    testpmd> port stop all
    testpmd> tx_vlan reset 1
    testpmd> port start all

Configure the traffic generator to send VLAN packet without VLAN Tag Identifier
and send 1 packet on port ``A``. Verify that the packet can been received on port
``B`` without VLAN Tag Identifier.


Test Case: Configure receive port inner VLAN TPID
=================================================

Enable vlan header QinQ on port ``0`` firstly to support set TPID::

    testpmd> vlan set extend on 0

Check whether the mode is set successfully::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    MAC address: 90:E2:BA:1B:DF:60
    Link status: up
    Link speed: 10000 Mbps
    Link duplex: full-duplex
    Promiscuous mode: enabled
    Allmulticast mode: disabled
    Maximum number of MAC addresses: 127
    VLAN offload:
      strip off, filter off, extend on, qinq strip off

Set Tag Protocol ID ``0x1234`` on port ``0``.
Nic only support inner model, except Intel® Ethernet 700 Series::

    testpmd> vlan set inner tpid 0x1234 0

Enable vlan packet filtering and strip on port ``0`` ::

    testpmd> vlan set filter on 0
    testpmd> vlan set strip on 0

Configure the traffic generator to send VLAN packet whose outer vlan tag is ``0x1``,
inter vlan tag is ``0x2`` and outer Tag Protocol ID is ``0x8100`` and send 1 packet
on port ``A``. Verify that one packet whose vlan header has not been strip has been
received on port ``B``.

Set Tag Protocol ID ``0x8100`` on port ``0``::

    testpmd> vlan set inner tpid 0x8100 0

Configure the traffic generator to send VLAN packet whose outer vlan tag is ``0x1``,
inter vlan tag is ``0x2`` and outer Tag Protocol ID is ``0x8100`` and send 1 packet
on port ``A``. Verify that no packets has been received on port ``B``

Test Case: Strip/Filter/Extend/Insert enable/disable synthetic test
===================================================================

Do the synthetic test following the below table and check the result is the same
as the table(the inserted VLAN Tag Identifier is limited to ``0x3``, and all modes
except insert are set on rx port).

+-------------------------------------------------------+-----------------------+
|                  Configure setting                    |       Result          |
+=======+=======+========+============+========+========+=======+=======+=======+
| Outer | Inner |  Vlan  |   Vlan     | Vlan   | Vlan   | Pass/ | Outer | Inner |
| vlan  | vlan  |  strip |   filter   | extend | insert | Drop  | vlan  | vlan  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |     no     |   no   |   no   | pass  |  0x1  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |     no     |   no   |   no   | pass  |  no   |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x1   |   no   |   no   | pass  |  0x1  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x2   |   no   |   no   | drop  |  no   |  no   |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x1   |   no   |   no   | pass  |  no   |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x2   |   no   |   no   | drop  |  no   |  no   |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |     no     |  yes   |   no   | pass  |  0x1  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |     no     |  yes   |   no   | pass  |  no   |  0x1  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x1   |  yes   |   no   | drop  |  no   |  no   |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x2   |  yes   |   no   | pass  |  0x1  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x1   |  yes   |   no   | drop  |  no   |  no   |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x2   |  yes   |   no   | pass  |  no   |  0x1  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |     no     |   no   |  yes   | pass  |  0x3  |  0x1  |
|       |       |        |            |        |        |       |       |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |     no     |   no   |  yes   | pass  |  0x3  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x1   |   no   |  yes   | pass  |  0x3  |  0x1  |
|       |       |        |            |        |        |       |       |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x2   |   no   |  yes   | drop  |  no   |  no   |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x1   |   no   |  yes   | pass  |  0x3  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x2   |   no   |  yes   | drop  |  no   |  no   |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |     no     |  yes   |  yes   | pass  |  0x3  |  0x1  |
|       |       |        |            |        |        |       |       |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |     no     |  yes   |  yes   | pass  |  0x3  |  0x1  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x1   |  yes   |  yes   | drop  |  no   |  no   |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x2   |  yes   |  yes   | pass  |  0x3  |  0x1  |
|       |       |        |            |        |        |       |       |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x1   |  yes   |  yes   | drop  |  no   |  no   |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x2   |  yes   |  yes   | pass  |  0x3  |  0x1  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+

Due to the kernel enables Qinq and cannot be closed, the DPDK only add `extend on` to make the VLAN filter
work normally. Therefore, if the i40e firmware >= 8.4 the synthetic test according to the following table.
In addition, filter inner vlan when firmware <= 8.3, filter outer vlan when firmware >= 8.4.

+-------------------------------------------------------+-----------------------+
|                  Configure setting                    |       Result          |
+=======+=======+========+============+========+========+=======+=======+=======+
| Outer | Inner |  Vlan  |   Vlan     | Vlan   | Vlan   | Pass/ | Outer | Inner |
| vlan  | vlan  |  strip |   filter   | extend | insert | Drop  | vlan  | vlan  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |     no     |   no   |   no   | pass  |  0x1  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |     no     |   no   |   no   | pass  |  no   |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x1   |   no   |   no   | pass  |  0x1  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x2   |   no   |   no   | pass  |  0x1  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x1   |   no   |   no   | pass  |  no   |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x2   |   no   |   no   | pass  |  no   |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |     no     |  yes   |   no   | pass  |  0x1  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |     no     |  yes   |   no   | pass  |  no   |  0x1  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x1   |  yes   |   no   | pass  |  0x1  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x2   |  yes   |   no   | drop  |  no   |   no  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x1   |  yes   |   no   | pass  |  no   |  0x1  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x2   |  yes   |   no   | drop  |  no   |  no   |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |     no     |   no   |  yes   | pass  |  0x3  |  0x1  |
|       |       |        |            |        |        |       |       |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |     no     |   no   |  yes   | pass  |  0x3  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x1   |   no   |  yes   | pass  |  0x3  |  0x1  |
|       |       |        |            |        |        |       |       |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x2   |   no   |  yes   | pass  |  0x3  |  0x1  |
|       |       |        |            |        |        |       |       |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x1   |   no   |  yes   | pass  |  0x3  |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x2   |   no   |  yes   | drop  |  no   |  no   |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |     no     |  yes   |  yes   | pass  |  0x3  |  0x1  |
|       |       |        |            |        |        |       |       |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |     no     |  yes   |  yes   | pass  |  0x3  |  0x1  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x1   |  yes   |  yes   | pass  |  0x3  |  0x1  |
|       |       |        |            |        |        |       |       |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |   no   |  yes,0x2   |  yes   |  yes   | pass  |  0x3  |  0x1  |
|       |       |        |            |        |        |       |       |  0x2  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x1   |  yes   |  yes   | pass  |  0x3  |  0x1  |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+
|  0x1  |  0x2  |  yes   |  yes,0x2   |  yes   |  yes   | drop  |   no  |  no   |
+-------+-------+--------+------------+--------+--------+-------+-------+-------+

Test Case: Strip/Filter/Extend/Insert enable/disable random test
================================================================

Choose the above table's item randomly 30 times and verify that the result is right.

At last, stop packet forwarding and quit the application::
    testpmd> stop
    testpmd> quit
