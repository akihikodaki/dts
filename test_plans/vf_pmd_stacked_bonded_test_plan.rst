.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2023 Intel Corporation

=================
VF Stacked Bonded
=================

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

NIC/DUT/TESTER ports requirements:

- Tester: 2/4 ports of nic
- DUT:    2/4 ports of nic

enable ``link-down-on-close`` in tester::

   ethtool --set-priv-flags {tport_iface0} link-down-on-close on
   ethtool --set-priv-flags {tport_iface1} link-down-on-close on
   ethtool --set-priv-flags {tport_iface2} link-down-on-close on
   ethtool --set-priv-flags {tport_iface3} link-down-on-close on

create 1 vf for 4 dut ports::

   echo 0 > /sys/bus/pci/devices/0000\:31\:00.0/sriov_numvfs
   echo 0 > /sys/bus/pci/devices/0000\:31\:00.1/sriov_numvfs
   echo 0 > /sys/bus/pci/devices/0000\:31\:00.2/sriov_numvfs
   echo 0 > /sys/bus/pci/devices/0000\:31\:00.3/sriov_numvfs

disabel spoofchk for VF::

     ip link set dev {pf0_iface} vf 0 spoofchk off
     ip link set dev {pf1_iface} vf 0 spoofchk off
     ip link set dev {pf2_iface} vf 0 spoofchk off
     ip link set dev {pf3_iface} vf 0 spoofchk off

port topology diagram(4 peer links)::

    TESTER                                          DUT
                 physical link              logical link
    .---------.                .------------------------------------------------.
    | portA 0 | <------------> | portB pf0vf0 <---> .--------.                  |
    |         |                |                    | bond 0 | <-----> .------. |
    | portA 1 | <------------> | portB pf1vf0 <---> '--------'         |      | |
    |         |                |                                       |bond2 | |
    | portA 2 | <------------> | portB pf2vf0 <---> .--------.         |      | |
    |         |                |                    | bond 1 | <-----> '------' |
    | portA 3 | <------------> | portB pf3vf0 <---> '--------'                  |
    '---------'                '------------------------------------------------'

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
   balance-alb   6

#. 802.3ad mode is not supported if one or more slaves is a bond device.
#. add the same device twice to check exceptional process is good.
#. master bonded port/each slaves queue configuration is the same.

steps
-----

#. bind two ports::

    ./usertools/dpdk-devbind.py --bind=vfio-pci <pci address 1> <pci address 2>

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

    ./usertools/dpdk-devbind.py --bind=vfio-pci <pci address 1> <pci address 2>

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
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 2>)

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

    ./usertools/dpdk-devbind.py --bind=vfio-pci <pci address 1> <pci address 2> <pci address 3> <pci address 4>

#. boot up testpmd, stop all ports::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 -- -i --tx-offloads=<0xXXXX>
    testpmd> port stop all

#. create first bonded port and add two ports as slaves::

    testpmd> create bonded device 1 0
    testpmd> add bonding slave 0 4
    testpmd> add bonding slave 1 4

#. set portB 0 down::

    ethtool --set-priv-flags {portA 0} link-down-on-close on
    ifconfig {portA 0} down

.. note::

    The vf port link status cannot be changed directly. Change the peer port to make the vf port link down.

#. create second bonded port and add two ports as slaves::

    testpmd> create bonded device 1 0
    testpmd> add bonding slave 2 5
    testpmd> add bonding slave 3 5

#. set portB 2 down::

    ethtool --set-priv-flags {portA 2} link-down-on-close on
    ifconfig {portA 2} down

.. note::

    The vf port link status cannot be changed directly. Change the peer port to make the vf port link down.

#. create third bonded port and add first/second bonded port as its' slaves,
   check if slave is added successful::

    testpmd> create bonded device 1 0
    testpmd> add bonding slave 4 6
    testpmd> add bonding slave 5 6
    testpmd> show bonding config 6

#. start top level bond port::

    testpmd> port start 6
    testpmd> start

#. send 100 packets to portB pf0vf0/portB pf1vf0/portB pf3vf0/portB pf4vf0 separately::

    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portB pf0>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 1>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portB pf2>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 3>)

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

    ./usertools/dpdk-devbind.py --bind=vfio-pci <pci address 1> <pci address 2>

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

#. send 100 packets to portB pf0vf0/portB pf1vf0/portB pf3vf0/portB pf4vf0 separately::

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

    ./usertools/dpdk-devbind.py --bind=vfio-pci <pci address 1> <pci address 2> <pci address 3> <pci address 4>

#. boot up testpmd, stop all ports::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 -- -i --tx-offloads=<0xXXXX>
    testpmd> port stop all

#. create first bonded port and add two ports as slaves::

    testpmd> create bonded device 2 0
    testpmd> add bonding slave 0 4
    testpmd> add bonding slave 1 4

#. set portB 0 down::

    ethtool --set-priv-flags {portA 0} link-down-on-close on
    ifconfig {portA 0} down

.. note::

    The vf port link status cannot be changed directly. Change the peer port to make the vf port link down.

#. create second bonded port and add two ports as slaves::

    testpmd> create bonded device 2 0
    testpmd> add bonding slave 2 5
    testpmd> add bonding slave 3 5

#. set portB 2 down::

    ethtool --set-priv-flags {portA 2} link-down-on-close on
    ifconfig {portA 2} down

.. note::

    The vf port link status cannot be changed directly. Change the peer port to make the vf port link down.

#. create third bonded port and add first/second bonded port as its' slaves
   check if slave is added successful::

    testpmd> create bonded device 2 0
    testpmd> add bonding slave 4 6
    testpmd> add bonding slave 5 6
    testpmd> show bonding config 6

#. start top level bond port::

    testpmd> port start 6
    testpmd> start

#. send 100 packets to portB pf0vf0/portB pf1vf0/portB pf3vf0/portB pf4vf0 separately::

    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portB pf0>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 1>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portB pf2>)
    sendp([Ether()/IP()/TCP()/Raw('\0'*60)], iface=<portA 3>)

#. check first/second bonded port should receive 100 packets, third bonded
   device should receive 200 packets::

    testpmd> show port stats all

#. close testpmd::

    testpmd> stop
    testpmd> quit
    
