.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2019 Intel Corporation

=================================
Link Bonding for mode 4 (802.3ad)
=================================

This test plan is mainly to test link bonding mode 4(802.3ad) function via
testpmd.

link bonding mode 4 is IEEE 802.3ad Dynamic link aggregation. Creates
aggregation groups that share the same speed and duplex settings. Utilizes all
slaves in the active aggregator according to the 802.3ad specification. DPDK
realize it based on 802.1AX specification, it includes LACP protocol and Marker
protocol. This mode requires a switch that supports IEEE 802.3ad Dynamic link
aggregation.

note: Slave selection for outgoing traffic is done according to the transmit
hash policy, which may be changed from the default simple XOR layer2 policy.

Requirements
============
#. Bonded ports shall maintain statistics similar to normal port.

#. The slave links shall be monitor for link status change. See also the concept
   of up/down time delay to handle situations such as a switch reboots, it is
   possible that its ports report "link up" status before they become usable.

#. Upon unbonding the bonding PMD driver must restore the MAC addresses that the
   slaves had before they were enslaved.

#. According to the bond type, when the bond interface is placed in promiscuous
   mode it will propagate the setting to the slave devices.

#. LACP control packet filtering offload. It is a idea of performance
   improvement, which use hardware offloads to improve packet classification.

#. support three 802.3ad aggregation selection logic modes (stable/bandwidth/
   count). The Selection Logic selects a compatible Aggregator for a port, using
   the port LAG ID. The Selection Logic may determine that the link should be
   operated as a standby link if there are constraints on the simultaneous
   attachment of ports that have selected the same Aggregator.

#. technical details refer to content attached in website::

    http://dpdk.org/ml/archives/dev/2017-May/066143.html

#. DPDK technical details refer to::

    dpdk/doc/guides/prog_guide/link_bonding_poll_mode_drv_lib.rst:
      ``Link Aggregation 802.3AD (Mode 4)``

#. linux technical document of 802.3ad as testing reference document::

    https://www.kernel.org/doc/Documentation/networking/bonding.txt:``802.3ad``

Prerequisites for Bonding
=========================
all link ports of switch/dut should be the same data rate and support full-duplex.

Functional testing hardware configuration
-----------------------------------------
NIC and DUT ports requirements:

- Tester: 2 ports of nic
- DUT:    2 ports of nic

port topology diagram::

     Tester                           DUT
    .-------.                      .-------.
    | port0 | <------------------> | port0 |
    | port1 | <------------------> | port1 |
    '-------'                      '-------'

Test Case : basic behavior start/stop
=====================================
#. check bonded device stop/start action under frequency operation status

steps
-----

#. bind two ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2>

#. boot up testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xXXXXX -n 4  -- -i --tx-offloads=0xXXXX

#. run testpmd command of bonding::

    testpmd> port stop all
    testpmd> create bonded device 4 0
    testpmd> add bonding slave 0 2
    testpmd> add bonding slave 1 2
    testpmd> set bonding lacp dedicated_queues 2 enable
    testpmd> set allmulti 0 on
    testpmd> set allmulti 1 on
    testpmd> set allmulti 2 on
    testpmd> set portlist 2

#. loop execute this step 10 times, check if bonded device still work::

    testpmd> port stop all
    testpmd> port start all
    testpmd> start
    testpmd> show bonding config 2
    testpmd> stop

#. quit testpmd::

    testpmd> stop
    testpmd> quit

Test Case : basic behavior mac
==============================
#. bonded device's default mac is one of each slave's mac after one slave has been added.
#. when no slave attached, mac should be 00:00:00:00:00:00
#. slave's mac restore the MAC addresses that the slave has before they were enslaved.

steps
-----

#. bind two ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2>

#. boot up testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xXXXXX -n 4  -- -i --tx-offloads=0xXXXX

#. run testpmd command of bonding::

    testpmd> port stop all
    testpmd> create bonded device 4 0

#. check bond device mac should be 00:00:00:00:00:00::

    testpmd> show bonding config 2

#. add two slaves to bond port::

    testpmd> add bonding slave 0 2
    testpmd> add bonding slave 1 2
    testpmd> port start all

#. check bond device mac should be one of each slave's mac::

    testpmd> show bonding config 0
    testpmd> show bonding config 1
    testpmd> show bonding config 2

#. quit testpmd::

    testpmd> stop
    testpmd> quit

Test Case : basic behavior link up/down
=======================================
#. bonded device should be down status without slaves.
#. bonded device device should have the same status of link status.
#. Active Slaves status should change with the slave status change.

steps
-----

#. bind two ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2>

#. boot up testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xXXXXX -n 4  -- -i --tx-offloads=0xXXXX

#. run testpmd command of bonding::

    testpmd> port stop all
    testpmd> create bonded device 4 0
    testpmd> add bonding slave 0 2
    testpmd> add bonding slave 1 2
    testpmd> set bonding lacp dedicated_queues 2 enable
    testpmd> set allmulti 0 on
    testpmd> set allmulti 1 on
    testpmd> set allmulti 2 on
    testpmd> set portlist 2

#. stop bonded device and check bonded device/slaves link status::

    testpmd> port stop 2
    testpmd> show bonding config 2
    testpmd> show bonding config 1
    testpmd> show bonding config 0

#. start bonded device and check bonded device/slaves link status::

    testpmd> port start 2
    testpmd> show bonding config 2
    testpmd> show bonding config 1
    testpmd> show bonding config 0

#. quit testpmd::

    testpmd> stop
    testpmd> quit

Test Case : basic behavior promiscuous  mode
============================================
#. bonded device promiscuous mode should be ``enabled`` by default.
#. bonded device/slave device should have the same status of promiscuous mode.

steps
-----

#. bind two ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2>

#. boot up testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xXXXXX -n 4  -- -i --tx-offloads=0xXXXX

#. run testpmd command of bonding::

    testpmd> port stop all
    testpmd> create bonded device 4 0

#. check if bonded device promiscuous mode is ``enabled``::

    testpmd> show bonding config 2

#. add two slaves and check if promiscuous mode is ``enabled``::

    testpmd> add bonding slave 0 2
    testpmd> add bonding slave 1 2
    testpmd> show bonding config 0
    testpmd> show bonding config 1

#. disable bonded device promiscuous mode and check promiscuous mode::

    testpmd> set promisc 2 off
    testpmd> show bonding config 2

#. enable bonded device promiscuous mode and check promiscuous mode::

    testpmd> set promisc 2 on
    testpmd> show bonding config 2

#. check slaves' promiscuous mode::

    testpmd> show bonding config 0
    testpmd> show bonding config 1

#. quit testpmd::

    testpmd> stop
    testpmd> quit

Test Case : basic behavior agg mode
===================================
#. stable is the default agg mode.
#. check 802.3ad aggregation mode configuration, support <agg_option>::
   ``count``
   ``stable``
   ``bandwidth``

steps
-----

#. bind two ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2>

#. boot up testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xXXXXX -n 4  -- -i --tx-offloads=0xXXXX

#. run testpmd command of bonding::

    testpmd> port stop all
    testpmd> create bonded device 4 0
    testpmd> add bonding slave 0 2
    testpmd> add bonding slave 1 2
    testpmd> set bonding lacp dedicated_queues 2 enable
    testpmd> set allmulti 0 on
    testpmd> set allmulti 1 on
    testpmd> set allmulti 2 on
    testpmd> set portlist 2
    testpmd> port start all
    testpmd> show bonding config 2
    testpmd> set bonding agg_mode 2 <agg_option>

#. check if agg_mode set successful::

    testpmd> show bonding config 2
    - Dev basic:
       Bonding mode: 8023AD(4)
       Balance Xmit Policy: BALANCE_XMIT_POLICY_LAYER2
       IEEE802.3AD Aggregator Mode: <agg_option>
       Slaves (2): [0 1]
       Active Slaves (2): [0 1]
       Current Primary: [0]
    - Lacp info:
        IEEE802.3 port: 2
        fast period: 900 ms
        slow period: 29000 ms
        short timeout: 3000 ms
        long timeout: 90000 ms
        aggregate wait timeout: 2000 ms
        tx period: 500 ms
        rx marker period: 2000 ms
        update timeout: 100 ms
        aggregation mode: count

        Slave Port: 0
        Aggregator port id: 0
        selection: SELECTED
        Actor detail info:
                system priority: 65535
                system mac address: 7A:1A:91:74:32:46
                port key: 8448
                port priority: 65280
                port number: 256
                port state: ACTIVE AGGREGATION DEFAULTED
        Partner detail info:
                system priority: 65535
                system mac address: 00:00:00:00:00:00
                port key: 256
                port priority: 65280
                port number: 0
                port state: ACTIVE

        Slave Port: 1
        Aggregator port id: 0
        selection: SELECTED
        Actor detail info:
                system priority: 65535
                system mac address: 5E:F7:F5:3E:58:D8
                port key: 8448
                port priority: 65280
                port number: 512
                port state: ACTIVE AGGREGATION DEFAULTED
        Partner detail info:
                system priority: 65535
                system mac address: 00:00:00:00:00:00
                port key: 256
                port priority: 65280
                port number: 0
                port state: ACTIVE

#. quit testpmd::

    testpmd> stop
    testpmd> quit

Test Case : basic behavior dedicated queues
===========================================
#. check 802.3ad dedicated queues is ``disable`` by default
#. check 802.3ad set dedicated queues, support <agg_option>::
   ``disable``
   ``enable``

steps
-----

#. bind two ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2>

#. boot up testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xXXXXX -n 4  -- -i --tx-offloads=0xXXXX

#. run testpmd command of bonding::

    testpmd> port stop all
    testpmd> create bonded device 4 0
    testpmd> add bonding slave 0 2
    testpmd> add bonding slave 1 2
    testpmd> show bonding config 2

#. check if dedicated_queues disable successful::

    testpmd> set bonding lacp dedicated_queues 2 disable

#. check if bonded port can start::

    testpmd> port start all
    testpmd> start

#. check if dedicated_queues enable successful::

    testpmd> stop
    testpmd> port stop all
    testpmd> set bonding lacp dedicated_queues 2 enable

#. check if bonded port can start::

    testpmd> port start all
    testpmd> start

#. quit testpmd::

    testpmd> stop
    testpmd> quit

Test Case : command line option
===============================
#. check command line option::

    slave=<0000:xx:00.0>
    agg_mode=<bandwidth | stable | count>

#. compare bonding configuration with expected configuration.

steps
-----

#. bind two ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2>

#. boot up testpmd ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0f -n 4 \
    --vdev 'net_bonding0,slave=0000:xx:00.0,slave=0000:xx:00.1,mode=4,agg_mode=<agg_option>'  \
    -- -i --port-topology=chained

#. run testpmd command of bonding::

    testpmd> port stop all

#. check if bonded device has been created and slaves have been bonded successful::

    testpmd> show bonding config 2
    - Dev basic:
       Bonding mode: 8023AD(4)
       Balance Xmit Policy: BALANCE_XMIT_POLICY_LAYER2
       IEEE802.3AD Aggregator Mode: <agg_option>
       Slaves (2): [0 1]
       Active Slaves (2): [0 1]
       Current Primary: [0]
    - Lacp info:
        IEEE802.3 port: 2
        fast period: 900 ms
        slow period: 29000 ms
        short timeout: 3000 ms
        long timeout: 90000 ms
        aggregate wait timeout: 2000 ms
        tx period: 500 ms
        rx marker period: 2000 ms
        update timeout: 100 ms
        aggregation mode: <agg_option>

#. check if bonded port can start::

    testpmd> port start all
    testpmd> start

#. check if dedicated_queues enable successful::

    testpmd> stop
    testpmd> port stop all

#. quit testpmd::

    testpmd> quit
