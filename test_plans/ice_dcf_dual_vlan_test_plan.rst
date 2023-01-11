.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021-2022 Intel Corporation

=========================
ICE support QinQ protocol
=========================
DPDK support QinQ protocol in Intel® Ethernet 800 Series as below requirements:
* DCF support QinQ by add steering rule and vlan strip disable.
* DCF is able to set port vlan by port representor.

this test plan contain 2 parts to cover above requirements:
* DCF switch filter for QinQ.
* DCF pvid support for QinQ.

Intel® Ethernet 800 Series support l4 for QinQ switch filter in DCF driver is by
dst MAC + outer VLAN id + inner VLAN id + dst IP + dst port, and port can support
as eth / vlan / vlan / IP / tcp|udp.
* Enable QINQ switch filter for IPv4/IPv6, IPv4 + TCP/UDP in non-pipeline mode.
* Enable QINQ switch filter for IPv6 + TCP/UDP in pipeline mode.

Prerequisites
=============
1. Hardware:
   Intel® Ethernet 800 Series: E810-XXVDA4/E810-CQ

2. Software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Copy specific ice package to /lib/firmware/updates/intel/ice/ddp/ice.pkg,
   then load driver::

    rmmod ice
    insmod ice.ko

4. Compile DPDK::

    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

5. Get the pci device id of DUT, for example::

    ./usertools/dpdk-devbind.py -s

    0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci
    0000:18:00.1 'Device 159b' if=ens785f1 drv=ice unused=vfio-pci

6. Disable vlan prune flag::

    ethtool --set-priv-flags ens785f0 vf-vlan-pruning off

7. Generate 4 VFs on PF0(not all the VFs are used)::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

    ./usertools/dpdk-devbind.py -s
    0000:18:01.0 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v0 drv=iavf unused=vfio-pci
    0000:18:01.1 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v1 drv=iavf unused=vfio-pci
    0000:18:01.2 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v2 drv=iavf unused=vfio-pci
    0000:18:01.3 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v3 drv=iavf unused=vfio-pci

8. Set VF0 as trust::

    ip link set ens785f0 vf 0 trust on

9. Set mac addr for VF1, VF2 and VF3::

    ip link set ens785f0 vf 1 mac 00:11:22:33:44:11
    ip link set ens785f0 vf 2 mac 00:11:22:33:44:22
    ip link set ens785f0 vf 3 mac 00:11:22:33:44:33

10. Bind VFs to dpdk driver::

     modprobe vfio-pci
     ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0 0000:18:01.1 0000:18:01.2 0000:18:01.3

11. Disabel spoofchk for VF::

     ip link set dev ens785f0 vf 0 spoofchk off
     ip link set dev ens785f0 vf 1 spoofchk off
     ip link set dev ens785f0 vf 2 spoofchk off
     ip link set dev ens785f0 vf 3 spoofchk off

12. For test cases for Non-pipeline mode(case 01-07,09-11), use below cmd to launch testpmd::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf,representor=[1] -a 0000:18:01.1 -a 0000:18:01.2 -a 0000:18:01.3 -- -i

   check the port 0 and port 1 driver is net_ice_dcf.

   For test cases for Pipeline mode(case 08), use below cmd to launch testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf,representor=[1],pipeline-mode-support=1 -a 0000:18:01.1 -a 0000:18:01.2 -a 0000:18:01.3 -- -i

   check the VF0 driver is net_ice_dcf.

13. config testpmd::

     testpmd> set fwd mac
     testpmd> set verbose 1
     testpmd> start
     testpmd> show port info all

DCF switch filter support pattern and input set
-----------------------------------------------
.. table::

    +------------------------+--------------------------+---------------------------------------------------------+
    | Packet type            | Pattern                  | All the Input Set options in combination                |
    +========================+==========================+=========================================================+
    | eth_qinq_ipv4          | MAC_QINQ_IPV4_PAY        | dest mac, outer vlan, inner vlan, src ip, dst ip        |
    +------------------------+--------------------------+---------------------------------------------------------+
    | eth_qinq_ipv6          | MAC_QINQ_IPV6_PAY        | dest mac, outer vlan, inner vlan, src ip, dst ip        |
    +------------------------+--------------------------+---------------------------------------------------------+
    | eth_qinq_pppoes        | MAC_QINQ_PPPOE_PAY       | dest mac, outer vlan, inner vlan, seid                  |
    +------------------------+--------------------------+---------------------------------------------------------+
    | eth_qinq_pppoes_proto  | MAC_QINQ_PPPOE_PAY       | dest mac, outer vlan, inner vlan, seid, pppoe_proto_id  |
    +------------------------+--------------------------+---------------------------------------------------------+
    | eth_qinq_pppoes_ipv4   | MAC_QINQ_PPPOE_IPV4_PAY  | dest mac, outer vlan, inner vlan, seid, src ip, dst ip  |
    +------------------------+--------------------------+---------------------------------------------------------+
    | eth_qinq_pppoes_ipv6   | MAC_QINQ_PPPOE_IPV6_PAY  | dest mac, outer vlan, inner vlan, seid, src ip, dst ip  |
    +------------------------+--------------------------+---------------------------------------------------------+


Test case 01: DCF switch for MAC_QINQ_IPV4_PAY
==============================================
subcase: dest mac
-----------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv4 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6()/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.

subcase: src ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv4 src is 196.222.232.221 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.222")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.

subcase: dst ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv4 dst is 196.222.232.221 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.222")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.


Test case 02: DCF switch for MAC_QINQ_IPV6_PAY
==============================================
subcase: dest mac
-----------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv6 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6()/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.

subcase: src ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv6 src is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:9999")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.

subcase: dst ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.


Test case 03: DCF switch for MAC_QINQ_PPPOE_PAY
===============================================

1. create a rule::

    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x21)/IP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.


Test case 04: DCF switch for MAC_QINQ_PPPOE_PAY_Proto
=====================================================

1. create a rule::

    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / pppoe_proto_id is 0x0057 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.


Test case 05: DCF switch for MAC_QINQ_PPPOE_IPV4
================================================
subcase: dest mac
-----------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv4 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x21)/IP()/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.

subcase: src ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv4 src is 196.222.232.221 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP(src="196.222.232.222")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x21)/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.

subcase: dst ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv4 dst is 196.222.232.221 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP(dst="196.222.232.222")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x21)/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.


Test case 06: DCF switch for MAC_QINQ_PPPOE_IPV6
================================================
subcase: dest mac
-----------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv6 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x57)/IPv6()/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.

subcase: src ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv6 src is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:9999")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x57)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.

subcase: dst ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions represented_port ethdev_port_id1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x57)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)], iface="ens786f0")

   check the packets are not to VF1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to VF1.


#Non-pipeline mode
Test case 07: DCF switch for MAC_L4_QINQ
========================================
subcase: MAC_QINQ_IPV4
----------------------
The test case enable QINQ switch filter for IPv4 in non-pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv4.

Test Steps
~~~~~~~~~~
1. Validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV4 => VF

3. Send matched packet in scapy on tester, check the port 2 of DUT received this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*80)],iface="<tester interface>")

DUT::

   testpmd> port 2/queue 0: received 1 packets
   src=A4:BF:01:4D:6F:32 - dst=00:11:22:33:44:55 - type=0x8100 - length=122 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Receive queue=0x0
   ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

4. Send mismatched packet in scapy on tester, check the port 2 of DUT could not receive this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci change inputset>,type=0x0800)/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")/("X"*80)],iface="<tester interface>")

5. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

   Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 3, check the packets are not to VF1.

subcase: MAC_QINQ_IPV6
----------------------
The test case enable QINQ switch filter for IPv6 in non-pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv6.

Test Steps
~~~~~~~~~~
1. Validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV6 => VF

3. Send matched packet in scapy on tester, check the port 2 of DUT received this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/("X"*80)],iface="<tester interface>")

DUT::

   testpmd> port 2/queue 0: received 1 packets
   src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x8100 - length=142 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV6  - l2_len=18 - inner_l2_len=4 - inner_l3_len=40 - Receive queue=0x0
   ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

4. Send mismatched packet in scapy on tester, check the port 2 of DUT could not receive this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci change inputset>,type=0x0800)/IPv6(dst="<ipv6 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst change inputset>")/("X"*80)],iface="<tester interface>")

5. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

   Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 3, check the packets are not to VF1.

subcase: MAC_QINQ_IPV4_UDP
--------------------------
The test case enable QINQ switch filter for IPv4 + UDP in non-pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv4 + UDP.

Test steps
~~~~~~~~~~
1. Validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 / udp src is <sport> dst is <dport> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 / udp src is <sport> dst is <dport> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV4 UDP => VF

3. Send matched packet in scapy on tester, check the port 2 of DUT received this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP()/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

DUT::

   testpmd> port 2/queue 0: received 1 packets
   src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x8100 - length=130 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_UDP  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4 INNER_L4_UDP  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x0
   ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

4. Send mismatched packet in scapy on tester, check the port 2 of DUT could not receive this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP()/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP()/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci change inputset>,type=0x0800)/IP()/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP()/UDP(sport=<sport>,dport=<dport change inputset>)/("X"*80)],iface="<tester interface>")

5. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

   Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 3, check the packets are not to VF1.

subcase: MAC_QINQ_IPV4_TCP
--------------------------
The test case enable QINQ switch filter for IPv4 + TCP in non-pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv4 + TCP.

Test Steps
~~~~~~~~~~
1. Validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 / tcp src is <sport> dst is <dport> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 / tcp src is <sport> dst is <dport> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV4 TCP => VF

3. Send matched packet in scapy on tester, check the port 2 of DUT received this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP()/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

DUT::

   testpmd> port 2/queue 0: received 1 packets
   src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x8100 - length=142 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_TCP  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4 INNER_L4_TCP  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - inner_l4_len=20 - Receive queue=0x0
   ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

4. Send mismatched packet in scapy on tester, check the port 2 of DUT could not receive this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP()/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP()/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci change inputset>,type=0x0800)/IP()/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x0800)/IP()/TCP(sport=<sport>,dport=<dport change inputset>)/("X"*80)],iface="<tester interface>")

5. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

   Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 3, check the packets are not to VF1.

#Pipeline mode
Test case 08: DCF switch for MAC_L4_QINQ_IPV6
=============================================
subcase: MAC_QINQ_IPV6_UDP
--------------------------
The test case enable QINQ switch filter for IPv6 + UDP in pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv6 + UDP.

Test Steps
~~~~~~~~~~
1. Validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / udp src is <sport> dst is <dport> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / udp src is <sport> dst is <dport> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV6 UDP => VF

3. Send matched packet in scapy on tester, check the port 2 of DUT received this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x86DD)/IPv6(dst="<ipv6 dst>")/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

DUT::

   testpmd> port 2/queue 0: received 1 packets
   src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x8100 - length=150 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_UDP  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV6 INNER_L4_UDP  - l2_len=18 - inner_l2_len=4 - inner_l3_len=40 - inner_l4_len=8 - Receive queue=0x0
   ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

4. Send mismatched packet in scapy on tester, check the port 2 of DUT could not receive this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x86DD)/IPv6(dst="<ipv6 dst>")/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x86DD)/IPv6(dst="<ipv6 dst>")/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci change inputset>,type=0x86DD)/IPv6(dst="<ipv6 dst>")/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x86DD)/IPv6(dst="<ipv6 dst change inputset>")/UDP(sport=<sport>,dport=<dport change inputset>)/("X"*80)],iface="<tester interface>")

5. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

   Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 3, check the packets are not to VF1.

subcase: MAC_QINQ_IPV6_TCP
--------------------------
The test case enable QINQ switch filter for IPv6 + TCP in pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv6 + TCP.

Test steps
~~~~~~~~~~
1. Validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / tcp src is <sport> dst is <dport> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / tcp src is <sport> dst is <dport> / end actions represented_port ethdev_port_id1 / end

   Get the message::

     Flow rule #0 created

   Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV6 TCP => VF

3. Send matched packet in scapy on tester, check the port 2 of DUT received this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x86DD)/IPv6(dst="<ipv6 dst>")/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

DUT::

   testpmd> port 2/queue 0: received 1 packets
   src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x8100 - length=162 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_TCP  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV6 INNER_L4_TCP  - l2_len=18 - inner_l2_len=4 - inner_l3_len=40 - inner_l4_len=20 - Receive queue=0x0
   ol_flags: RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

4. Send mismatched packet in scapy on tester, check the port 2 of DUT could not receive this packet.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x86DD)/IPv6(dst="<ipv6 dst>")/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x86DD)/IPv6(dst="<ipv6 dst>")/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci change inputset>,type=0x86DD)/IPv6(dst="<ipv6 dst>")/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=<inner vlan tci>,type=0x86DD)/IPv6(dst="<ipv6 dst change inputset>")/TCP(sport=<sport>,dport=<dport change inputset>)/("X"*80)],iface="<tester interface>")

5. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

   Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 3, check the packets are not to VF1.

Test case 09: DCF vlan strip when pvid enable
=============================================

1. enable vlan header stripping for VF1 by representor::

    testpmd> vlan set strip on 1

    Port 2: reset event

2. reset VF1(port 2)::

    testpmd> port stop 2
    testpmd> port reset 2
    testpmd> port start 2
    testpmd> start

3. tester send qinq pkt and single vlan pkt to VF1::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=21,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

4. check the pkts can be received in VF1 and fwd to tester without outer vlan header::

    testpmd> port 2/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 2/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    10:15:10.958039 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:15:10.958121 00:11:22:33:44:22 > 02:00:00:00:00:03, ethertype 802.1Q (0x8100), length 518: vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    10:15:15.693894 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 21, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:15:15.693942 00:11:22:33:44:22 > 02:00:00:00:00:03, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

5. disable vlan header stripping for VF1::

    testpmd> vlan set strip off 1

    Port 2: reset event

6. reset VF1::

    testpmd> port stop 2
    testpmd> port reset 2
    testpmd> port start 2
    testpmd> start

7. repeat step 3, check the pkts can be received in VF1 and fwd to tester with outer vlan header::

    testpmd> port 2/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 2/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    10:17:55.321952 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:17:55.322008 00:11:22:33:44:22 > 02:00:00:00:00:03, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    10:17:58.009862 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 21, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:17:58.009908 00:11:22:33:44:22 > 02:00:00:00:00:03, ethertype 802.1Q (0x8100), length 518: vlan 21, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

8. repeat step 1,2, then enable vlan strip by AVF::

    testpmd> vlan set strip on 2

9. repeat step 3, check the pkts can be received in VF1 and fwd to tester without both outer and inner vlan header::

    testpmd> port 2/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 2/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    10:28:01.642361 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:28:01.642438 00:11:22:33:44:22 > 02:00:00:00:00:03, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    10:28:10.185876 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 21, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:28:10.185916 00:11:22:33:44:22 > 02:00:00:00:00:03, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

10. relaunch testpmd and enable vlan strip by AVF::

     testpmd> vlan set strip on 2

11. repeat step 1,2 and 3, check the pkts can be received in VF1 and fwd to tester without both outer and inner vlan header::

     testpmd> port 2/queue 0: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x0
     ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

     port 2/queue 0: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
     ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

     10:28:01.642361 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480
     10:28:01.642438 00:11:22:33:44:22 > 02:00:00:00:00:03, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480

     10:28:10.185876 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 21, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480
     10:28:10.185916 00:11:22:33:44:22 > 02:00:00:00:00:03, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480


Test case 10: DCF vlan insertion when pvid enable
=================================================

1. add tx port vlan for VF1 by representor 1::

    testpmd> tx_vlan set pvid 1 24 on

    Port 2: reset event

2. reset VF1::

    testpmd> port stop 2
    testpmd> port reset 2
    testpmd> port start 2
    testpmd> start

3. send a pkt without vlan header to VF2(VF2 rx, VF1 tx)::

    sendp([Ether(dst="00:11:22:33:44:22",type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:22",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

4. check the dpdk can receive this pkt with VF2 and fwd this pkt with outer vlan header id 24 by VF1, and the vlan header ptype is 8100::

    testpmd> port 4/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:22 - type=0x0800 - length=514 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 4/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:22 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    tcpdump -i ens786f0 -nn -e -v
    11:08:01.061908 00:00:00:00:00:00 > 00:11:22:33:44:22, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    11:08:01.061987 00:11:22:33:44:11 > 02:00:00:00:00:02, ethertype 802.1Q (0x8100), length 518: vlan 24, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    11:08:06.773884 00:00:00:00:00:00 > 00:11:22:33:44:22, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    11:08:06.773928 00:11:22:33:44:11 > 02:00:00:00:00:02, ethertype 802.1Q (0x8100), length 522: vlan 24, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

5. change the tpid of vlan header to 88A8 for VF1::

    testpmd> vlan set outer tpid 0x88a8 1

6. reset VF1::

    testpmd> port stop 2
    testpmd> port reset 2
    testpmd> port start 2
    testpmd> start

7. repeat step 3, check the dpdk can receive this pkt with VF2 and fwd this pkt with outer vlan header id 24 by VF1, and the vlan header ptype is 88a8::

    testpmd> port 4/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:22 - type=0x0800 - length=514 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 4/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:22 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    tcpdump -i ens786f0 -nn -e -v
    11:10:32.441834 00:00:00:00:00:00 > 00:11:22:33:44:22, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    11:10:32.441883 00:11:22:33:44:11 > 02:00:00:00:00:02, ethertype 802.1Q-QinQ (0x88a8), length 518: vlan 24, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    11:10:34.081863 00:00:00:00:00:00 > 00:11:22:33:44:22, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    11:10:34.081913 00:11:22:33:44:11 > 02:00:00:00:00:02, ethertype 802.1Q-QinQ (0x88a8), length 522: vlan 24, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

8. change the tpid of vlan header to 9100 for VF1::

    testpmd> vlan set outer tpid 0x9100 1

9. reset VF1::

    testpmd> port stop 2
    testpmd> port reset 2
    testpmd> port start 2
    testpmd> start

10. repeat step 3, check the dpdk can receive this pkt with VF2 and fwd this pkt with outer vlan header id 24 by VF1, and the vlan header ptype is 9100::

     testpmd> port 4/queue 0: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:22 - type=0x0800 - length=514 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
     ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

     port 4/queue 0: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:22 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x0
     ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

     tcpdump -i ens786f0 -nn -e -v
     11:12:13.237834 00:00:00:00:00:00 > 00:11:22:33:44:22, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480
     11:12:13.237890 00:11:22:33:44:11 > 02:00:00:00:00:02, ethertype 802.1Q-9100 (0x9100), length 518: vlan 24, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480

     11:12:26.049869 00:00:00:00:00:00 > 00:11:22:33:44:22, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480
     11:12:26.049920 00:11:22:33:44:11 > 02:00:00:00:00:02, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q-9100, vlan 24, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480

11. enable tx_vlan for VF1 by AVF::

     testpmd> port stop 2
     Stopping ports...
     Checking link statuses...
     Done
     testpmd> tx_vlan set 2 11
     testpmd> port start 2

12. repeat step 3, check the dpdk can receive this pkt with VF2 and fwd this pkt with outer vlan header id 24, inner vlan id 11 by VF1::

     testpmd> port 3/queue 0: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:22 - type=0x0800 - length=514 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
     ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

     port 3/queue 0: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:22 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x0
     ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

     11:22:29.561918 00:00:00:00:00:00 > 00:11:22:33:44:22, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480
     11:22:29.561992 00:11:22:33:44:11 > 02:00:00:00:00:02, ethertype 802.1Q (0x8100), length 522: vlan 24, p 0, ethertype 802.1Q, vlan 11, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480

     11:22:44.481889 00:00:00:00:00:00 > 00:11:22:33:44:22, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480
     11:22:44.481922 00:11:22:33:44:11 > 02:00:00:00:00:02, ethertype 802.1Q (0x8100), length 526: vlan 24, p 0, ethertype 802.1Q, vlan 11, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480

13. relaunch testpmd and execute step 11 then step 1, 2 and 3, check the dpdk can receive this pkt with VF2 and fwd this pkt with outer vlan header id 24, inner vlan id 11 by VF1::

     testpmd> port 3/queue 0: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:22 - type=0x0800 - length=514 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
     ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

     port 3/queue 0: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:22 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x0
     ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

     11:22:29.561918 00:00:00:00:00:00 > 00:11:22:33:44:22, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480
     11:22:29.561992 00:11:22:33:44:11 > 02:00:00:00:00:02, ethertype 802.1Q (0x8100), length 522: vlan 24, p 0, ethertype 802.1Q, vlan 11, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480

     11:22:44.481889 00:00:00:00:00:00 > 00:11:22:33:44:22, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480
     11:22:44.481922 00:11:22:33:44:11 > 02:00:00:00:00:02, ethertype 802.1Q (0x8100), length 526: vlan 24, p 0, ethertype 802.1Q, vlan 11, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480


Test case 11: DCF vlan filter when pvid enable
==============================================

1. reset test environment, create vfs and enable vlan prune flag::

    ethtool --set-priv-flags ens785f0 vf-vlan-pruning on

2. repeat Prerequisites steps from 7 to 12

3. enable vlan filter and add rx_vlan for VF1 by representor::

    testpmd> vlan set filter on 1
    testpmd> rx_vlan add 11 1
    rte_eth_dev_vlan_filter(port_pi=1, vlan_id=11, on=1) failed diag=-95

4. enable vlan filter and add rx_vlan for VF1 by AVF::

    testpmd> vlan set filter on 2
    testpmd> rx_vlan add 11 2

5. tester send qinq pkt and single vlan pkt which outer vlan id is 11 to VF1::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=11,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=11,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

6. check the pkts can be received by VF1 and fwd to tester::

    testpmd> port 2/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=522 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    port 2/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    10:21:53.418039 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 11, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:21:53.418114 00:11:22:33:44:22 > 02:00:00:00:00:03, ethertype 802.1Q (0x8100), length 522: vlan 11, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    10:22:00.005885 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 11, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:22:00.005919 00:11:22:33:44:22 > 02:00:00:00:00:03, ethertype 802.1Q (0x8100), length 518: vlan 11, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

7. tester send qinq pkt and single vlan pkt which outer vlan id is 21 to VF1::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=21,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=21,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

8. check the pkts can not be received by VF1.

9. remove rx_vlan::

    testpmd> rx_vlan rm 11 2

10. repeat step 5, check the pkts can not be received by VF1.
