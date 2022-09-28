.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation\

====================================================
IAVF enable Protocol agnostic flow offloading in RSS
====================================================

Description
===========
IAVF enable protocol agnostic flow offloading in rss, that means we can use raw packet filter instead of naming filter(legacy flow offloading).
As the raw packet filter using spec and mask to describr pattern and input set,
the protocol agnostic flow offloading is more flexible and customizable compared with legacy flow offloading.
To reduce redundancy, we don't check all the patterns and input set which is covered by naming filter test cases.
this plan only cover below test hints to check the feasibility of protocol agnostic flow offloading:

1. try RSS with regular 5 tuples for any UDP or TCP packet
2. try RSS with VXLAN inner IP match (make sure VXLAN tunnel port has been configured either by DCF or swtichdev)
3. try RSS with GTPU inner IP match
4. try RSS with GTPU outer IP match
5. try RSS with un-word-aligned key

And all the rules are created by packageviewer(ICE parser emulator).
The first string of numbers in the rule represents the matched packet's raw pattern spec,
the second string represents the mask, using 'F' to mask the inputset.
Pls get the tool from Intel DPDK team.
..note::
there will be conflict between raw packet filter and naming filter, so need to disable default rss when testing raw packet filter.

Prerequisites
=============

Hardware
--------
Supportted NICs: columbiaville_25g/columbiaville_100g

Software
--------
DPDK: http://dpdk.org/git/dpdk
Scapy: http://www.secdev.org/projects/scapy/

General Set Up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110

2. Generate 2 VF from PF(0000:18:00.0 here), ::

    # echo 2 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs

3. Get the pci device id and interface of DUT and tester::

    <dpdk dir># ./usertools/dpdk-devbind.py -s

    0000:18:01.0 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v0 drv=iavf unused=vfio-pci
    0000:18:01.1 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v1 drv=iavf unused=vfio-pci

4. set VF0 trust on::

    # ip link set ens785f0 vf 0 trust on

5. set mac address for VF1::

    # ip link set ens785f0 vf 1 mac 00:11:22:33:44:55

6. Bind the DUT port to dpdk::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>

7. Launch the userland ``testpmd`` application on DUT as follows and ::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 0000:18:01.0,cap=dcf -a 0000:18:01.1 -- -i --rxq=<queue number> --txq=<queue number>
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> port config 0 udp_tunnel_port add vxlan 0x12b5
    testpmd> start

..note:: 

    For <EAL options>, you can use "-c 0xf -n 1", you can also refer to testpmd doc for other setings.

8. Import layers when start scapy::

    >>> import sys
    >>> from scapy.contrib.gtp import *


Test Case
=========
common steps
------------
toeplitz cases
1. validate rules.
2. create rules and list rules.
3. send a basic hit pattern packet,record the hash value, check the packet distributed to queue by rss
4. send hit pattern packets with changed input set in the rule, check the received packets have different hash value with basic packet,
check all the packets are distributed to queues by rss
5. send hit pattern packets with changed input set not in the rule, check the received packet have same hash value with the basic packet,
check all the packets are distributed to queues by rss

..note:: 
    if there is not this type packet in the case, omit this step.

6. destroy the rule and list rule. check the flow list has no rule.

symmetric cases
1. validate rules.
2. create rules and list rules.
3. send a basic hit pattern packet,record the hash value.
4. send a hit pattern packet with switched value of input set in the rule, check the received packets have same hash value,
check both the packets are distributed to queues by rss
5. destroy the rule and list rule.
6. send the packet in step 4, check the received packet has different hash value with which in step 3(including the case has no hash value).

Test case 1: VF_RSS_MAC/IPv4/UDP
--------------------------------
pattern::

    MAC/IPv4/UDP

inputset::

    IP src/dst, UDP sport/dport

rule::

    flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500001C0000000000110000C0A80014C0A800150016001700080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF00000000 / end actions rss queues end / end

basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="ens786f0")

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20",dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.10.21")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=32,dport=23)/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=33)/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="ens786f0")


Test case 2: VF_RSS_MAC/IPv6/TCP_sysmetric
------------------------------------------
pattern::

    MAC/IPv6/TCP

inputset::

    IP src/dst, TCP sport/dport

rule::

    flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000140600CDCD910A222254988475111139001010CDCD910A2222549884751111390020200016001700000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions rss func symmetric_toeplitz queues end / end

packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=22,dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=23,dport=22)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:1010", src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:1010", src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=23,dport=22)/("X"*480)], iface="ens786f0")


Test case 3: VF_RSS_MAC/IPv4/UDP/VXLAN/MAC/IPv4/PAY
---------------------------------------------------
pattern::

    MAC/IPv4/UDP/VXLAN/MAC/IPv4/PAY

inputset::

    inner IP src/dst

rule::

    flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000003000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues end / end

basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/Raw('x' * 80)],iface="ens786f0")

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.10.20",dst="192.168.0.21")/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.10.21")/Raw('x' * 80)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=33)/IP(src="192.168.0.20",dst="192.168.0.21")/Raw('x' * 80)],iface="ens786f0")


Test case 4: VF_RSS_MAC/IPv4/UDP/VXLAN/MAC/IPv4/UDP
---------------------------------------------------
pattern::

    MAC/IPv4/UDP/VXLAN/MAC/IPv4/UDP

inputset::

    inner IP src/dst

rule::

    flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004E00000000001100000101010102020202000012B5003A0000080000000000000000000000000100000000000208004500001C0000000000110000C0A80014C0A800150000000000080000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions rss queues end / end

basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/("X"*480)], iface="ens786f0")

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.10.20",dst="192.168.0.21")/UDP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.10.21")/UDP()/("X"*480)], iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=33)/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/("X"*480)], iface="ens786f0")


Test case 5: VF_RSS_MAC/IPv4/UDP/VXLAN/MAC/IPv4_sysmetric
---------------------------------------------------------
pattern::

    MAC/IPv4/UDP/VXLAN/MAC/IPv4

inputset::

    inner IP src/dst

rule::

    flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss func symmetric_toeplitz queues end / end

packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/Raw('x' * 80)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.21",dst="192.168.0.20")/Raw('x' * 80)],iface="ens786f0")


Test case 6: VF_RSS_IPv4/UDP/VXLAN/MAC/IPv4_inner-l3-src-only
-------------------------------------------------------------
pattern::

    MAC/IPv4/UDP/VXLAN/MAC/IPv4

inputset::

    inner-l3-src-only

rule::

    flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFF00000000 / end actions rss queues end / end

basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)], iface="ens786f0")

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.10.20",dst="192.168.0.21")/("X"*480)], iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.10.21")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=22)/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)], iface="ens786f0")


Test case 7: VF_RSS_MAC/IPV4/UDP/GTPU/IPV4
------------------------------------------
pattern::

    MAC/IPV4/UDP/GTPU/IPV4

inputset::

    outer IP src/dst, inner IP src/dst

rule::

    flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000380000000000110000C0A80014C0A80015000008680024000030FF001400000000450000140000000000000000C0A80A14C0A80A15 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues end / end

basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw('x'*20)], iface="ens786f0")

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.30", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.30", dst="192.168.10.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.31")/Raw('x'*20)], iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x567)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw('x'*20)], iface="ens786f0")


Test case 8: VF_RSS_MAC/IPV4/UDP/GTPU/IPV6/UDP_outer-l3
-------------------------------------------------------
pattern::

    MAC/IPV4/UDP/GTPU/IPV6/UDP

inputset::

    outer IP src/dst

rule::

    flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000540000000000110000C0A80014C0A80015000008680040000030FF0030000000006000000000081100CDCD910A222254988475111139001010CDCD910A2222549884751111390020210000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 / end actions rss queues end / end

basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw('x'*20)], iface="ens786f0")

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.22", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw('x'*20)], iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1011", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw('x'*20)], iface="ens786f0")


Test case 9: VF_RSS_MAC/IPV4/UDP/GTPU/EH/IPV4/UDP_innersysmetric
----------------------------------------------------------------
pattern::

    MAC/IPV4/UDP/GTPU/EH/IPV4/UDP

inputset::

    inner IP src/dst

rule::

    flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000440000000000110000C0A80014C0A80014000008680030000034FF00240000000000000085010000004500001C0000000000110000C0A80114C0A801150000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions rss func symmetric_toeplitz queues end / end

packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.1.20", dst="192.168.1.21")/UDP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.1.21", dst="192.168.1.20")/UDP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.20")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.1.20", dst="192.168.1.21")/UDP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.20")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.1.21", dst="192.168.1.20")/UDP()/Raw('x'*20)], iface="ens786f0")


Test case 10: VF_RSS_MAC/IPV4/UDP/GTPU/UL/IPV4_inner-l3-dst-only
----------------------------------------------------------------
pattern::

    MAC/IPV4/UDP/GTPU/UL/IPV4

inputset::

    inner-l3-dst-only

rule::

    flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500003C0000000000110000C0A80014C0A80015000008680028000034FF001C000000000000008501100000450000140000000000000000C0A80114C0A80115 pattern mask 000000000000000000000000000000000000000000000000000000000000FFFFFFFF000000000000000000000000000000000000000000F000000000000000000000000000000000000000000000 / end actions rss queues end / end

basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw('x'*20)], iface="ens786f0")

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.10.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw('x'*20)], iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.11.20", dst="192.168.1.21")/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.11.21")/Raw('x'*20)], iface="ens786f0")


Test case 11: VF_RSS_MAC/IPV4/UDP/GTPU/DL/IPV4/TCP_un-word-aligned key
----------------------------------------------------------------------
pattern::

    MAC/IPV4/UDP/GTPU/DL/IPV4/TCP

inputset::

    the first and second field of inner IP src

rule::

    flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF0030000000000000008501000000450000280000000000060000C0A80114C0A801150000000000000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F00000000000000000000000000000FFFF0000000000000000000000000000000000000000000000000000 / end actions rss queues end / end
    
basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw('x'*20)], iface="ens786f0")

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="191.168.1.20", dst="192.168.1.21")/TCP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.161.1.20", dst="192.168.1.21")/TCP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw('x'*20)], iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.10.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.11.20", dst="192.168.1.21")/TCP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.21", dst="192.168.1.21")/TCP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.22")/TCP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.22")/TCP()/Raw('x'*20)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123)/GTPPDUSessionContainer(pdu_type=0, qos_flow=0x12)/IP(src="192.168.1.20", dst="192.168.1.22")/TCP()/Raw('x'*20)], iface="ens786f0")


Test case 12: VF_RSS_multi-rules_MAC/IPv4/UDP/VXLAN/IPv6
--------------------------------------------------------
1. create 2 rules, same pattern(MAC/IPv4/UDP/VXLAN/IPv6), different inputset(inner IP src, dst)::

    flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004C00000000001100000101010102020202000012B50038000008000000000000006000000000000000CDCD910A222254988475111139001010CDCD910A222254988475111139002021 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF / end actions rss queues end / end
    flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004C00000000001100000101010102020202000012B50038000008000000000000006000000000000000CDCD910A222254988475111139001010CDCD910A222254988475111139002021 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions rss queues end / end

2. send basic packet and save hash value::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)], iface="ens786f0")

3. send packets hit rules, check the hash value of first packet is same with basic packet, the second packet is different::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1011", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)], iface="ens786f0")