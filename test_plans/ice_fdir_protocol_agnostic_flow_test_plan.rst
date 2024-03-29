.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=======================================================
ICE PF enable Protocol agnostic flow offloading in FDIR
=======================================================

Description
===========
ICE PF enable protocol agnostic flow offloading in fdir, that means we can use raw packet filter instead of naming filter(legacy flow offloading).
As the raw packet filter using spec and mask to describr pattern and input set,
the protocol agnostic flow offloading is more flexible and customizable compared with legacy flow offloading.
To reduce redundancy, we don't check all the patterns and input set which is covered by naming filter test cases.
this plan only cover below test hints to check the feasibility of protocol agnostic flow offloading:

1. try FDIR with regular 5 tuples for any UDP or TCP packet
2. try FDIR with VXLAN inner IP match (make sure VXLAN tunnel port has been configured either by DCF or swtichdev)
3. try FDIR with GTPU inner IP match
4. try FDIR with GTPU outer IP match
5. try FDIR with un-word-aligned key

And all the rules are created by packageviewer(ICE parser emulator).
The first string of numbers in the rule represents the matched packet's raw pattern spec,
the second string represents the mask, using 'F' to mask the inputset.
Pls get the tool from Intel DPDK team.


Prerequisites
=============

Hardware
--------
Supportted NICs: Intel® Ethernet 800 Series: E810-CQDA2/E810-2CQDA2/E810-XXVDA4 etc.

Software
--------
DPDK: http://dpdk.org/git/dpdk
Scapy: http://www.secdev.org/projects/scapy/

General Set Up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110

2. Get the pci device id and interface of DUT and tester. 
   For example, 0000:18:00.0 and 0000:18:00.1 is pci device id,
   ens785f0 and ens785f1 is interface::

    <dpdk dir># ./usertools/dpdk-devbind.py -s

    0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci
    0000:18:00.1 'Device 159b' if=ens785f1 drv=ice unused=vfio-pci

3. Bind the DUT port to dpdk::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>

4. Launch the userland ``testpmd`` application on DUT as follows and ::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -- -i --rxq=<queue number> --txq=<queue number>
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> rx_vxlan_port add 4789 0
    testpmd> start

..note:: 

    For <EAL options>, you can use "-c 0xf -n 1", you can also refer to testpmd doc for other setings.

5. Import layers when start scapy::

    >>> import sys
    >>> from scapy.contrib.gtp import *


Test Case
=========
common steps
------------
1. validate rules.
2. create rules and list rules.
3. send matched packets, check the action is right::

    queue index: to right queue with mark id
    rss queues: to right queue group with mark id
    passthru: distributed by rss with mark id
    drop: not receive pkt

4. send mismatched packets, check the action is not right::

    queue index: not to right queue without mark id
    rss queues: not to right queue group without mark id
    passthru: distributed by rss without mark id
    drop: receive pkt

5. destroy rule, list rules.
6. send matched packets, check the action is not right.

Test case 1: ICE_FDIR_MAC/IPv4/UDP
----------------------------------
pattern::

    MAC/IPv4/UDP

inputset::

    IP src/dst, UDP sport/dport

rule::

    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500001C0000000000110000C0A80014C0A800150016001700080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF00000000 / end actions queue index 1 / mark id 10 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500001C0000000000110000C0A80014C0A800150016001700080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF00000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500001C0000000000110000C0A80014C0A800150016001700080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF00000000 / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500001C0000000000110000C0A80014C0A800150016001700080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF00000000 / end actions drop / end

matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="ens786f0")

mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.20",dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=21,dport=23)/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=24)/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="ens786f0")


Test case 2: ICE_FDIR_MAC/IPv6/TCP
----------------------------------
pattern::

    MAC/IPv6/TCP

inputset::

    IP src/dst, TCP sport/dport

rule::

    flow create 0 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000140600CDCD910A222254988475111139001010CDCD910A2222549884751111390020200016001700000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions queue index 1 / mark id 10 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000140600CDCD910A222254988475111139001010CDCD910A2222549884751111390020200016001700000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000140600CDCD910A222254988475111139001010CDCD910A2222549884751111390020200016001700000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000140600CDCD910A222254988475111139001010CDCD910A2222549884751111390020200016001700000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions drop / end

matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=22,dport=23)/("X"*480)], iface="ens786f0")

mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=22,dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1011")/TCP(sport=22,dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=21,dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=22,dport=24)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/UDP(sport=22,dport=23)/("X"*480)], iface="ens786f0")


Test case 3: ICE_FDIR_MAC/IPv4/UDP/VXLAN/MAC/IPv4/PAY
-----------------------------------------------------
pattern::

    MAC/IPv4/UDP/VXLAN/MAC/IPv4/PAY

inputset::

    inner IP src/dst

rule::

    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000460000000000110000C0A80014C0A80015000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions queue index 1 / mark id 10 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000460000000000110000C0A80014C0A80015000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues 0 1 2 3 end / mark id 4 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000460000000000110000C0A80014C0A80015000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000460000000000110000C0A80014C0A80015000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions drop / end

matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/Raw('x' * 80)],iface="ens786f0")

mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.1.21")/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.1.20",dst="192.168.0.21")/Raw('x' * 80)],iface="ens786f0")


Test case 4: ICE_FDIR_MAC/IPv4/UDP/VXLAN/MAC/IPv4/UDP
-----------------------------------------------------
pattern::

    MAC/IPv4/UDP/VXLAN/MAC/IPv4/UDP

inputset::

    inner IP src/dst

rule::

    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500004E00000000001100000101010102020202000012B5003A0000080000000000000000000000000100000000000208004500001C0000000000110000C0A80014C0A800150000000000080000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions queue index 1 / mark id 10 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500004E00000000001100000101010102020202000012B5003A0000080000000000000000000000000100000000000208004500001C0000000000110000C0A80014C0A800150000000000080000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500004E00000000001100000101010102020202000012B5003A0000080000000000000000000000000100000000000208004500001C0000000000110000C0A80014C0A800150000000000080000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500004E00000000001100000101010102020202000012B5003A0000080000000000000000000000000100000000000208004500001C0000000000110000C0A80014C0A800150000000000080000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions drop / end

matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/("X"*480)], iface="ens786f0")

mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.10.20",dst="192.168.0.21")/UDP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.10.21")/UDP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/TCP()/("X"*480)], iface="ens786f0")


Test case 5: ICE_FDIR_MAC/IPv4/UDP/VXLAN/MAC/IPv4_vni
-----------------------------------------------------
pattern::

    MAC/IPv4/UDP/VXLAN/MAC/IPv4

inputset::

    vni

rule::

    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000003000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F0000000000000000000000000000000000000000000000000000000000000000000000 / end actions queue index 1 / mark id 10 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000003000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F0000000000000000000000000000000000000000000000000000000000000000000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000003000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F0000000000000000000000000000000000000000000000000000000000000000000000 / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000003000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F0000000000000000000000000000000000000000000000000000000000000000000000 / end actions drop / end

matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.10.20",dst="192.168.0.21")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.20",dst="192.168.10.21")/("X"*480)], iface="ens786f0")

mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=13)/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)], iface="ens786f0")


Test case 6: ICE_FDIR_MAC/IPV4/UDP/GTPU/IPV4
--------------------------------------------
pattern::

    MAC/IPV4/UDP/GTPU/IPV4

inputset::

    outer IP src/dst, inner IP src/dst

rule::

    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000380000000000110000C0A80014C0A80015000008680024000030FF001400000000450000140000000000000000C0A80A14C0A80A15 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions queue index 1 / mark id 10 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000380000000000110000C0A80014C0A80015000008680024000030FF001400000000450000140000000000000000C0A80A14C0A80A15 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues 0 1 2 3 end / mark id 4 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000380000000000110000C0A80014C0A80015000008680024000030FF001400000000450000140000000000000000C0A80A14C0A80A15 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000380000000000110000C0A80014C0A80015000008680024000030FF001400000000450000140000000000000000C0A80A14C0A80A15 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions drop / end

matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw('x'*20)], iface="ens786f0")

mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.30", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.30", dst="192.168.10.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.31")/Raw('x'*20)], iface="ens786f0")


Test case 7: ICE_FDIR_MAC/IPV4/UDP/GTPU/IPV6/UDP
------------------------------------------------
pattern::

    MAC/IPV4/UDP/GTPU/IPV6/UDP

inputset::

    outer IP src/dst, inner IP src/dst

rule::

    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000540000000000110000C0A80014C0A80015000008680040000030FF0030000000006000000000081100CDCD910A222254988475111139001010CDCD910A2222549884751111390020210000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000000000000000 / end actions queue index 1 / mark id 10 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000540000000000110000C0A80014C0A80015000008680040000030FF0030000000006000000000081100CDCD910A222254988475111139001010CDCD910A2222549884751111390020210000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000000000000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000540000000000110000C0A80014C0A80015000008680040000030FF0030000000006000000000081100CDCD910A222254988475111139001010CDCD910A2222549884751111390020210000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000000000000000 / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000540000000000110000C0A80014C0A80015000008680040000030FF0030000000006000000000081100CDCD910A222254988475111139001010CDCD910A2222549884751111390020210000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000000000000000 / end actions drop / end

matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw('x'*20)], iface="ens786f0")

mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.10.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1011", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP()/Raw('x'*20)], iface="ens786f0")


Test case 8: ICE_FDIR_MAC/IPV6/UDP/GTPU/DL/IPV4
-----------------------------------------------
pattern::

    MAC/IPV6/UDP/GTPU/DL/IPV4

inputset::

    outer IP src/dst, inner IP src/dst

rules::

    flow create 0 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000281100CDCD910A222254988475111139001010CDCD910A222254988475111139002021000008680028000034FF001C000000000000008501000000450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions queue index 1 / mark id 10 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000281100CDCD910A222254988475111139001010CDCD910A222254988475111139002021000008680028000034FF001C000000000000008501000000450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues 0 1 2 3 end / mark id 4 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000281100CDCD910A222254988475111139001010CDCD910A222254988475111139002021000008680028000034FF001C000000000000008501000000450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000281100CDCD910A222254988475111139001010CDCD910A222254988475111139002021000008680028000034FF001C000000000000008501000000450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions drop / end

matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)], iface="ens786f0")

mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1011", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.20", dst="192.168.0.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20", dst="192.168.10.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)], iface="ens786f0")


Test case 9: ICE_FDIR_MAC/IPV4/UDP/GTPU/UL/IPV4
-----------------------------------------------
pattern::

    MAC/IPV4/UDP/GTPU/UL/IPV4

inputset::

    outer IP src/dst, inner IP src/dst

rule::

    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500003C0000000000110000C0A80014C0A80015000008680028000034FF001C000000000000008501100000450000140000000000000000C0A80114C0A80115 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F00000000000000000000000000000FFFFFFFFFFFFFFFF / end actions queue index 1 / mark id 10 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500003C0000000000110000C0A80014C0A80015000008680028000034FF001C000000000000008501100000450000140000000000000000C0A80114C0A80115 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F00000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues 0 1 2 3 end / mark id 4 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500003C0000000000110000C0A80014C0A80015000008680028000034FF001C000000000000008501100000450000140000000000000000C0A80114C0A80115 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F00000000000000000000000000000FFFFFFFFFFFFFFFF / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000208004500003C0000000000110000C0A80014C0A80015000008680028000034FF001C000000000000008501100000450000140000000000000000C0A80114C0A80115 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F00000000000000000000000000000FFFFFFFFFFFFFFFF / end actions drop / end

matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw('x'*20)], iface="ens786f0")

mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.10.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.11.20", dst="192.168.1.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.11.21")/Raw('x'*20)], iface="ens786f0")


Test case 10: ICE_FDIR_MAC/IPV4/UDP/GTPU/DL/IPV6
------------------------------------------------
pattern::

    MAC/IPV4/UDP/GTPU/DL/IPV6

inputset::

    outer IP src/dst, inner IP src/dst

rule::

    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF00300000000000000085010000006000000000000000CDCD910A222254988475111140001010CDCD910A222254988475111140002021 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF / end actions queue index 1 / mark id 10 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF00300000000000000085010000006000000000000000CDCD910A222254988475111140001010CDCD910A222254988475111140002021 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF / end actions rss queues 0 1 2 3 end / mark id 4 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF00300000000000000085010000006000000000000000CDCD910A222254988475111140001010CDCD910A222254988475111140002021 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF00300000000000000085010000006000000000000000CDCD910A222254988475111140001010CDCD910A222254988475111140002021 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF / end actions drop / end

matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1010", dst="CDCD:910A:2222:5498:8475:1111:4000:2021")/Raw('x'*20)], iface="ens786f0")

mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1010", dst="CDCD:910A:2222:5498:8475:1111:4000:2021")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1010", dst="CDCD:910A:2222:5498:8475:1111:4000:2021")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.10.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1010", dst="CDCD:910A:2222:5498:8475:1111:4000:2021")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1011", dst="CDCD:910A:2222:5498:8475:1111:4000:2021")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1010", dst="CDCD:910A:2222:5498:8475:1111:4000:2022")/Raw('x'*20)], iface="ens786f0")


Test case 11: ICE_FDIR_MAC/IPV4/UDP/GTPU/UL/IPV4/TCP_un-word-aligned key
------------------------------------------------------------------------
pattern::

    MAC/IPV4/UDP/GTPU/UL/IPV4/TCP

inputset::

    the second field of outer IP src , the third field of inner IP dst

rule::

    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF0030000000000000008501100000450000280000000000060000C0A80114C0A801150000000000000000000000005000000000000000 pattern mask 000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000 / end actions queue index 1 / mark id 10 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF0030000000000000008501100000450000280000000000060000C0A80114C0A801150000000000000000000000005000000000000000 pattern mask 000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF0030000000000000008501100000450000280000000000060000C0A80114C0A801150000000000000000000000005000000000000000 pattern mask 000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000 / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF0030000000000000008501100000450000280000000000060000C0A80114C0A801150000000000000000000000005000000000000000 pattern mask 000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000 / end actions drop / end

matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw('x'*20)], iface="ens786f0")

mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.16.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.10.21")/TCP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw('x'*20)], iface="ens786f0")


Test case 12: ICE_FDIR_multi-rules_MAC/IPv6/UDP/VXLAN/IPv4
----------------------------------------------------------
1. relaunch testpmd, create 2 rules, same pattern(MAC/IPv6/UDP/VXLAN/IP), different inputset(inner IP src, inner IP dst), different actions::

    flow create 0 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000241100CDCD910A222254988475111139001010CDCD910A222254988475111139002020000012B5002400000800000000000000450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions queue index 4 / mark id 11 / end
    flow create 0 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000241100CDCD910A222254988475111139001010CDCD910A222254988475111139002020000012B5002400000800000000000000450000140000000000000000C0A80014C0A80015 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions queue index 1 / mark id 1 / end

2. send matched packet, check the first rule can work, the second rule can't work::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)], iface="ens786f0")