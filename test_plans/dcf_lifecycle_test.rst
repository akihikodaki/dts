.. Copyright (c) <2019-2020>, Intel Corporation
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


============================
CVL DCF Lifecycle Test Suite
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
launch, and exit, switch rules handling, reseting, and exception exit.


Configuration
=============

NIC: 2x25G or 2x100G, serveral TC need breakout mode.
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
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=vf -- -i

Expected: VF get DCF mode. There are outputs in testpmd launching ::

    EAL: PCI device 0000:18:01.0 on NUMA socket 0
    EAL: probe driver: 8086:1889 net_ice_dcf


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
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf1 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 11-15 -n 4 -w 18:11.0,cap=dcf --file-prefix=dcf2 -- -i

Expected: VF get DCF mode. There are outputs in each testpmd launching ::

    EAL: PCI device 0000:18:01.0 on NUMA socket 0
    EAL: probe driver: 8086:1889 net_ice_dcf

    EAL: PCI device 0000:18:11.0 on NUMA socket 0
    EAL: probe driver: 8086:1889 net_ice_dcf


TC03: Check only VF zero can get DCF mode
-----------------------------------------

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 1 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.1
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.1,cap=dcf --file-prefix=vf -- -i

Expected: VF can NOT get DCF mode. testpmd should provide a friendly output ::

    ice_dcf_get_vf_resource(): Fail to get response of OP_GET_VF_RESOURCE
    ice_dcf_init_hw(): Failed to get VF resource
    ice_dcf_dev_init(): Failed to init DCF hardware

Error message in dmesg ::

    ice 0000:18:00.0: Only VF0 can request for DCF.
    ice 0000:18:00.0: VF 1 failed opcode 3, retval: -5


TC04: Check only trusted VF can get DCF mode
--------------------------------------------

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust off

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=vf -- -i

Expected: VF can NOT get DCF mode. testpmd should provide a friendly output ::

    ice_dcf_get_vf_resource(): Fail to get response of OP_GET_VF_RESOURCE
    ice_dcf_init_hw(): Failed to get VF resource
    ice_dcf_dev_init(): Failed to init DCF hardware

Error message in dmesg ::

    ice 0000:18:00.0: DCF needs to be trusted.
    ice 0000:18:00.0: VF 0 failed opcode 3, retval: -5


TC05: DCF graceful exit
-----------------------

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf -- -i

Launch another testpmd on the VF1, and start mac forward ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 11-14 -n 4 -w 18:01.1 --file-prefix=vf -- -i
    set verbose 1
    set fwd mac
    start

Set switch rule to VF1 `0000:18:01.1` from DCF ::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end

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
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf -- -i

Launch another testpmd on the VF1, and start mac forward ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 11-14 -n 4 -w 18:01.1 --file-prefix=vf -- -i
    set verbose 1
    set fwd macstart

Set switch rule to VF1 0000:18:01.1 from DCF ::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end

Send a scapy packet to VF1 ::

    p = Ether(dst='xx:xx:xx:xx:xx:xx')/IP(src='192.168.0.2', dst='192.168.0.3')/Raw(64*'x')
    sendp(p, iface='testeri0', count=1)

Check VF1 received the packet. Stats shows 1 packet received and forwarded. ::

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
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf -- -i

Launch another testpmd on the VF1, and start mac forward ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 11-14 -n 4 -w 18:01.1 --file-prefix=vf -- -i
    set verbose 1
    set fwd macstart

Set switch rule to VF1 0000:18:01.1 from DCF ::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end

Send a scapy packet to VF1 ::

    p = Ether(dst='xx:xx:xx:xx:xx:xx')/IP(src='192.168.0.2', dst='192.168.0.3')/Raw(64*'x')
    sendp(p, iface='testeri0', count=1)

Check VF1 received the packet. Stats shows 1 packet received and forwarded ::

    show port stats all

Kill DCF process ::

    ps -ef |grep testpmd #Check the process id
    kill -9 <pid>

Send scapy packet again. Check VF1 can't receive the packet ::

    show port stats all

Expect: VF1 can't receive the packet


TC13: Launch 2nd DCF process on the same VF
-------------------------------------------

Launch 2nd DCF process on the same VF, PF shall reject the request.
DPDK does not support to open 2nd DCF PMD driver on same VF.

Generate 4 VFs on PF

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf -- -i

Launch another testpmd on the DCF ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 11-14 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf2 -- -i

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
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf -- -i

Launch another testpmd on the VF1 and VF2, and start mac forward ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 11-14 -n 4 -w 18:01.1 --file-prefix=vf1 -- -i
    set verbose 1
    set fwd mac
    start

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 15-16 -n 4 -w 18:01.2 --file-prefix=vf2 -- -i
    set verbose 1
    set fwd mac
    start

Set switch rule to VF1 0000:18:01.1 from DCF ::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.4 dst is 192.168.0.5 / end actions vf id 1 / end

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
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf -- -i

Launch another testpmd on the VF1, and start mac forward ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 11-14 -n 4 -w 18:01.1 -w 18:01.2 --file-prefix=vf -- -i
    set verbose 1
    set fwd macstart

Set switch rule to VF1 0000:18:01.1 and VF2 0000:18:01.2 from DCF ::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end

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

Send scapy packet again. Check VF1 can't receive the packet

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
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf -- -i

Expect: testpmd can't be launched. PF should reject DCF mode.

Remove ADQ on PF ::

    tc filter del dev enp24s0f0 parent ffff: pref 1 protocol ip
    tc filter show dev enp24s0f0 parent ffff:
    tc qdisc del dev enp24s0f0 root mqprio
    tc qdisc del dev enp24s0f0 ingress
    tc qdisc show dev enp24s0f0

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf -- -i

Expect: testpmd can launch successfully. DCF mode can be grant ::

    EAL: PCI device 0000:18:01.0 on NUMA socket 0
    EAL: probe driver: 8086:1889 net_ice_dcf


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
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf -- -i

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
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=dcf -- -i

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

    ethtool -K enp24s0f0 l2-fwd-offload on
    ip link add link macvlan0 link enp24s0f0 type macvlan
    ifconfig macvlan0 192.168.1.111
    ipconfig macvlan0 up

Remove MAC-VLAN commands ::

  ip link del macvlan0
  ethtool -K enp24s0f0 l2-fwd-offload off
