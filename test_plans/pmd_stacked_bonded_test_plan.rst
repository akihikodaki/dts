.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2019 Intel Corporation

==============
stacked Bonded
==============

Stacked bonded mechanism allow a bonded port to be added to another bonded port.

The demand arises from a discussion with a prospective customer for a 100G NIC
based on RRC. The customer already uses Mellanox 100G NICs. Mellanox 100G NICs
support a proper x16 PCIe interface so the host sees a single netdev and that
netdev corresponds directly to the 100G Ethernet port. They indicated that in
their current system they bond multiple 100G NICs together, using DPDK bonding
API in their application. They are interested in looking at an alternative source
for the 100G NIC and are in conversation with Silicom who are shipping a 100G
RRC based NIC (something like Boulder Rapids). The issue they have with RRC NIC
is that the NIC presents as two PCIe interfaces (netdevs) instead of one. If the
DPDK bonding could operate at 1st level on the two RRC netdevs to present a
single netdev could the application then bond multiple of these bonded
interfaces to implement NIC bonding.

Prerequisites
=============

hardware configuration
----------------------

all link ports of tester/dut should be the same data rate and support full-duplex.
Slave down test cases need four ports at least, other test cases can run with
two ports.

NIC/DUT/TESTER ports requirements::

     DUT:     2/4 ports.
     TESTER:  2/4 ports.

port topology diagram(4 peer links)::

       TESTER                                   DUT
                  physical link             logical link
     .---------.                .-------------------------------------------.
     | portA 0 | <------------> | portB 0 <---> .--------.                  |
     |         |                |               | bond 0 | <-----> .------. |
     | portA 0a| <------------> | portB 1 <---> '--------'         |      | |
     |         |                |                                  |bond2 | |
     | portA 1 | <------------> | portB 2 <---> .--------.         |      | |
     |         |                |               | bond 1 | <-----> '------' |
     | portA 1a| <------------> | portB 3 <---> '--------'                  |
     '---------'                '-------------------------------------------'

Test cases
==========
``tx-offloads`` value set based on nic type. Test cases' steps, which run for
slave down testing, are based on 4 ports. Other test cases' steps are based on
2 ports.

Test Case: basic behavior
=========================
allow a bonded port to be added to another bonded port, which is
supported by::

   balance-rr    0
   active-backup 1
   balance-xor   2
   broadcast     3
   balance-tlb   5

#. 802.3ad mode is not supported if one or more slaves is a bond device.
#. add the same device twice to check exceptional process is good.
#. master bonded port/each slaves queue configuration is the same.

steps
-----

#. bind two ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2>

#. boot up testpmd, stop all ports::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 -- -i --tx-offloads=<0xXXXX>
    testpmd> port stop all

#. create first bonded port and add one slave, check bond 2 config status::

    testpmd> create bonded device <mode> 0
    testpmd> add bonding slave 0 2
    testpmd> show bonding config 2

#. create second bonded port and add one slave, check bond 3 config status::

    testpmd> create bonded device <mode> 0
    testpmd> add bonding slave 1 3
    testpmd> show bonding config 3

#. create third bonded port and add first/second bonded port as its' slaves.
   check if slaves are added successful. stacked bonded is forbidden by mode 4,
   mode 4 will fail to add a bonded port as its' slave::

    testpmd> create bonded device <mode> 0
    testpmd> add bonding slave 2 4
    testpmd> add bonding slave 3 4
    testpmd> show bonding config 4

#. check master bonded port/slave port's queue configuration are the same::

    testpmd> show bonding config 0
    testpmd> show bonding config 1
    testpmd> show bonding config 2
    testpmd> show bonding config 3
    testpmd> show bonding config 4

#. start top level bond port to check ports start action::

    testpmd> port start 4
    testpmd> start

#. close testpmd::

    testpmd> stop
    testpmd> quit

#. repeat upper steps with the following mode number::

    balance-rr    0
    active-backup 1
    balance-xor   2
    broadcast     3
    802.3ad       4
    balance-tlb   5

Test Case: active-backup stacked bonded rx traffic
==================================================
setup dut/testpmd stacked bonded ports, send tcp packet by scapy and check
testpmd packet statistics.

steps
-----

#. bind two ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2>

#. boot up testpmd, stop all ports::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 -- -i --tx-offloads=<0xXXXX>
    testpmd> port stop all

#. create first bonded port and add one port as slave::

    testpmd> create bonded device 1 0
    testpmd> add bonding slave 0 2

#. create second bonded port and add one port as slave::

    testpmd> create bonded device 1 0
    testpmd> add bonding slave 1 3

#. create third bonded port and add first/second bonded ports as its' slaves,
   check if slaves are added successful::

    testpmd> create bonded device 1 0
    testpmd> add bonding slave 2 4
    testpmd> add bonding slave 3 4
    testpmd> show bonding config 4

#. start top level bond port::

    testpmd> port start 4
    testpmd> start

#. send 100 tcp packets to portA 0 and portA 1::

    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 0>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 1>)

#. first/second bonded port should receive 100 packets, third bonded port
   should receive 200 packets::

    testpmd> show port stats all

#. close testpmd::

    testpmd> stop
    testpmd> quit

Test Case: active-backup stacked bonded rx traffic with slave down
==================================================================
setup dut/testpmd stacked bonded ports, set one slave of 1st level bonded port
to down status, send tcp packet by scapy and check testpmd packet statistics.

steps
-----

#. bind four ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2> \
                                               <pci address 3> <pci address 4>

#. boot up testpmd, stop all ports::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 -- -i --tx-offloads=<0xXXXX>
    testpmd> port stop all

#. create first bonded port and add two ports as slaves::

    testpmd> create bonded device 1 0
    testpmd> add bonding slave 0 4
    testpmd> add bonding slave 1 4

#. set portB 1 down::

    testpmd> set link-down port <portB 1>

#. create second bonded port and add two ports as slaves::

    testpmd> create bonded device 1 0
    testpmd> add bonding slave 2 5
    testpmd> add bonding slave 3 5

#. set portB 3 down::

    testpmd> set link-down port <portB 3>

#. create third bonded port and add first/second bonded port as its' slaves,
   check if slave is added successful::

    testpmd> create bonded device 1 0
    testpmd> add bonding slave 4 6
    testpmd> add bonding slave 5 6
    testpmd> show bonding config 6

#. start top level bond port::

    testpmd> port start 6
    testpmd> start

#. send 100 packets to portA 0/portA 0a/portA 1/portA 1a separately::

    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 0>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 0a>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 1>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 1a>)

#. check first/second bonded ports should receive 100 packets, third bonded
   device should receive 200 packets.::

    testpmd> show port stats all

#. close testpmd::

    testpmd> stop
    testpmd> quit

Test Case: balance-xor stacked bonded rx traffic
================================================
setup dut/testpmd stacked bonded ports, send tcp packet by scapy and check
packet statistics.

steps
-----

#. bind two ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2>

#. boot up testpmd, stop all ports::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 -- -i --tx-offloads=<0xXXXX>
    testpmd> port stop all

#. create first bonded port and add one port as slave::

    testpmd> create bonded device 2 0
    testpmd> add bonding slave 0 2

#. create second bonded port and add one port as slave::

    testpmd> create bonded device 2 0
    testpmd> add bonding slave 1 3

#. create third bonded port and add first/second bonded ports as its' slaves
   check if slaves are added successful::

    testpmd> create bonded device 2 0
    testpmd> add bonding slave 2 4
    testpmd> add bonding slave 3 4
    testpmd> show bonding config 4

#. start top level bond port::

    testpmd> port start 4
    testpmd> start

#. send 100 packets to portA 0 and portA 1::

    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 0>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 1>)

#. check first/second bonded port should receive 100 packets, third bonded
   device should receive 200 packets::

    testpmd> show port stats all

#. close testpmd::

    testpmd> stop
    testpmd> quit

Test Case: balance-xor stacked bonded rx traffic with slave down
================================================================
setup dut/testpmd stacked bonded ports, set one slave of 1st level bonded
device to down status, send tcp packet by scapy and check packet statistics.

steps
-----

#. bind four ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2> \
                                               <pci address 3> <pci address 4>

#. boot up testpmd, stop all ports::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 -- -i --tx-offloads=<0xXXXX>
    testpmd> port stop all

#. create first bonded port and add two ports as slaves, set portA 0a down::

    testpmd> create bonded device 2 0
    testpmd> add bonding slave 0 4
    testpmd> add bonding slave 1 4
    testpmd> port stop 1

#. set portB 1 down::

    testpmd> set link-down port <portB 1>

#. create second bonded port and add two ports as slaves, set portA 1a down::

    testpmd> create bonded device 2 0
    testpmd> add bonding slave 2 5
    testpmd> add bonding slave 3 5
    testpmd> port stop 3

#. set portB 3 down::

    testpmd> set link-down port <portB 3>

#. create third bonded port and add first/second bonded port as its' slaves
   check if slave is added successful::

    testpmd> create bonded device 2 0
    testpmd> add bonding slave 4 6
    testpmd> add bonding slave 5 6
    testpmd> show bonding config 6

#. start top level bond port::

    testpmd> port start 6
    testpmd> start

#. send 100 packets to portA 0/portA 0a/portA 1/portA 1a separately::

    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 0>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 0a>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 1>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 1a>)

#. check first/second bonded port should receive 100 packets, third bonded
   device should receive 200 packets::

    testpmd> show port stats all

#. close testpmd::

    testpmd> stop
    testpmd> quit