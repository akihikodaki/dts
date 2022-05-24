.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

==============================================
Port Representor Tests
==============================================

Description
===========
Use two representor ports as the control plane to manage the two VFs,
the control plane could change VFs behavior such as change promiscous
mode, stats reset, etc. our statistical data information is independent
on the control plane and data plane.

Prerequisites
===============
Create two VFs and two VFs representor ports which are used as control plane.

1. bind PF to igb_uio::

    ./usertools/dpdk-devbind.py -b igb_uio 0000:af:00.0

2. create two VFs from PF::

    echo 2 > /sys/bus/pci/devices/0000\:af\:00.0/max_vfs

3. bind two VFs to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:af:02.0 0000:af:02.1

4. start a testpmd with create 2 VFs representor ports as control plane named testpmd-pf::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --lcores 1,2 -n 4 -a af:00.0,representor=0-1 --socket-mem 1024,1024 \
            --proc-type auto --file-prefix testpmd-pf -- -i --port-topology=chained

5. start two testpmd as dataplane named testpmd-vf0/testpmd-vf1(case 3 run later)::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --lcores 3,4 -n 4 -a af:02.0 --socket-mem 1024,1024 --proc-type auto --file-prefix testpmd-vf0 -- -i
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --lcores 5,6 -n 4 -a af:02.1 --socket-mem 1024,1024 --proc-type auto --file-prefix testpmd-vf1 -- -i

Note: Every case needs to restart testpmd.

Test Cases
==========

1. Test Case 1: VF Stats show and clear [ixgbe not support]
-----------------------------------------------------------
Description: use control testpmd to get and clear dataplane testpmd ports Stats.

1. prepare 3 testpmd to receive packets::

    PF  testpmd> set promisc 0 off
    PF  testpmd> start
    VF0 testpmd> set promisc 0 off
    VF0 testpmd> start
    VF1 testpmd> set promisc 0 off
    VF1 testpmd> start

2. send 30 packets by scapy as below::

    scapy> pkt1=Ether(src=src_mac, dst=pf_mac)/IP()
    scapy> pkt2=Ether(src=src_mac, dst=vf0_mac)/IP()
    scapy> pkt3=Ether(src=src_mac, dst=vf1_mac)/IP()
    scapy> pkts=[pkt1, pkt2, pkt3]*10
    scapy> sendp(pkts, iface="ens785f0")

3. check port stats in control testpmd, it will show 1 PF and 2 VF stats::

    PF testpmd> show port stats all

  expected result:
  VF0 and VF1 will show receive 10 packets separately in control testmpd.

4. clear port stats in control testpmd::

    PF testpmd> clear vf stats 0 0
    PF testpmd> clear vf stats 0 1
    PF testpmd> clear port stats all
    PF testpmd> show port stats all

  expected result:
  all the testpmd's port stats should be cleared

Note: PF statistics superimpose the number of VFs, and the independent command
      'clear vf stats <vf-port-id>' to clear this part of the data.

2. Test Case 2: VF Promiscous enable/disable
--------------------------------------------
Description: use control testpmd to enable/disable dataplane testpmd ports promiscous mode.

1. prepare 3 testpmd to receive packets, turn on VF0 promisc mode in control testpmd::

    PF  testpmd> set promisc 0 off
    PF  testpmd> start
    VF0 testpmd> set promisc 0 off
    VF0 testpmd> start
    VF1 testpmd> set promisc 0 off
    VF1 testpmd> start
    PF  testpmd> set promisc 1 on

2. send 40 packets by scapy as below::

    scapy> pkt1=Ether(src=src_mac, dst=pf_mac)/IP()
    scapy> pkt2=Ether(src=src_mac, dst=vf0_mac)/IP()
    scapy> pkt3=Ether(src=src_mac, dst=vf1_mac)/IP()
    scapy> pkt4=Ether(src=src_mac, dst=unicast_mac)/IP()
    scapy> pkts=[pkt1, pkt2, pkt3, pkt4]*10
    scapy> sendp(pkts, iface="ens785f0")

3. check port stats in DUT::

    PF testpmd> show port stats all

  expected result:
  VF0 should receive 20 packets(10 vf0_mac and 10 unicast_mac) and VF1 show receive 10
  packets in representor ports of PF.

3. Test Case 3: set VF MAC address
----------------------------------
Description: use control testpmd to set vf mac address

1. Run PF testpmd with PF first, set VF0 and VF1 mac address use representor ports::

    PF testpmd> mac_addr set 1 aa:11:22:33:44:55
    PF testpmd> mac_addr set 2 aa:22:33:44:55:66
    PF testpmd> set promisc 0 off
    PF testpmd> start

2. Run VFs testpmd, and turn off promisc mode::

    VF0 testpmd> set promisc 0 off
    VF0 testpmd> start
    VF1 testpmd> set promisc 0 off
    VF1 testpmd> start

3. use test case 2 step 2 to send packets from traffic generator

4. check port stats in DUT::

    PF testpmd> show port stats all

  expected result:
  VF0 should receive 10 packets and VF1 show receive 10 packets in representor ports of PF.

4. Test Case 4: set vlan filter
-------------------------------
Description: use control testpmd to set vlan

1. set promisc mode off in control testpmd, turn on vlan filter, add vlan filter in each VF::

    PF testpmd> set promisc 1 off
    PF testpmd> vlan set filter on 1
    PF testpmd> rx_vlan add 3 1
    PF testpmd> set promisc 2 off
    PF testpmd> vlan set filter on 2
    PF testpmd> rx_vlan add 4 2
    VF0 testpmd> start
    VF1 testpmd> start


2. use scapy to send packets as below::

    scapy> pkt1=Ether(src=src_mac, dst=vf0_mac)/Dot1Q(vlan=3)/IP()
    scapy> pkt2=Ether(src=src_mac, dst=vf1_mac)/Dot1Q(vlan=4)/IP()
    scapy> pkts=[pkt1, pkt2]*10
    scapy> sendp(pkts, iface="ens785f0")

3. check port stats in 2 VF testpmd:
    expected result:
    2 VF testpmds should receive 10 packets separately.
