.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

===============================
ICE IAVF Flow Subscription Test
===============================

Description
===========

IAVF is able to subscribe a flow from PF through virtual channel.

1. IAVF driver support rte_flow "to port" action, the port id must be itself.
2. only trusted VF can flow subscribe.
3. only a flow that dst mac address matched PF's mac addresses can be subscribed.
4. if the rule does not contain pf dst mac address, the mac address of PF will be used as the dst mac by default.
5. vf restet, all subscribed rule will be deleted automatically by PF driver.
6. ideally one VF's subscription should not impact another VF's subscription, so the application running on each VF can belong to an independent security domain.
7. if two VF's subscriptions have overlap, a packet matched both subscription rules should be replicated into 2 VFs.
8. pf reset all flow subscribe rules will be invalid.
9. one pf reset will not affect other pfs.


DPDK changes::

    1. IAVF driver will support rte_flow "to port" action, the port id should be itself.
    2. IAVF driver transfer the "to port" flow into virtual channel command "FLOW_SUBCRIBE" combined the matched pattern.
    3. to destroy a rule, IAVF need to send command "FLOW_UNSUBSCRIBE" to PF.

Kernel driver change::

    1. introduce an new security level as "flow subscribe" above "trusted" for VF, use devlink to configure VF for the new security level.(optional in POC)
    2. support FLOW_SUBCSRIBE virtchal command and transfer it into switch rule.
    3. any rule that contain dst mac matched but the dst mac is not one of the PF will be rejected
    4. any rule don't contains dst mac match, the PF will force to append the matched to the rule.
    5. when VF reset is detected, all subscribed rule will be deleted automatically by PF driver.

Prerequisites
=============

Hardware
--------
    Supportted NICs: Intel® Ethernet 800 Series: E810-XXVDA4/E810-CQ, etc.

Software
--------
    DPDK: http://dpdk.org/git/dpdk

    Scapy: http://www.secdev.org/projects/scapy/

General Set Up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir>

2. insmod ice.ko, and bind PF to ice.

case: flow subscription smoke test
==================================

Subcase 1: 1 PF 4 VFs
---------------------
1. only trusted VF can flow subscribe.
2. only a flow that matches dst mac address to its PF’s mac addresses can be subscribed.
3. rule don't contains PF dst mac match, the PF will force to append the matched to the rule.
4. vf restet, all subscribed rule will be deleted automatically by PF driver.
5. if two VF's subscriptions have overlap, a packet matched both subscription rules should be replicated into 2 VFs.

create and set vf::

    echo 4 > /sys/bus/pci/devices/0000\:31\:00.0/sriov_numvfs
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:31:01.0 0000:31:01.1 0000:31:01.2 0000:31:01.3
    ip link set ens85f0 vf 0 trust on
    ip link set ens85f0 vf 1 trust on
    ip link set ens85f0 vf 2 trust on
    ip link set ens85f0 vf 3 trust on

launch the userland ``testpmd`` application on DUT as follows and ::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> <all vf> -- -i
    testpmd> set verbose 1
    testpmd> set fwd rxonly
    testpmd> set promisc all off
    testpmd> start

validate and create rules::

    testpmd> flow validate/create 0 ingress pattern eth dst is {pf_mac} / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end
    Flow rule validated/Flow rule #0 created
    testpmd> flow validate/create 1 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 1 / end
    Flow rule validated/Flow rule #0 created
    testpmd> flow validate/create 2 ingress pattern eth dst is {pf_mac} / ipv4 / udp src is 22 / end actions port_representor port_id 2 / end
    Flow rule validated/Flow rule #0 created
    testpmd> flow validate/create 3 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 3 / end
    Flow rule validated/Flow rule #0 created

Check all can validate/create successully.

check rule list::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => REPRESENTED_PORT
    testpmd> flow list 1
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => REPRESENTED_PORT
    testpmd> flow list 2
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => REPRESENTED_PORT
    testpmd> flow list 3
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => REPRESENTED_PORT

send matched packets::

    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80),

All vf can received the packet.

send mismatched packets::

    Ether(dst={other_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80),
    Ether(dst={pf_mac})/IPv6()/UDP(sport=22)/Raw("x" * 80),
    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/Raw("x" * 80),
    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22)/Raw("x" * 80),

All vf can not received all the packets.

vf reset::

    testpmd> stop
    testpmd> port stop all
    testpmd> port reset all
    testpmd> port start all
    testpmd> start
    testpmd> flow list 0
    testpmd> flow list 1
    testpmd> flow list 2
    testpmd> flow list 3

Check all vf have no flow subscribe rule.

send matched packets::

    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80),

All vf can not received the packet.

Subcase 2: 2 PFs 4 VFs
----------------------
1. reset PF mac and still be able to flow subscribe.
2. all VFs can flow subscribe.
3. flow subscribe not affect the normal packet receiving of VF.
4. ideally one VF's subscription should not impact another VF's subscription, so the application running on each VF can belong to an independent security domain.

create and set vf::

    ip link set dev ens85f0 address 00:11:22:33:44:55
    ip link set dev ens85f1 address 00:11:22:33:44:66
    echo 2 > /sys/bus/pci/devices/0000\:31\:00.0/sriov_numvfs
    echo 2 > /sys/bus/pci/devices/0000\:31\:00.1/sriov_numvfs
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:31:01.0 0000:31:01.1 0000:31:09.0 0000:31:09.1
    ip link set ens85f0 vf 0 trust on
    ip link set ens85f0 vf 1 trust off
    ip link set ens85f1 vf 0 trust on
    ip link set ens85f1 vf 1 trust off

Launch two "testpmd" application on DUT as follows::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> <pf0 vfs pci> -- -i
    testpmd> set verbose 1
    testpmd> set fwd rxonly
    testpmd> set promisc all off
    testpmd> start
    <dpdk build dir>/app/dpdk-testpmd <EAL options> <pf1 vfs pci> -- -i
    testpmd> set verbose 1
    testpmd> set fwd rxonly
    testpmd> set promisc all off
    testpmd> start

create rules in two testpmds respectively::

    testpmd> flow create 0 ingress pattern eth dst is {old_pf_mac} / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end
    iavf_execute_vf_cmd(): Return failure -5 for cmd 114
    iavf_flow_sub(): Failed to execute command of OP_FLOW_SUBSCRIBE
    iavf_flow_sub(): Failed to add rule request due to the hw doesn't support
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

    testpmd> flow create 0 ingress pattern eth dst is {new_pf_mac} / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end
    Flow rule #0 created

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => REPRESENTED_PORT

Check rule 0 create failed, rule 1 create successully in two testpmd respectively.

send vf normal packets::

    Ether(dst={vf_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80),
    Ether(dst={vf_mac})/IPv6(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22)/Raw("x" * 80),
    Ether(dst={vf_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80),
    Ether(dst={vf_mac})/IPv6(src="::22",dst="::11")/Raw("x" * 80),

Send all the normal packets to each vf separately and
check all vfs only can receive the corresponding mac packets.

send matched rule packets::

    Ether(dst={new_pf0_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80),
    Ether(dst={new_pf1_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80),

send all matched packets from port 0 and port 1 of the tester,
and check that all vfs can only receive packets whose dst mac is their pf.

send mismatched rule packets::

    Ether(dst={old_pf0_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80),
    Ether(dst={old_pf1_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80),
    Ether(dst={new_pf0_mac})/IPv6()/UDP(sport=22)/Raw("x" * 80),
    Ether(src={new_pf1_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/Raw("x" * 80),
    Ether(dst={new_pf0_mac})/IP(src="192.168.0.20",dst="192.168.0.21")/TCP()/Raw("x" * 80),

Send all mismatched packets from port 0 and port 1 of the tester,
and check that all vfs can not receive these packets.

destroy the rule in two testpmd respectively::

    testpmd> flow flush 0

Send all the normal packets to each vf separately again
and check all vfs also only can receive the corresponding mac packets.

Send all matched packets from port 0 and port 1 of the tester again,
and check that all vfs can not receive these packets.

Subcase 3: exclusive rule
-------------------------
1. the same flow subscribe rule only can create once.
2. after the rule of to queue is created, the rule of the same input set can't be created.

create and set vf::

    echo 4 > /sys/bus/pci/devices/0000\:31\:00.0/sriov_numvfs
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:31:01.0 0000:31:01.1 0000:31:01.2 0000:31:01.3
    ip link set ens85f0 vf 0 trust on
    ip link set ens85f0 vf 1 trust on
    ip link set ens85f0 vf 2 trust on
    ip link set ens85f0 vf 3 trust on

launch the "testpmd" application on DUT as follows::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -- -i --rxq=8 --txq=8
    testpmd> set verbose 1
    testpmd> set fwd rxonly
    testpmd> set promisc all off
    testpmd> start

create rule::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end
    Flow rule #0 created
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end
    iavf_execute_vf_cmd(): Return failure -5 for cmd 114
    iavf_flow_sub(): Failed to execute command of OP_FLOW_SUBSCRIBE
    iavf_flow_sub(): Failed to add rule request due to the hw doesn't support
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

The same flow subscribe rule only can create once, so check rule 0 create successful, rule 1 create failed.

flush rule::

    testpmd> flow flush 0

create rule::

    testpmd> flow create 2 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 2 / queue index 3 / end
    Flow rule #0 created
    testpmd> flow create 3 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 3 / queue index 4 / end
    iavf_execute_vf_cmd(): Return failure -5 for cmd 114
    iavf_flow_sub(): Failed to execute command of OP_FLOW_SUBSCRIBE
    iavf_flow_sub(): Failed to add rule request due to the hw doesn't support
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

After the rule of to queue is created, the rule of the same inputset can't be created,
so check rule 0 create successful, rule 1 create successful failed.

destory rule 0 and recreate rule::

    testpmd> flow destory 2 rule 0
    testpmd> flow create 3 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 3 / queue index 4 / end
    Flow rule #0 created
    testpmd> flow create 2 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 2 / queue index 3 / end
    iavf_execute_vf_cmd(): Return failure -5 for cmd 114
    iavf_flow_sub(): Failed to execute command of OP_FLOW_SUBSCRIBE
    iavf_flow_sub(): Failed to add rule request due to the hw doesn't support
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

check rule 1 create successful, rule 0 create successful failed.

Subcase 4: negative rule
------------------------
1. Iavf driver will support rte_flow "to port" action, the port id should be itself.
2. only trusted VF can flow subscribe.
3. only a flow that matches dst mac address to its PF’s mac addresses can be subscribed.
4. not support the input set is src mac adress

create and set vf::

    echo 4 > /sys/bus/pci/devices/0000\:31\:00.0/sriov_numvfs
    ip link set ens85f0 vf 0 trust on
    ip link set ens85f0 vf 1 trust on
    ip link set ens85f0 vf 2 trust on
    ip link set ens85f0 vf 3 trust off

launch the "testpmd" application on DUT as follows::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> <all vf> -- -i

create rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 1 / end
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

    testpmd> flow create 1 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument


    testpmd> flow create 0 ingress pattern eth dst is {not_pf0_mac} / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end
    iavf_execute_vf_cmd(): Return failure -5 for cmd 114
    iavf_flow_sub(): Failed to execute command of OP_FLOW_SUBSCRIBE
    iavf_flow_sub(): Failed to add rule request due to the hw doesn't support
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

    testpmd> flow create 1 ingress pattern eth dst is {not_pf0_mac} / ipv4 / udp src is 22 / end actions port_representor port_id 1 / end
    iavf_execute_vf_cmd(): Return failure -5 for cmd 114
    iavf_flow_sub(): Failed to execute command of OP_FLOW_SUBSCRIBE
    iavf_flow_sub(): Failed to add rule request due to the hw doesn't support
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument


    testpmd> flow create 2 ingress pattern eth src is {pf0_mac} / ipv4 / udp src is 22 / end actions port_representor port_id 2 / end
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

    testpmd> flow create 3 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 3 / end
    iavf_execute_vf_cmd(): Return failure -5 for cmd 114
    iavf_flow_sub(): Failed to execute command of OP_FLOW_SUBSCRIBE
    iavf_flow_sub(): Failed to add rule request due to the hw doesn't support
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

check all rule create failed.

Subcase 5: pf reset
-------------------
1. pf reset all flow subscribe rules will be invalid.
2. one pf reset will not affect other pfs

create and set vf::

    echo 2 > /sys/bus/pci/devices/0000\:31\:00.0/sriov_numvfs
    echo 2 > /sys/bus/pci/devices/0000\:31\:00.1/sriov_numvfs
    ip link set ens85f0 vf 0 trust on
    ip link set ens85f0 vf 1 trust on
    ip link set ens85f1 vf 0 trust on
    ip link set ens85f1 vf 1 trust on

launch two "testpmd" application on DUT as follows::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> <pf0 vfs pci> -- -i
    testpmd> set verbose 1
    testpmd> set fwd rxonly
    testpmd> set promisc all off
    testpmd> start
    <dpdk build dir>/app/dpdk-testpmd <EAL options> <pf1 vfs pci> -- -i
    testpmd> set verbose 1
    testpmd> set fwd rxonly
    testpmd> set promisc all off
    testpmd> start

rule::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end
    Flow rule #0 created
    testpmd> flow create 1 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 1 / end
    Flow rule #0 created
    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => REPRESENTED_PORT
    testpmd> flow list 1
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => REPRESENTED_PORT


check all vf flow subscribe rule successful in 2 testpmd respectively.

send packet::

    packet1: Ether(dst={pf0_mac})/IP()/UDP(sport=22)/Raw("x"*80),
    packet2: Ether(dst={pf1_mac})/IP()/UDP(sport=22)/Raw("x"*80),

vf0 and vf1 of pf0 can receive packet1, vf1 and vf2 of pf1 can receive packet2.

pf0 reset::

    echo 1 > /sys/bus/pci/devices/0000\:31\:00.0/reset

send packet::

    packet1: Ether(dst={pf0_mac})/IP()/UDP(sport=22)/Raw("x"*80),
    packet2: Ether(dst={pf1_mac})/IP()/UDP(sport=22)/Raw("x"*80),

vf0 and vf1 of pf0 can not receive packet1, vf1 and vf2 of pf1 can receive packet2.

pf1 reset::

    echo 1 > /sys/bus/pci/devices/0000\:89\:00.1/reset

send packet::

    packet1:Ether(dst={pf0_mac})/IP()/UDP(sport=22)/Raw("x"*80),
    packet2:Ether(dst={pf1_mac})/IP()/UDP(sport=22)/Raw("x"*80),

vf0 and vf1 of pf0 can not receive packet1, vf1 and vf2 of pf 1 can not receive packet2.


flow subscribe Test
====================

Pattern and input set
---------------------

+--------------------------------------------------------+--------------------------------------+----------------------------------------------------------------+
|                          Pattern                       |                Input Set             |                         Comments                               |
+========================================================+======================================+================================================================+
|  MAC_IPV4_UDP_VXLAN_MAC_IPV4/IPV6_TCP/UDP/ICPM_PAYLOAD |   outer_ipv4 + outer_udp(dstP=4789)  | actions port_representor port_id {vf_id}                       |
+--------------------------------------------------------+--------------------------------------+----------------------------------------------------------------+
|  MAC_IPV6_UDP_VXLAN_MAC_IPV4/IPV6_TCP/UDP/ICPM_PAYLOAD |   outer_udp(dstP=4789)               | actions port_representor port_id {vf_id}                       |
+--------------------------------------------------------+--------------------------------------+----------------------------------------------------------------+
|  MAC_IPV4_UDP_PAYLOAD                                  |   srcIP + dstIP + srcPort + dstPort  | actions port_representor port_id {vf_id} + rss + priority      |
+--------------------------------------------------------+--------------------------------------+----------------------------------------------------------------+
|  MAC_IPV4_TCP_PAYLOAD                                  |   srcIP + dstIP + srcPort + dstPort  | actions port_representor port_id {vf_id} + to queue + priority |
+--------------------------------------------------------+--------------------------------------+----------------------------------------------------------------+
|  MAC_IPV6_UDP_PAYLOAD                                  |   dstIP + srcPort+ dstPort           | actions port_representor port_id {vf_id} + to queue + priority |
+--------------------------------------------------------+--------------------------------------+----------------------------------------------------------------+
|  MAC_IPV6_TCP_PAYLOAD                                  |   srcIP + srcPort + dstPort          | actions port_representor port_id {vf_id} + rss + priority      |
+--------------------------------------------------------+--------------------------------------+----------------------------------------------------------------+
|  MAC_VLAN_IPV4                                         |   vlan_id, dstIP,                    | actions port_representor port_id {vf_id}                       |
+--------------------------------------------------------+--------------------------------------+----------------------------------------------------------------+
|  MAC_IPV4_ICMP                                         |   ipv4(proto=1)                      | actions port_representor port_id {vf_id}                       |
+--------------------------------------------------------+--------------------------------------+----------------------------------------------------------------+
|  MAC_IPV4/IPV6_PAYLOAD                                 |   srcIP mask + dstIP mask            | actions port_representor port_id {vf_id}                       |
+--------------------------------------------------------+--------------------------------------+----------------------------------------------------------------+
|  MAC_IPV4/IPV6_TCP/UDP_PAYLOAD                         |   srcPort mask + dstPort mask        | actions port_representor port_id {vf_id}                       |
+--------------------------------------------------------+--------------------------------------+----------------------------------------------------------------+

  .. note::

   1. The maximum input set length of a switch rule is 32 bytes, and src ipv6,
      dst ipv6 account for 32 bytes. Therefore, for ipv6 cases, if need to test
      fields other than src, dst ip, we create rule by removing src or dst ip in
      the test plan.

flow subscribe Prerequisites
----------------------------

1. create and set vf::

    echo 4 > /sys/bus/pci/devices/0000\:31\:00.0/sriov_numvfs
    ip link set ens85f0 vf 0 trust on

2. bind the Dut port to dpdk::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>

3. launch "testpmd" application on DUT as follows::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a <vf_pci> -- -i --rxq=<queue number> --txq=<queue number>
    testpmd> set verbose 1
    testpmd> set fwd rxonly
    testpmd> set promisc all off
    testpmd> start

test steps for flow subscribe
=============================
1. validate rules.
2. create rules and check rules list for vf.
3. send matched packets, check the packets are received by vf and queue.
4. send mismatched packets, check the packets are not received by vf
5. destroy rule, list rules.
6. send matched packets, check the packtet can not received by vf.

case: MAC_IPV4_UDP_VXLAN
========================
rule::

    flow create 0 ingress pattern eth / ipv4 / udp dst is 4789 / end actions port_representor port_id 0 / end

matched packets::

    Ether(dst={pf_mac})/IP()/UDP(dport=4789)/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP()/VXLAN()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP()/VXLAN()/Ether()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP()/VXLAN()/Ether()/IP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP()/VXLAN()/Ether()/IP()/TCP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP()/VXLAN()/Ether()/IP()/UDP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP()/VXLAN()/Ether()/IP()/ICMP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP()/VXLAN()/Ether()/IPv6()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP()/VXLAN()/Ether()/IPv6()/TCP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP()/VXLAN()/Ether()/IPv6()/UDP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP()/VXLAN()/Ether()/IPv6()/ICMP()/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/IPv6()/UDP()/VXLAN()/Ether()/IP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP(dport=1)/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP(dport=1)/VXLAN()/Ether()/IP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/TCP()/VXLAN()/Ether()/IP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/ICMP()/VXLAN()/Ether()/IP()/Raw("x"*80),

case: MAC_IPV6_UDP_VXLAN
========================

rule::

   flow create 0 ingress pattern eth / ipv6 / udp dst is 4789 / end actions port_representor port_id 0 / end

matched packets::

    Ether(dst={pf_mac})/IPv6()/UDP(dport=4789)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP()/VXLAN()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP()/VXLAN()/Ether()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP()/VXLAN()/Ether()/IP()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP()/VXLAN()/Ether()/IP()/TCP()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP()/VXLAN()/Ether()/IP()/UDP()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP()/VXLAN()/Ether()/IP()/ICMP()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP()/VXLAN()/Ether()/IPv6()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP()/VXLAN()/Ether()/IPv6()/TCP()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP()/VXLAN()/Ether()/IPv6()/UDP()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP()/VXLAN()/Ether()/IPv6()/ICMP()/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/IP()/UDP()/VXLAN()/Ether()/IP()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP(dport=1)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP(dport=1)/VXLAN()/Ether()/IP()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/TCP()/VXLAN()/Ether()/IP()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/ICMP()/VXLAN()/Ether()/IP()/Raw("x"*80),

case: MAC_VLAN_IPV4
===================
rule::

    flow create 0 ingress pattern eth / vlan tci is 1 / ipv4 dst is 192.168.0.1 / end actions port_representor port_id 0 / end

matched packets::

    Ether(dst={pf_mac})/Dot1Q(vlan=1)/IP(dst="192.168.0.1")/Raw("x"*80),
    Ether(dst={pf_mac})/Dot1Q(vlan=1)/IP(dst="192.168.0.1")/UDP()/Raw("x"*80),
    Ether(dst={pf_mac})/Dot1Q(vlan=1)/IP(dst="192.168.0.1")/TCP()/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/Dot1Q(vlan=1)/Raw("x"*80),
    Ether(dst={pf_mac})/IP(dst="192.168.0.1")/Raw("x"*80),
    Ether(dst={pf_mac})/Dot1Q(vlan=1)/IP(dst="192.168.0.2")/Raw("x"*80),
    Ether(dst={pf_mac})/Dot1Q(vlan=2)/IP(dst="192.168.0.1")/Raw("x"*80),

case: MAC_IPV4_ICMP
===================
rule::

    flow create 0 ingress pattern eth / ipv4 proto is 0x1 / end actions port_representor port_id 0 / end

matched packets::

    Ether(dst={pf_mac})/IP(proto=1)/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/ICMP()/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/IP(proto=2)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/ICMP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/TCP()/Raw("x"*80),

case: l3 mask
=============

subcase 1: MAC_IPV4_SRC_DST_MASK
--------------------------------
rule::

    flow create 0 ingress pattern eth / ipv4 src spec 224.0.0.0 src mask 255.0.0.0 dst spec 224.0.0.0 dst mask 255.0.0.0 / end actions port_representor port_id 0 / end

matched packets::

    Ether(dst={pf_mac})/IP(src="224.255.255.255",dst="224.255.255.255")/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="224.255.255.255",dst="224.0.0.0")/UDP(sport=22)/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="224.0.0.0",dst="224.255.255.255")/TCP(sport=22)/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/IP(src="225.0.0.0",dst="225.0.0.0")/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="225.0.0.0",dst="224.0.0.0")/UDP(sport=22)/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="224.0.0.0",dst="225.0.0.0")/TCP(sport=22)/Raw("x"*80),

subcase 2: MAC_IPV6_SRC_MASK
----------------------------
rule::

    flow create 0 ingress pattern eth / ipv6 src spec CDCD:910A:2222:5498:8475:1111:3900:2020 src mask ffff:ffff:ffff:ffff:0000:0000:0000:0000 dst spec CDCD:910A:2222:5498:8475:1111:3900:2020 dst mask ffff:ffff:ffff:ffff:0000:0000:0000:0000 / end actions port_representor port_id 0 / end

matched packets::

    Ether(dst={pf_mac})/IPv6(dst="CDCD:910A:2222:5498:0000:0000:0000:0000",src="CDCD:910A:2222:5498:0000:0000:0000:0000")/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="CDCD:910A:2222:5498:0000:0000:0000:0000")/UDP(sport=22)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(dst="CDCD:910A:2222:5498:0000:0000:0000:0000",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22)/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/IPv6(dst="CDCD:910A:2222:5499:8475:1111:3900:2020",src="CDCD:910A:2222:5499:8475:1111:3900:2020")/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(dst="CDCD:910A:2222:5498:0000:0000:0000:0000",src="CDCD:910A:2222:5499:8475:1111:3900:2020")/UDP(sport=22)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(dst="dst="CDCD:910A:2222:5499:8475:1111:3900:2020",src="CDCD:910A:2222:5498:0000:0000:0000:0000")/TCP(sport=22)/Raw("x"*80),

case : l4 mask
==============

subcase 1: MAC_IPV4_UDP_SRC_DST_MASK
------------------------------------
rule::

    flow create 0 ingress pattern eth / ipv4 / udp src spec 2152 src mask 0xff00 dst spec 1281 dst mask 0x00ff / end actions port_representor port_id 0 / end

matched packets::

	Ether(dst={pf_mac})/IP()/UDP(sport=2048,dport=1)/Raw("x"*80),

mismatched packets::

	Ether(dst={pf_mac})/IP()/Raw("x"*80),
	Ether(dst={pf_mac})/IP()/UDP(sport=104,dport=1281)/Raw("x"*80),
	Ether(dst={pf_mac})/IP()/UDP(sport=2152,dport=1280)/Raw("x"*80),
	Ether(dst={pf_mac})/IP()/TCP(sport=2152,dport=1281)/Raw("x"*80),
	Ether(dst={pf_mac})/IPv6()/UDP(sport=2152,dport=1281)/Raw("x"*80),

subcase 2: MAC_IPV4_TCP_SRC_DST_MASK
------------------------------------
rule::

	flow create 0 ingress pattern eth / ipv4 / tcp src spec 2152 src mask 0xff00 dst spec 1281 dst mask 0x00ff / end actions port_representor port_id 0 / end

matched packets::

	Ether(dst={pf_mac})/IP()/TCP(sport=2048,dport=1)/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/IP()/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/TCP(sport=104,dport=1281)/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/TCP(sport=2152,dport=1280)/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/UDP(sport=2152,dport=1281)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/TCP(sport=2152,dport=1281)/Raw("x"*80),

subcase 3: MAC_IPV6_UDP_SRC_DST_MASK
------------------------------------
rule::

	flow create 0 ingress pattern eth / ipv6 / udp src spec 2152 src mask 0xff00 dst spec 1281 dst mask 0x00ff / end actions port_representor port_id 0 / end

matched packets::

	Ether(dst={pf_mac})/IPv6()/UDP(sport=2048,dport=1)/Raw("x"*80),

mismatched packets::

	Ether(dst={pf_mac})/IPv6()/Raw("x"*80),
	Ether(dst={pf_mac})/IPv6()/UDP(sport=104,dport=1281)/Raw("x"*80),
	Ether(dst={pf_mac})/IPv6()/UDP(sport=2152,dport=1280)/Raw("x"*80),
	Ether(dst={pf_mac})/IPv6()/TCP(sport=2152,dport=1281)/Raw("x"*80),
	Ether(dst={pf_mac})/IP()/UDP(sport=2152,dport=1281)/Raw("x"*80),

subcase 4: MAC_IPV6_TCP_SRC_DST_MASK
------------------------------------
rule::

	flow create 0 ingress pattern eth / ipv6 / tcp src spec 2152 src mask 0xff00 dst spec 1281 dst mask 0x00ff / end actions port_representor port_id 0 / end

matched packets::

	Ether(dst={pf_mac})/IPv6()/TCP(sport=2048,dport=1)/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/IPv6()/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/TCP(sport=104,dport=1281)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/TCP(sport=2152,dport=1280)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6()/UDP(sport=2152,dport=1281)/Raw("x"*80),
    Ether(dst={pf_mac})/IP()/TCP(sport=2152,dport=1281)/Raw("x"*80),

test steps for supported flow subscribe priority
================================================
1. validate rules: two rules have same pattern, input set but different priority and action(priority 0 -> to queue 5, priority 1 -> to queue 6).
2. create rules and list rules for vf.
3. send matched packets, check vf receive the packets for hiting the priority 0.
4. send mismatched packets, check the packets are not received by vf.
5. destroy rule with priority 0, list rules.
6. send matched packets, check vf receive the packets for hiting the priority 1.
7. create rule 0 and send matched packet, check vf receive the packets for hiting the priority 0.

case: MAC_IPV4_UDP_PAYLOAD_priority
===================================

rule::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / udp src is 2048 dst is 2022 / end actions port_representor port_id 0 / rss queues 4 5 end / end
    flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / udp src is 2048 dst is 2022 / end actions port_representor port_id 0 / rss queues 6 7 end / end

matched packets::

    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.1")/UDP(sport=2048,dport=2022)/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.1")/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="192.168.0.21",dst="192.168.0.1")/UDP(sport=2048,dport=2022)/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.2")/UDP(sport=2048,dport=2022)/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.1")/UDP(sport=2047,dport=2022)/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.1")/UDP(sport=2048,dport=2023)/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.1")/TCP(sport=2048,dport=2022)/Raw("x"*80),

case: MAC_IPV4_TCP_PAYLOAD_priority
===================================

rule::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / tcp src is 2048 dst is 2022 / end actions port_representor port_id 0 / queue index 2 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / tcp src is 2048 dst is 2022 / end actions port_representor port_id 0 / queue index 3 / end / end

matched packets::

    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.1")/TCP(sport=2048,dport=2022)/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.1")/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="192.168.0.21",dst="192.168.0.1")/TCP(sport=2048,dport=2022)/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="192.168.0.21",dst="192.168.0.1")/TCP(sport=2048,dport=2022)/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.1")/TCP(sport=2047,dport=2022)/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.1")/TCP(sport=2048,dport=2023)/Raw("x"*80),
    Ether(dst={pf_mac})/IP(src="192.168.0.20",dst="192.168.0.1")/UDP(sport=2048,dport=2022)/Raw("x"*80),


case: MAC_IPV6_UDP_PAYLOAD_priority
===================================

rule::

    flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 2048 dst is 2022 / end actions port_representor port_id 0 / rss queues 4 5 end / end
    flow create 0 priority 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 2048 dst is 2022 / end actions port_representor port_id 0 / rss queues 6 7 end / end

matched packets::

    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=2048,dport=2022)/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=2048,dport=2022)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=2048,dport=2023)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=2047,dport=2022)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=2048,dport=2022)/Raw("x"*80),

case: MAC_IPV6_TCP_PAYLOAD_priority
===================================

rule::

    flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 / tcp src is 2048 dst is 2022 / end actions port_representor port_id 0 / queue index 2 / end
    flow create 0 priority 1 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 / tcp src is 2048 dst is 2022 / end actions port_representor port_id 0 / queue index 3 / end

matched packets::

    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=2048,dport=2022)/Raw("x"*80),

mismatched packets::

    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=2048,dport=2022)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=2047,dport=2023)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=2048,dport=2023)/Raw("x"*80),
    Ether(dst={pf_mac})/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=2048,dport=2022)/Raw("x"*80),

