.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019-2020 Intel Corporation

============================
ICE DCF Lifecycle Test Suite
============================

Description
===========

The DCF is a device configuration function (DCF - driver) bound to
one of the device's VFs which can act as a sole controlling entity
to exercise advance functionality (such as switch, ACL) for rest of
the VNFs (virtual network functions) under a DPDK based NFV deployment.

The DCF can act as a special VF talking to the kernel PF over the same
virtchannel mailbox to configure the underlying device (port) for the VFs.

The test suite covers the lifecycle of DCF context in Kernel PF, such as
launch, and exit, switch rules handling, resetting, and exception exit.


Configuration
=============

NIC: 2x25G or 2x100G, several TC need breakout mode.
NIC should have 2 PF ports at least, and connect to tester's ports.

Topology

  +-------+       +--------+
  |       |       |        |
  |     p1|<----->|        |
  |  DUT  |       | Tester |
  |     p2|<----->|        |
  |       |       |        |
  +-------+       +--------+


Device naming convention and mapping in this test suite
(You should change these names by your setup)

  +-------------+--------------+------------------+
  | Device Name |   PCI addr   | Kernel Interface |
  +=============+==============+==================+
  |     P1      | 0000:18:00.0 |    enp24s0f0     |
  +-------------+--------------+------------------+
  |     VF0     | 0000:18:01.0 |     enp24s1      |
  +-------------+--------------+------------------+
  |     P2      | 0000:18:00.1 |    enp24s0f1     |
  +-------------+--------------+------------------+


Support DCF mode
================


TC01: DCF on 1 trust VF on 1 PF
-------------------------------

Generate 1 trust VF on 1 PF, and request 1 DCF on the trust VF.
PF should grant DCF mode to it.

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf --file-prefix=vf -- -i

Expected: VF get DCF mode. There are outputs in testpmd launching ::

    EAL: Probe PCI driver: net_ice_dcf (8086:1889) device: 0000:18:01.0 (socket 0)


TC02: DCF on 2 PFs, 1 trust VF on each PF
-----------------------------------------

Generate 2 trust VFs on 2 PFs, each trust VF request DCF.
Each PF should grant DCF mode to them.

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    echo 4 > /sys/bus/pci/devices/0000:18:00.1/sriov_numvfs

Set a VF as trust on each PF ::

    ip link set enp24s0f0 vf 0 trust on
    ip link set enp24s0f1 vf 0 trust on

Launch dpdk on the VF on each PF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:11.0
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf --file-prefix=dcf1 -- -i
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 11-15 -n 4 -a 18:11.0,cap=dcf --file-prefix=dcf2 -- -i

Expected: VF get DCF mode. There are outputs in each testpmd launching ::

    EAL: Probe PCI driver: net_ice_dcf (8086:1889) device: 0000:18:01.0 (socket 0)

    EAL: Probe PCI driver: net_ice_dcf (8086:1889) device: 0000:18:11.0 (socket 0)


TC03: Check only VF zero can get DCF mode
-----------------------------------------

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 1 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.1
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.1,cap=dcf --file-prefix=vf -- -i

Expected: VF can NOT get DCF mode. testpmd should provide a friendly output ::

    ice_dcf_get_vf_resource(): Failed to get response of OP_GET_VF_RESOURCE
    ice_dcf_init_hw(): Failed to get VF resource
    ice_dcf_dev_init(): Failed to init DCF hardware

Error message in dmesg ::

    ice 0000:18:00.0: VF 1 requested DCF capability, but only VF 0 is allowed to request DCF capability


TC04: Check only trusted VF can get DCF mode
--------------------------------------------

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust off

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf --file-prefix=vf -- -i

Expected: VF can NOT get DCF mode. testpmd should provide a friendly output ::

    ice_dcf_get_vf_resource(): Failed to get response of OP_GET_VF_RESOURCE
    ice_dcf_init_hw(): Failed to get VF resource
    ice_dcf_dev_init(): Failed to init DCF hardware

Error message in dmesg ::

    ice 0000:18:00.0: VF needs to be trusted to configure DCF capability


TC05: DCF graceful exit
-----------------------

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf,representor=vf[1] --file-prefix=dcf -- -i

Launch another testpmd on the VF1, and start mac forward ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 11-14 -n 4 -a 18:01.1 --file-prefix=vf -- -i
    set verbose 1
    set fwd mac
    start

Set switch rule to VF1 `0000:18:01.1` from DCF ::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions represented_port ethdev_port_id 1 / end

Send a scapy packet to VF1 ::

    p = Ether(dst='xx:xx:xx:xx:xx:xx')/IP(src='192.168.0.2', dst='192.168.0.3')/Raw(64*'x')
    sendp(p, iface='testeri0', count=1)

Check VF1 received the packet. Stats shows 1 packet received and forwarded. ::

    show port stats all

Exit the DCF in DCF testpmd ::

    quit

Send scapy packet again. Check VF1 can't receive the packet ::

    show port stats all

Expect: VF1 can't receive the packet


Handling of switch filters added by DCF
=======================================

TC11: Turn trust mode off, when DCF launched
--------------------------------------------

If turn trust mode off, when DCF launched. The DCF rules should be removed.

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf,representor=vf[1] --file-prefix=dcf -- -i

Launch another testpmd on the VF1, and start mac forward ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 11-14 -n 4 -a 18:01.1 --file-prefix=vf -- -i
    set verbose 1
    set fwd mac
    start

Set switch rule to VF1 0000:18:01.1 from DCF ::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions represented_port ethdev_port_id 1 / end

Send a scapy packet to VF1 ::

    p = Ether(dst='xx:xx:xx:xx:xx:xx')/IP(src='192.168.0.2', dst='192.168.0.3')/Raw(64*'x')
    sendp(p, iface='testeri0', count=1)

Check VF1 received the packet. Stats shows 1 packet received and forwarded ::

    show port stats all

Turn off DCF trust mode ::

    ip link set enp24s0f0 vf 0 trust off

Send scapy packet again. Check VF1 can't receive the packet ::

    show port stats all

Expect: VF1 can't receive the packet


TC12: Kill DCF process
----------------------

If kill DCF process, when DCF launched. The DCF rules should be removed.

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf,representor=vf[1] --file-prefix=dcf -- -i

Launch another testpmd on the VF1, and start mac forward ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 11-14 -n 4 -a 18:01.1 --file-prefix=vf -- -i
    set verbose 1
    set fwd mac
    start

Set switch rule to VF1 0000:18:01.1 from DCF ::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions represented_port ethdev_port_id 1 / end

Send a scapy packet to VF1 ::

    p = Ether(dst='xx:xx:xx:xx:xx:xx')/IP(src='192.168.0.2', dst='192.168.0.3')/Raw(64*'x')
    sendp(p, iface='testeri0', count=1)

Check VF1 received the packet. Stats shows 1 packet received and forwarded ::

    show port stats all

Kill DCF process ::

    ps -ef |grep testpmd #Check the process id
    kill -9 <pid>

Send scapy packet again. DCF flow rule is still valid, check VF1 can receive the packet ::

    show port stats all

Expect: VF1 can receive the packet


TC13: Launch 2nd DCF process on the same VF
-------------------------------------------

Launch 2nd DCF process on the same VF, PF shall reject the request.
DPDK does not support to open 2nd DCF PMD driver on same VF.

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf --file-prefix=dcf -- -i

Launch another testpmd on the DCF ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 11-14 -n 4 -a 18:01.0,cap=dcf --file-prefix=dcf2 -- -i

Expect: the second testpmd can't be launched


TC14: DCF enabled, one of VF reset
----------------------------------

If DCF enabled, one of VF reset. DCF shall clean up all the rules of this VF.

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf,representor=vf[1-2] --file-prefix=dcf -- -i

Launch another testpmd on the VF1 and VF2, and start mac forward ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 11-14 -n 4 -a 18:01.1 --file-prefix=vf1 -- -i
    set verbose 1
    set fwd mac
    start

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 15-16 -n 4 -a 18:01.2 --file-prefix=vf2 -- -i
    set verbose 1
    set fwd mac
    start

Set switch rule to VF1 0000:18:01.1 from DCF ::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions represented_port ethdev_port_id 1 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.4 dst is 192.168.0.5 / end actions represented_port ethdev_port_id 1 / end

Send a scapy packet to VF1 ::

    p = Ether(dst='xx:xx:xx:xx:xx:xx')/IP(src='192.168.0.2', dst='192.168.0.3')/Raw(64*'x')
    sendp(p, iface='testeri0', count=1)

Send a scapy packet to VF2 ::

    p = Ether(dst='xx:xx:xx:xx:xx:xx')/IP(src='192.168.0.4', dst='192.168.0.5')/Raw(64*'x')
    sendp(p, iface='testeri0', count=1)

Check VF1 received the packet. Stats shows 1 packet received and forwarded ::

    show port stats all

Reset VF1 by set mac addr, to trigger VF reset ::

    ip link set enp24s0f0 vf 1 mac 00:01:02:03:04:05

Reset port in testpmd::

    stop
    port stop all
    port reset all
    port start all
    start

Send scapy packet again. Check VF1 can receive the packet ::

    show port stats all

Expect: Send packet to VF1 and VF2. VF1 can receive the packet, VF2 can receive the packet.


TC15: DCF enabled, PF reset - PFR
---------------------------------

If DCF enabled, PF reset - PFR. All DCF the rules should be clean up.

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1 18:01.2
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf,representor=vf[1-2] --file-prefix=dcf -- -i

Launch another testpmd on the VF1 and VF2, and start mac forward ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 11-14 -n 4 -a 18:01.1 -a 18:01.2 --file-prefix=vf -- -i
    set verbose 1
    set fwd mac
    start

Set switch rule to VF1 0000:18:01.1 and VF2 0000:18:01.2 from DCF ::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions represented_port ethdev_port_id 1 / end

Send a scapy packet to VF1 and VF2 ::

    p1 = Ether(dst='xx:xx:xx:xx:xx:xx')/IP(src='192.168.0.2', dst='192.168.0.3')/Raw(64*'x')
    sendp(p1, iface='testeri0', count=1)

Check if VF1 and VF2 received the packet.
Stats shows 1 packet received and forwarded on each VF ::

    show port stats all

Reset PF by lanconf command::

    lanconf /zeroinit
    <Choose 18:00.0 device> and Enter. See the "Initialize Options Menu"
    Press Esc, See "LANConf Menu"
    Select "SV Menu" and then select "Reset Menu"
    Select "PF Reset" to trigger PF reset event

Send scapy packet again. Check VF1 can't receive the packet::

    show port stats all

Expect: VF1 can't receive the packet


TC16: DCF enabled, PF reset - CORER. All the rules should be clean up
---------------------------------------------------------------------

Same to TC15, just reset command is different at last step::

    Select "Core Reset" to trigger Core reset event


TC17: DCF enabled, PF reset - GLOBR. All the rules should be clean up
---------------------------------------------------------------------

Same to TC15, just reset command is different at last step::

    Select "Global Reset" to trigger Global reset event


TC18: DCF enabled, PF reset - ENPR. All the rules should be clean up
--------------------------------------------------------------------

Same to TC15, just reset command is different at last step::

    Select "EMP Reset" to trigger EMP reset event


ADQ and DCF mode shall be mutually exclusive
============================================

TC19: When ADQ set on PF, PF should reject the DCF mode
-------------------------------------------------------

When ADQ set on PF, PF should reject the DCF mode. Remove the ADQ setting, PF shall accept DCF mode.

Host kernel version is required 4.19+, and MACVLAN offload should be set off

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Set ADQ on PF ::

    modprobe sch_mqprio
    modprobe act_mirred
    modprobe cls_flower

    ethtool -K enp24s0f0 hw-tc-offload on
    tc qdisc add dev enp24s0f0 ingress
    tc qdisc show dev enp24s0f0
    tc qdisc add dev enp24s0f0 root mqprio num_tc 4 map 0 0 0 0 1 1 1 1 2 2 2 2 3 3 3 3 queues 4@0 4@4 8@8 8@16 hw 1 mode channel
    tc filter add dev enp24s0f0 protocol ip parent ffff: prio 1 flower dst_ip 192.168.1.10 ip_proto tcp action gact pass
    tc filter show dev enp24s0f0 parent ffff:

Try to launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf --file-prefix=dcf -- -i

Expect: testpmd can't be launched. PF should reject DCF mode.

Remove ADQ on PF ::

    tc filter del dev enp24s0f0 parent ffff: pref 1 protocol ip
    tc filter show dev enp24s0f0 parent ffff:
    tc qdisc del dev enp24s0f0 root mqprio
    tc qdisc del dev enp24s0f0 ingress
    tc qdisc show dev enp24s0f0
    ethtool -K enp24s0f0 hw-tc-offload off

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf --file-prefix=dcf -- -i

Expect: testpmd can launch successfully. DCF mode can be grant ::

    EAL: Probe PCI driver: net_ice_dcf (8086:1889) device: 0000:18:01.0 (socket 0)


TC20: When DCF mode enabled, ADQ setting on PF shall fail
---------------------------------------------------------

When DCF mode enabled, ADQ setting on PF shall fail.
Exit DCF mode, ADQ setting on PF shall be successful.

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf --file-prefix=dcf -- -i

Set ADQ on PF ::

    ethtool -K enp24s0f0 hw-tc-offload on
    tc qdisc add dev enp24s0f0 ingress
    tc qdisc show dev enp24s0f0
    tc qdisc add dev enp24s0f0 root mqprio num_tc 4 map 0 0 0 0 1 1 1 1 2 2 2 2 3 3 3 3 queues 4@0 4@4 8@8 8@16 hw 1 mode channel
    tc filter add dev enp24s0f0 protocol ip parent ffff: prio 1 flower dst_ip 192.168.1.10 ip_proto tcp action gact pass
    tc filter show dev enp24s0f0 parent ffff:

Expect: ADQ command can't be executed successfully

Exit testpmd ::

    quit

Set ADQ on PF again

Expect: ADQ can be set.


TC21: DCF and ADQ can be enabled on different PF
------------------------------------------------

Configure the DCF on 1 PF port and configure ADQ on the other PF port.
Then turn off DCF, other PF's should not be impact.

Generate 4 VFs on PF1 and 4VFs on PF2 ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    echo 4 > /sys/bus/pci/devices/0000:18:00.1/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Launch dpdk on the VF0 on PF1, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-10 -n 4 -a 18:01.0,cap=dcf --file-prefix=dcf -- -i

Set ADQ on PF2 ::

    modprobe sch_mqprio
    modprobe act_mirred
    modprobe cls_flower

    ethtool -K enp24s0f1 hw-tc-offload on
    tc qdisc add dev enp24s0f1 ingress
    tc qdisc show dev enp24s0f1
    tc qdisc add dev enp24s0f1 root mqprio num_tc 4 map 0 0 0 0 1 1 1 1 2 2 2 2 3 3 3 3 queues 4@0 4@4 8@8 8@16 hw 1 mode channel
    tc filter add dev enp24s0f1 protocol ip parent ffff: prio 1 flower dst_ip 192.168.1.10 ip_proto tcp action gact pass
    tc filter show dev enp24s0f1 parent ffff:

Expect: ADQ can be set on PF2.


L2 Forwarding (MAC-VLAN feature) and DCF mode shall be mutually exclusive
=========================================================================

TC22: When L2 forwarding set, PF should reject the DCF mode
-----------------------------------------------------------

When L2 forwarding set, PF should reject the DCF mode.
Remove L2 forwarding set, PF shall accept the DCF mode.

Similar to ADQ test TC19

Just change the ADQ commands to MAC-VLAN ::

    ethtool -K enp24s0f0 l2-fwd-offload on
    ip link add link macvlan0 link enp24s0f0 type macvlan
    ifconfig macvlan0 192.168.1.111
    ipconfig macvlan0 up

Remove MAC-VLAN commands ::

   ip link del macvlan0
   ethtool -K enp24s0f0 l2-fwd-offload off


TC23: When DCF mode enabled, PF can't set L2 forwarding
-------------------------------------------------------

When DCF mode enabled, PF can't set L2 forwarding.
Exit DCF mode, PF can set L2 forwarding.

Similar to ADQ test TC20

Just change the ADQ commands to MAC-VLAN ::

    ethtool -K enp24s0f0 l2-fwd-offload on
    ip link add link macvlan0 link enp24s0f0 type macvlan
    ifconfig macvlan0 192.168.1.111
    ipconfig macvlan0 up

Remove MAC-VLAN commands ::

    ip link del macvlan0
    ethtool -K enp24s0f0 l2-fwd-offload off


TC24: DCF and L2 forwarding can be enabled on different PF
----------------------------------------------------------

Configure the DCF on 1 PF port and configure MAC-VLAN on the other PF port.
Then turn off DCF, other PF's MAC-VLAN filter should not be impact.

Similar to ADQ test TC21

Just change the ADQ commands to MAC-VLAN ::

    ethtool -K enp24s0f1 l2-fwd-offload on
    ip link add link macvlan0 link enp24s0f1 type macvlan
    ifconfig macvlan0 192.168.1.111
    ipconfig macvlan0 up

Remove MAC-VLAN commands ::

    ip link del macvlan0
    ethtool -K enp24s0f1 l2-fwd-offload off


Handling of ACL filters added by DCF
====================================
1. PF base driver shall track all the ACL filters being added by DCF.
   Additionally it shall also track the related profiles needed for
   the ACL filters being added.
2. PF base driver shall ensure cleanup of these ACL filters and profiles
   during resets and exception cases.

pre-steps:

1. Generate 2 VFs on PF0::

    echo 2 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

    0000:18:01.0 'Ethernet Adaptive Virtual Function 1889' if=enp24s1 drv=iavf unused=vfio-pci
    0000:18:01.1 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f1 drv=iavf unused=vfio-pci

2. Set VF0 as trust::

    ip link set enp24s0f0 vf 0 trust on

3. Bind VFs to dpdk driver::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0 0000:18:01.1

4. Launch dpdk on VF0, and VF0 request DCF mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf --file-prefix=vf0 -- -i
    testpmd> set fwd mac
    testpmd> set verbose 1
    testpmd> start
    testpmd> show port info all

   check the VF0 driver is net_ice_dcf.

5. Launch dpdk on VF1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf0 -n 4 -a 18:01.1 --file-prefix=vf1 -- -i
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start
    testpmd> show port info all

   check the VF1 driver is net_iavf.
   the mac address is 5E:8E:8B:4D:89:05

TC25: Turn trust mode off, when DCF launched
--------------------------------------------
If turn trust mode off, when DCF launched. The DCF rules should be removed.

1. Create an ACL rule::

    flow create 0 priority 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end

   check the rule created successfully.

2. send packet with dst mac of VF1::

    sendp([Ether(src="00:11:22:33:44:55", dst="5E:8E:8B:4D:89:05")/IP()/TCP(sport=8012)/Raw(load='X'*30)], iface="testeri0")

   check the packet is dropped by VF1::

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 0              RX-dropped: 1             RX-total: 1
    TX-packets: 0              TX-dropped: 0             TX-total: 0
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 0              RX-dropped: 1             RX-total: 1
    TX-packets: 0              TX-dropped: 0             TX-total: 0
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

3. turn VF0 trust mode off, while DCF launched::

    ip link set enp24s0f0 vf 0 trust off

4. check the DCF ACL rule can be listed.
   send the packet again, check the packet not dropped by VF1.
   so the rule can't take effect any more.

5. turn VF0 trust mode on, then re-launch dpdk on VF0, which requests DCF mode again.
   check there is no ACL rule listed.
   repeat step 1-2, check the packet is dropped by VF1.

TC26: Kill DCF process
----------------------
If kill DCF process, when DCF launched. The DCF rules should be removed.

1. Create an ACL rule::

    flow create 0 priority 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end

   check the rule created successfully.

2. send packet with dst mac of VF1::

    sendp([Ether(src="00:11:22:33:44:55", dst="5E:8E:8B:4D:89:05")/IP()/TCP(sport=8012)/Raw(load='X'*30)], iface="testeri0")

   check the packet is dropped by VF1.

3. kill DCF process ::

    ps -ef |grep testpmd #Check the process id
    kill -9 <pid>

4. send the packet again, check the packet not dropped by VF1.
   so the rule can't take effect any more.

5. re-launch dpdk on VF0, which requests DCF mode again.
   check there is no ACL rule listed.
   send the packet again, check the packet not dropped by VF1.

6. repeat step 1-2, check the packet is dropped by VF1.

TC27: Allow AVF request
-----------------------
This is a scenario when the DCF user process was killed and a new AVF is being installed.
Kill DCF process, then fail to launch avf on the previous DCF VF.

1. Create an ACL rule::

    flow create 0 priority 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end

   check the rule created successfully.

2. send packet with dst mac of VF1::

    sendp([Ether(src="00:11:22:33:44:55", dst="5E:8E:8B:4D:89:05")/IP()/TCP(sport=8012)/Raw(load='X'*30)], iface="testeri0")

   check the packet is dropped by VF1.

3. kill DCF process ::

    ps -ef |grep testpmd #Check the process id
    kill -9 <pid>

4. send the packet again, check the packet not dropped by VF1.
   so the rule can't take effect any more.

5. re-launch dpdk on VF0, which requests AVF mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0 --file-prefix=vf0 -- -i

   report::

    iavf_get_vf_resource(): Failed to execute command of OP_GET_VF_RESOURCE
    iavf_init_vf(): iavf_get_vf_config failed
    iavf_dev_init(): Init vf failed

   then quit the process, re-launch AVF on VF0 again, launch successfully.
   send the packet again, check the packet not dropped by VF1.

TC28: DCF graceful exit
-----------------------
1. Create an ACL rule::

    flow create 0 priority 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end

   check the rule created successfully.

2. send packet with dst mac of VF1::

    sendp([Ether(src="00:11:22:33:44:55", dst="5E:8E:8B:4D:89:05")/IP()/TCP(sport=8012)/Raw(load='X'*30)], iface="testeri0")

   check the packet is dropped by VF1.

3. Exit the DCF in DCF testpmd ::

    testpmd> quit

4. send the packet again, check the packet not dropped by VF1.
   the ACL rule is removed.

TC29: DCF enabled, AVF VF reset
-------------------------------
1. Create an ACL rule::

    flow create 0 priority 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end

   check the rule created successfully.

2. send packet with dst mac of VF1::

    sendp([Ether(src="00:11:22:33:44:55", dst="5E:8E:8B:4D:89:05")/IP()/TCP(sport=8012)/Raw(load='X'*30)], iface="testeri0")

   check the packet is dropped by VF1.

3. reset VF1 in testpmd::

    stop
    port stop 0
    port reset 0
    port start 0
    start

4. send the packet again, check the packet still be dropped by VF1.
   so the rule still take effect.

5. Reset VF1 by setting mac addr::

    ip link set enp24s0f0 vf 1 mac 00:01:02:03:04:05

   Reset port in testpmd::

    stop
    port stop all
    port reset all
    port start all
    start

6. send the packet with changed dst mac address "00:01:02:03:04:05",
   check the packet still be dropped by VF1.
   so the rule still take effect.

TC30: DCF enabled, DCF VF reset
-------------------------------
1. Create an ACL rule::

    flow create 0 priority 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end

   check the rule created successfully.

2. send packet with dst mac of VF1::

    sendp([Ether(src="00:11:22:33:44:55", dst="5E:8E:8B:4D:89:05")/IP()/TCP(sport=8012)/Raw(load='X'*30)], iface="testeri0")

   check the packet is dropped by VF1.

3. reset VF0 in testpmd::

    stop
    port stop 0
    port reset 0
    port start 0
    start

4. send the packet with new mac address of VF1 again, check the packet not dropped by VF1.
   the rule is removed.

DCF mode and any ACL filters (not added by DCF) shall be mutually exclusive
===========================================================================
PF base driver shall ensure ACL filters being added by host based
configuration tools such as tc flower or tc u32 (but not limited to)
are mutually exclusive to DCF mode.

TC31: add ACL rule by kernel, reject request for DCF functionality
------------------------------------------------------------------
1. create 2 VFs on PF0, set trust mode to VF0::

    echo 2 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    ip link set enp24s0f0 vf 0 trust on

2. create an ACL rule on PF0 by kernel command::

    # ethtool -N enp24s0f0 flow-type tcp4 src-ip 192.168.10.0 m 0.255.255.255 dst-port 8000 m 0x00ff action -1
    Added rule with ID 15871

3. launch testpmd on VF0 requesting for DCF funtionality::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc -n 4 -a 18:01.0,cap=dcf --log-level=ice,7 -- -i --port-topology=loop

   report error::

    ice_dcf_init_parent_hw(): firmware 5.1.5 api 1.7.3 build 0x7a25e184
    ice_load_pkg_type(): Active package is: 1.3.20.0, ICE COMMS Package
    ice_dcf_send_aq_cmd(): No response (201 times) or return failure (desc: -63 / buff: -63)
    ice_flow_init(): Failed to initialize engine 4
    ice_dcf_init_parent_adapter(): Failed to initialize flow
    ice_dcf_dev_init(): Failed to init DCF parent adapter

   get dmesg::

    ice 0000:18:00.0: Grant request for DCF functionality to VF0
    ice 0000:18:00.0: Failed to grant ACL capability to VF0 as ACL rules already exist

4. delete the kernel ACL rule::

    ethtool -N enp24s0f0 delete 15871

5. relaunch testpmd on VF0 requesting for DCF funtionality with same command.
   accept request for DCF functionality.
   show the port info::

    Driver name: net_ice_dcf

   there is not Failed infomation in dmesg.

TC32: add ACL rule by kernel, accept request for DCF functionality of another PF
--------------------------------------------------------------------------------
1. create 2 VFs on PF0, set trust mode to VF0::

    echo 2 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    ip link set enp24s0f0 vf 0 trust on

2. create an ACL rule on PF1 by kernel command::

    # ethtool -N enp24s0f1 flow-type tcp4 src-ip 192.168.10.0 m 0.255.255.255 dst-port 8000 m 0x00ff action -1
    Added rule with ID 15871

3. launch testpmd on VF0 of PF0 requesting for DCF funtionality successfully::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc -n 4 -a 18:01.0,cap=dcf --log-level=ice,7 -- -i --port-topology=loop

   show the port info::

    Driver name: net_ice_dcf

   there is not Failed infomation in dmesg.

TC33: ACL DCF mode is active, add ACL filters by way of host based configuration is rejected
--------------------------------------------------------------------------------------------
1. create 2 VFs on PF0, set trust mode to VF0::

    echo 2 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    ip link set enp24s0f0 vf 0 trust on

2. launch testpmd on VF0 of PF0 requesting for DCF funtionality successfully::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc -n 4 -a 18:01.0,cap=dcf --log-level=ice,7 -- -i --port-topology=loop

   show the port info::

    Driver name: net_ice_dcf

3. failed to add ACL filter by host kernel command::

    ~# ethtool -N enp24s0f0 flow-type tcp4 src-ip 192.168.10.0 m 0.255.255.255 dst-port 8000 m 0x00ff action -1
    rmgr: Cannot insert RX class rule: No such file or directory

4. exit ACL DCF mode::

    testpmd> quit

5. add ACL filters by way of host based configuration successfully::

    # ethtool -N enp24s0f0 flow-type tcp4 src-ip 192.168.10.0 m 0.255.255.255 dst-port 8000 m 0x00ff action -1
    Added rule with ID 15871

TC34: ACL DCF mode is active, add ACL filters by way of host based configuration on another PF successfully
-----------------------------------------------------------------------------------------------------------
1. create 2 VFs on PF0, set trust mode to VF0::

    echo 2 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    ip link set enp24s0f0 vf 0 trust on

2. launch testpmd on VF0 of PF0 requesting for DCF funtionality successfully::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc -n 4 -a 18:01.0,cap=dcf --log-level=ice,7 -- -i --port-topology=loop

   show the port info::

    Driver name: net_ice_dcf

3. add ACL filter by host kernel command on PF1 successfully::

    # ethtool -N enp24s0f1 flow-type tcp4 src-ip 192.168.10.0 m 0.255.255.255 dst-port 8000 m 0x00ff action -1
    Added rule with ID 15871

===============================
ICE DCF enable device reset API
===============================

Description
===========
DCF PMD need to support rte_eth_dev_reset.The reason is that when a DCF instance be killed, all the flow rules still exist in hardware. when DCF gets to reconnect, 
It has already lost the flow context, and if the application wants to create new rules, they may fail because FW reports that the rules already exist.The current 
workaround assumes that the user can turn off / turn on VF trust mode, so kernel PF will reset DCF by removing all old rules.The rte_eth_dev_reset API provides 
a more elegant way for the application to reset DCF through the command "port reset all" when reconnecting.

Prerequisites
=============

Hardware
--------
Supportted NICs: Intel® Ethernet Network Adapter E810-XXVDA4/Intel® Ethernet Network Adapter E810-CQDA2

Software
--------
dpdk: http://dpdk.org/git/dpdk
scapy: http://www.secdev.org/projects/scapy/

General Set Up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110

2. Get the pci device id and interface of DUT and tester. 
   For example, 0000:3b:00.0 and 0000:af:00.0 is pci device id,
   ens785f0 and ens260f0 is interface::

    <dpdk dir># ./usertools/dpdk-devbind.py -s

    0000:3b:00.0 'Ethernet Controller E810-C for SFP 1593' if=ens785f0 drv=ice unused=vfio-pci
    0000:af:00.0 'Ethernet Controller XXV710 for 25GbE SFP28 158b' if=ens260f0 drv=i40e unused=vfio-pci

3. Generate 4 VFs on PF0::

    # echo 4 > /sys/bus/pci/devices/0000:3b:00.0/sriov_numvfs

4. Get VF pci device id and interface of DUT.

    # ./usertools/dpdk-devbind.py -s

     0000:3b:01.0 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v0 drv=iavf unused=vfio-pci
     0000:3b:01.1 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v1 drv=iavf unused=vfio-pci

5. Set VF0 as trust::

    # ip link set ens785f0 vf 0 trust on

6. Bind the DUT port to dpdk::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
    
Test case
=========

Common Steps
------------
The common steps launch two testpmds and kill DCF process, then relaunch two testpmds.

1. Launch the userland ``testpmd`` application on DUT as follows::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a <DUT port pci device id> -- -i 

..note:: 

    For <EAL options>, you can use "-c 0x6 -n 4", you can also refer to testpmd doc for other setings.
    For <DUT port pci device id>, you can use "0000:3b:01.0,cap=dcf,representor=vf[1] --file-prefix=dcf" for this test plan.
  
2. Launch another ``testpmd`` application on the VF1 of DUT as follows::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a <DUT port pci device id> -- -i 

..note:: 

    For <EAL options>, you can use "-c 0x18 -n 4", you can also refer to testpmd doc for other setings.
    For this test plan, you can use "0000:3b:01.1 --file-prefix=vf" for this test plan. 

3. Set verbose in VF testpmd::
    
     testpmd> set verbose 1
    
4. Set fwd engine and start in VF testpmd::

     testpmd> set fwd mac
     testpmd> start

5. Validate a switch rule to VF1 in DCF testpmd::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

6. Create a switch rule to VF1 in DCF testpmd and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

7. Send a matched packet in scapy to VF1, check the VF1 of DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

the VF1 of DUT::

     testpmd> port 0/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

All the packets in this test plan use below settings:
dst src: 00:11:22:33:44:55
dst mac: C6:44:32:0A:EC:E1
ipv4 src: 192.168.0.2
ipv4 dst: 192.168.0.3

Test Case 1: two_testpmd_dcf_reset_port
---------------------------------------
The test case resets DCF by killing DCF and resetting the port, and DCF should clean up all old rules.

Test Steps
~~~~~~~~~~
1. Check the process ID and kill DCF process::

    # ps -ef |grep testpmd 
    # kill -9 #####

2. Relaunch the userland ``testpmd`` application on DUT as follows::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a <DUT port pci device id> -- -i 

..note:: 

    For <EAL options>, you can use "-c 0x6 -n 4", you can also refer to testpmd doc for other setings.
    For <DUT port pci device id>, you can use "0000:3b:01.0,cap=dcf,representor=vf[1] --file-prefix=dcf" for this test plan.

3. Send a matched packet in scapy to VF1, DCF flow rule is still valid and check the VF1 of DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

the VF1 of DUT::

     testpmd> port 0/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

4. Reset port in DCF testpmd::

    testpmd> stop
    testpmd> port stop all
    testpmd> port reset all
    testpmd> port start all
    testpmd> start
    testpmd> flow list 0

5. Validate a switch rule to VF1 in DCF testpmd::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

6. Create a switch rule to VF1 in DCF testpmd and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

7. Send a matched packet in scapy to VF1, and check the VF1 of DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

the VF1 of DUT::

     testpmd> port 0/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

Test Case 2: two_testpmd_dcf_reset_device
-----------------------------------------
The test case resets DCF by resetting the device, and DCF should clean up all old rules.

Test Steps
~~~~~~~~~~
1. Reset DCF device::

    # echo 1 > /sys/bus/pci/devices/0000:3b:01.0/reset

2. Reset port in DCF testpmd::
   
    testpmd> stop
    testpmd> port stop all
    testpmd> port reset all
    testpmd> port start all
    testpmd> start
    testpmd> flow list 0

3. Validate a switch rule to VF1 in DCF testpmd::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

4. Create a switch rule to VF1 in DCF testpmd and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

5. Send a matched packet in scapy to VF1, and check the VF1 of DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

the VF1 of DUT::

     testpmd> port 0/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

Test Case 3: two_testpmd_dcf_reset_port_detach
----------------------------------------------
The test case resets DCF by detaching the port, and DCF should clean up all old rules.

Test Steps
~~~~~~~~~~
1. Reset DCF device::

    # echo 1 > /sys/bus/pci/devices/0000:3b:01.0/reset

2. Detach and reset port in DCF testpmd::
    
    testpmd> stop 
    testpmd> port stop 0
    testpmd> port detach 0
    testpmd> port attach 3b:01.0,cap=dcf
    testpmd> port reset 0
    testpmd> port start 0
    testpmd> start
    testpmd> flow list 0

3. Validate a switch rule to VF1 in DCF testpmd::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

4. Create a switch rule to VF1 in DCF testpmd and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

5. Send a matched packet in scapy to VF1, and check the VF1 of DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

the VF1 of DUT::

     testpmd> port 0/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN    

Test Case 4: two_testpmd_dcf_reset_mtu
--------------------------------------
The test case resets DCF by resetting the mtu, and DCF should clean up all old rules.

Test Steps
~~~~~~~~~~
1. Modify the value of mtu::

    # ifconfig ens785f0 mtu 3000

2. Reset port in DCF testpmd::
   
    testpmd> stop
    testpmd> port stop all
    testpmd> port reset all
    testpmd> port start all
    testpmd> start
    testpmd> flow list 0
   
3. Validate a switch rule to VF1 in DCF testpmd::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

4. Create a switch rule to VF1 in DCF testpmd and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

5. Send a matched packet in scapy to VF1, and check the VF1 of DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

the VF1 of DUT::

     testpmd> port 0/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
  
Test Case 5: two_testpmd_dcf_reset_mac
--------------------------------------
The test case resets DCF by resetting mac addr, and DCF should clean up all old rules.

Test Steps
~~~~~~~~~~
1. Reset VF0 by set mac addr::

    # ip link set ens785f0 vf 0 mac 00:01:02:03:04:05

2. Reset port in DCF testpmd::
   
    testpmd> stop
    testpmd> port stop all
    testpmd> port reset all
    testpmd> port start all
    testpmd> start
    testpmd> flow list 0

3. Validate a switch rule to VF1 in DCF testpmd::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

4. Create a switch rule to VF1 in DCF testpmd and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

5. Send a matched packet in scapy to VF1, and check the VF1 of DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

the VF1 of DUT::

     testpmd> port 0/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

Common Steps
------------
The common steps launch one testpmd and kill DCF process, then relaunch one testpmd.

1. Launch the userland ``testpmd`` application on DUT as follows::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a <DUT port pci device id> -- -i 

..note:: 

    For <EAL options>, you can use "-c 0x6 -n 4", you can also refer to testpmd doc for other setings.
    For <DUT port pci device id>, you can use"-a 3b:01.0,cap=dcf,representor=vf[1] -a 3b:01.1 --file-prefix=dcf" for this test plan.

2. Set verbose::
    
     testpmd> set verbose 1
    
3. Set fwd engine and start::

     testpmd> set fwd mac
     testpmd> start

4. Validate a switch rule to VF1::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

5. Create a switch rule to VF1 and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

6. Send a matched packet in scapy to VF1, check DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

DUT::

    testpmd> port 1/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

Test Case 6: one_testpmd_dcf_reset_port
---------------------------------------
The test case resets DCF by killing DCF and resetting the port, and DCF should clean up all old rules.

Test Steps
~~~~~~~~~~
1. Check the process ID and kill DCF process::

    # ps -ef |grep testpmd 
    # kill -9 #####

2. Relaunch the userland ``testpmd`` application on DUT as follows::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a <DUT port pci device id> -- -i 

..note:: 

    For <EAL options>, you can use "-c 0x6 -n 4", you can also refer to testpmd doc for other setings.
    For <DUT port pci device id>, you can use"-a 3b:01.0,cap=dcf,representor=vf[1] -a 3b:01.1 --file-prefix=dcf" for this test plan.

3. Set verbose::
    
     testpmd> set verbose 1
    
4. Set fwd engine and start::

     testpmd> set fwd mac
     testpmd> start
     testpmd> flow list 0

5. Send a matched packet in scapy to VF1, DCF flow rule is cleared and check DUT can't receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

DUT::

    testpmd> 

6. Reset port in testpmd::
   
    testpmd> stop
    testpmd> port stop all
    testpmd> port reset all
    testpmd> port start all
    testpmd> start

7. Validate a switch rule to VF1::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

8. Create a switch rule to VF1 and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

9. Send a matched packet in scapy to VF1, and check DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

DUT::

    testpmd> port 1/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN    

Test Case 7: one_testpmd_dcf_reset_device
-----------------------------------------
The test case resets DCF by resetting the device, and DCF should clean up all old rules.

Test Steps
~~~~~~~~~~
1. Reset DCF device::

    # echo 1 > /sys/bus/pci/devices/0000:3b:01.0/reset

2. Reset port in testpmd::
   
    testpmd> stop
    testpmd> port stop all
    testpmd> port reset all
    testpmd> port start all
    testpmd> start
    testpmd> flow list 0

3. Validate a switch rule to VF1::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

4. Create a switch rule to VF1 and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

5. Send a matched packet in scapy to VF1, and check DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

DUT::

    testpmd> port 1/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

Test Case 8: one_testpmd_dcf_reset_port_detach
----------------------------------------------
The test case resets DCF by detaching the port, and DCF should clean up all old rules.

Test Steps
~~~~~~~~~~
1. Reset DCF device::

    # echo 1 > /sys/bus/pci/devices/0000:3b:01.0/reset

2. Detach and reset port in DCF testpmd::
    
    testpmd> stop 
    testpmd> port stop 0
    testpmd> port detach 0
    testpmd> port attach 3b:01.0,cap=dcf,representor=vf[1]
    testpmd> port reset 0
    testpmd> port start 0
    testpmd> start
    testpmd> flow list 0

3. Validate a switch rule to VF1::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

4. Create a switch rule to VF1 and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

5. Send a matched packet in scapy to VF1, and check DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

DUT::

    testpmd> port 1/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN    

Test Case 9: one_testpmd_dcf_reset_mtu
--------------------------------------
The test case resets DCF by resetting the mtu, and DCF should clean up all old rules.

Test Steps
~~~~~~~~~~
1. Modify the value of mtu::

    # ifconfig ens785f0 mtu 3000

2. Reset port in DCF testpmd::
   
    testpmd> stop
    testpmd> port stop all
    testpmd> port reset all
    testpmd> port start all
    testpmd> start
    testpmd> flow list 0    

3. Validate a switch rule to VF1::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

4. Create a switch rule to VF1 and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

5. Send a matched packet in scapy to VF1, and check DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

DUT::

    testpmd> port 1/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

Test Case 10: one_testpmd_dcf_reset_mac
---------------------------------------
The test case resets DCF by resetting mac addr, and DCF should clean up all old rules.

Test Steps
~~~~~~~~~~
1. Reset VF0 by set mac addr::

    # ip link set ens785f0 vf 0 mac 00:01:02:03:04:05

2. Reset port in DCF testpmd::
   
    testpmd> stop
    testpmd> port stop all
    testpmd> port reset all
    testpmd> port start all
    testpmd> start
    testpmd> flow list 0

3. Validate a switch rule to VF1::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule validated

4. Create a switch rule to VF1 and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id 1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0
   
   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH IPV4 => VF

5. Send a matched packet in scapy to VF1, and check DUT can receive the packet.

Tester::

    >>> sendp([Ether(src="<src mac>",dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*64)], iface="<tester interface>")

DUT::

    testpmd> port 1/queue 0: received 1 packets
  src=00:11:22:33:44:55 - dst=C6:44:32:0A:EC:E1 - type=0x0800 - length=98 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
  ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN


