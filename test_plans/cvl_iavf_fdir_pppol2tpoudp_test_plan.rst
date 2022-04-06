.. Copyright (c) <2022>, Intel Corporation
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

=================================
CVL IAVF: FDIR For PPPoL2TPv2oUDP
=================================

Description
===========

Support IAVF PPPoL2TPv2oUDP FDIR.
Required to distribute packets based on MAC src, L2TP session ID, inner IP src+dest address and TCP/UDP src+dest port.

Prerequisites
=============

Topology
--------
1node/1nic/2port/fwd
2node/1nic/1port/loopback

Hardware
--------
Supportted NICs: columbiaville_25g/columbiaville_100g

Software
--------
dpdk: http://dpdk.org/git/dpdk
scapy: http://www.secdev.org/projects/scapy/

General set up
--------------
1. Copy specific ice package to /lib/firmware/updates/intel/ice/ddp/ice.pkg,
   then load driver::

    # cp <ice package> /lib/firmware/updates/intel/ice/ddp/ice.pkg
    # rmmod ice
    # insmod <ice build dir>/ice.ko

2. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110

3. Get the pci device id and interface of DUT and tester. 
   For example, 0000:3b:00.0 and 0000:af:00.0 is pci device id,
   ens785f0 and ens260f0 is interface::

    <dpdk dir># ./usertools/dpdk-devbind.py -s

     0000:3b:00.0 'Ethernet Controller E810-C for SFP 1593' if=ens785f0 drv=ice unused=vfio-pci
     0000:af:00.0 'Ethernet Controller XXV710 for 25GbE SFP28 158b' if=ens260f0 drv=i40e unused=vfio-pci

4. Generate 1 VF on PF0, set mac address for this VF::

    # echo 1 > /sys/bus/pci/devices/0000:3b:00.0/sriov_numvfs
    # ip link set ens785f0 vf 0 mac 00:11:22:33:44:55

5. Bind the DUT port to dpdk::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>

6. Launch the userland ``testpmd`` application on DUT as follows and ::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -- -i --rxq=<queue number> --txq=<queue number>
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> show port info all
    testpmd> start

..note::

    For <EAL options>, you can use "-l 1,2,3,4 -n 4", you can also refer to testpmd doc for other setings.

Test Case
=========

Common Steps
------------
1. validate rules.
2. create rules and list rules.
3. send matched packets, check the action hiting the rule.
4. send mismatched packets, check the packets will not hit any rules.
5. destroy rule, list rules.
6. send matched packets, check the packets will not hit any rules.

All the packets in this test plan use below settings:
src mac: 11:22:33:44:55:77
src mac change inputset: 00:00:00:00:00:01
session_id: 0x1111
session_id change inputset: 0x2222
ipv4 src: 10.0.0.11
ipv4 dst: 10.0.0.22
ipv4 src change inputset: 10.0.0.10
ipv4 dst change inputset: 10.0.0.20
ipv6 src: ABAB:910B:6666:3457:8295:3333:1800:2929
ipv6 dst: CDCD:910A:2222:5498:8475:1111:3900:2020
ipv6 src change inputset: ABAB:910B:6666:3457:8295:3333:1800:2920
ipv6 dst change inputset: CDCD:910A:2222:5498:8475:1111:3900:2022
dport: 1701
offset: 6
sport: 11
sport change inputset: 10
dport: 22
dport change inputset: 20

Test case 1: MAC_IPV4_L2TPV2_CONTROL
------------------------------------
This case is designed to check distribute MAC IPv4 L2TPV2 control packets based on MAC src and L2TP session ID as input set.

Subcase 1: l2tpv2_session_id_MAC_IPV4_L2TPV2_CONTROL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type control session_id is <session_id> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")

Subcase 2: eth_l2_src_only_MAC_IPV4_L2TPV2_CONTROL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv4 / udp / l2tpv2 type control / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id change inputset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")

Test case 2: MAC_IPV6_L2TPV2_CONTROL
------------------------------------
This case is designed to check distribute MAC IPv6 L2TPV2 control packets based on MAC src and L2TP session ID as input set.

Subcase 1: l2tpv2_session_id_MAC_IPV6_L2TPV2_CONTROL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type control session_id is 0x1111 / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")

Subcase 2: eth_l2_src_only_MAC_IPV6_L2TPV2_CONTROL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv6 / udp / l2tpv2 type control / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id change inputset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0xc80,len=12,session_id=<session_id>)], iface="<tester interface>")

Test case 3: MAC_IPV4_L2TPV2
----------------------------
This case is designed to check distribute MAC IPv4 L2TPV2 data packets based on MAC src and L2TP session ID as input set.

Subcase 1: l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data session_id is <session_id> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")

Subcase 2: eth_l2_src_only_MAC_IPV4_L2TPV2_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv4 / udp / l2tpv2 type data / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id change inputset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")

Subcase 3: l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l session_id is <session_id> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>)], iface="<tester interface>")

Subcase 4: eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv4 / udp / l2tpv2 type data_l / end actions queue index 3/ end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id change inputset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>)], iface="<tester interface>")

Subcase 5: l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s session_id is 0x1111 / end actions passthru / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")
 
Subcase 6: eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv4 / udp / l2tpv2 type data_s / end actions queue index 6 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id change inputset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")

Subcase 7: l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o session_id is <session_id> offset_size is <offset> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id change inputset>,offset=<offset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")

Subcase 8: eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv4 / udp / l2tpv2 type data_o offset_size is <offset> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id change inputset>,offset=<offset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")

Subcase 9: l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s session_id is 0x1111 / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")

Subcase 10: eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv4 / udp / l2tpv2 type data_l_s / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id change inputset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")
 
Test case 4: MAC_IPV6_L2TPV2 
----------------------------
This case is designed to check distribute MAC IPv6 L2TPV2 data packets based on MAC src and L2TP session ID as input set.

Subcase 1: l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data session_id is 0x1111 / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")

Subcase 2: eth_l2_src_only_MAC_IPV6_L2TPV2_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv6 / udp / l2tpv2 type data / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id change inputset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)], iface="<tester interface>")

Subcase 3: l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l session_id is <session_id> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>)], iface="<tester interface>")

Subcase 4: eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv6 / udp / l2tpv2 type data_l / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id change inputset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=8,session_id=<session_id>)], iface="<tester interface>")

Subcase 5: l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s session_id is <session_id> / end actions mark id 1 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")

Subcase 6: eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv6 / udp / l2tpv2 type data_s / end actions queue index 6 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id change inputset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)], iface="<tester interface>")

Subcase 7: l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o session_id is <session_id> offset_size is <offset> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")
 
mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id change inputset>,offset=<offset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")

Subcase 8: eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv6 / udp / l2tpv2 type data_o offset_size is <offset> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id change inputset>,offset=<offset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)], iface="<tester interface>")

Subcase 9: l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s session_id is <session_id> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")

Subcase 10: eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv6 / udp / l2tpv2 type data_l_s / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id change inputset>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=12,session_id=<session_id>)], iface="<tester interface>")

Test case 5: MAC_IPV4_PPPoL2TPV2 
--------------------------------
This case is designed to check distribute MAC IPv4 PPPoL2TPV2 data packets based on MAC src and L2TP session ID as input set.

Subcase 1: l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data session_id is <session_id> / ppp / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 2: eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv4 / udp / l2tpv2 type data / ppp / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 3: l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l session_id is <session_id> / ppp / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 4: eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv4 / udp / l2tpv2 type data_l / ppp / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 5: l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s session_id is <session_id> / ppp / end actions passthru / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 6: eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv4 / udp / l2tpv2 type data_s / ppp / end actions queue index 6/ end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 7: l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o session_id is <session_id> offset_size is <offset> / ppp / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id change inputset>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 8: eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv4 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id change inputset>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 9: l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s session_id is <session_id> / ppp / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 10: eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv4 / udp / l2tpv2 type data_l_s / ppp / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Test case 6: MAC_IPV6_PPPoL2TPV2 
--------------------------------
This case is designed to check distribute MAC IPv6 PPPoL2TPV2 data packets based on MAC src and L2TP session ID as input set.

Subcase 1: l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data session_id is <session_id> / ppp / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 2: eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv6 / udp / l2tpv2 type data / ppp / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 3: l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l session_id is <session_id> / ppp / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 4: eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv6 / udp / l2tpv2 type data_l / ppp / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=12,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 5: l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s session_id is <session_id> / ppp / end actions mark id 1 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 6: eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv6 / udp / l2tpv2 type data_s / ppp / end actions queue index 6 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 7: l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o session_id is <session_id> offset_size is <offset> / ppp / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id change inputset>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 8: eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

     testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv6 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id change inputset>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,session_id=<session_id>,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 9: l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s session_id is <session_id> / ppp / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Subcase 10: eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth src is <src mac change inputset> / ipv6 / udp / l2tpv2 type data_l_s / ppp / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id change inputset>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=16,session_id=<session_id>)/HDLC()/Raw(b"\\x00\\x00")], iface="<tester interface>")

Test case 7: MAC_IPV4_PPPoL2TPV2_IPV4_PAY
-----------------------------------------
This case is designed to check distribute MAC IPv4 PPPoL2TPV2 IPv4 data packets based on inner IP src+dest address as input set.

Subcase 1: ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_PAY_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

Subcase 2: ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_PAY_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

Subcase 3: ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_PAY_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/iIP(src="<ipv4 src>",dst="<ipv4 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

Subcase 4: ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_PAY_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

Subcase 5: ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_PAY_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

Test case 8: MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY
---------------------------------------------
This case is designed to check distribute MAC IPv4 PPPoL2TPV2 IPv4 UDP data packets based on IP src+dest address and inner UDP src+dest port as input set.

Subcase 1: ipv4_udp_MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv4 src is <ipv4 src> / udp src is <inner sport> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(sport=<inner sport>)], iface="<tester interface>")

Subcase 2: ipv4_udp_MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv4 src is <ipv4 src> / udp dst is <inner dport> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Subcase 3: ipv4_udp_MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv4 dst is <ipv4 dst> / udp src is <inner sport> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst change inputset>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

Subcase 4: ipv4_udp_MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv4 dst is <ipv4 dst> / udp dst is <inner dport> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Subcase 5: ipv4_udp_MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv4 src is <ipv4 src> / udp dst is <inner dport> / end actions drop / end

matched packets::

  >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")
  >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

  >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
  >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
  >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Test case 9: MAC_IPV4_PPPoL2TPV2_IPV4_TCP 
-----------------------------------------
This case is designed to check distribute MAC IPv4 PPPoL2TPV2 IPv4 TCP data packets based on IP src+dest address and inner TCP src+dest port as input set.

Subcase 1: ipv4_tcp_MAC_IPV4_PPPoL2TPV2_IPV4_TCP_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv4 src is <ipv4 src> / tcp src is <inner sport> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(sport=<inner sport>)], iface="<tester interface>")

Subcase 2: ipv4_tcp_MAC_IPV4_PPPoL2TPV2_IPV4_TCP_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv4 src is <ipv4 src> / tcp dst is <inner dport> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

Subcase 3: ipv4_tcp_MAC_IPV4_PPPoL2TPV2_IPV4_TCP_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv4 dst is <ipv4 dst> / tcp src is <inner sport> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst change inputset>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

Subcase 4: ipv4_tcp_MAC_IPV4_PPPoL2TPV2_IPV4_TCP_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv4 dst is <ipv4 dst> / tcp dst is <inner dport> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst change inputset>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(dport=<inner dport>)], iface="<tester interface>")

Subcase 5: ipv4_tcp_MAC_IPV4_PPPoL2TPV2_IPV4_TCP_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv4 src is <ipv4 src> / tcp dst is <inner dport> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

Test case 10: MAC_IPV4_PPPoL2TPV2_IPV6_PAY
------------------------------------------
This case is designed to check distribute MAC IPv4 PPPoL2TPV2 IPv6 data packets based on IP src+dest address as input set.

Subcase 1: ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_PAY_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv6 src is <ipv6 src> dst is <ipv6 dst> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

Subcase 2: ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_PAY_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv6 src is <ipv6 src> dst is <ipv6 dst> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

Subcase 3: ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_PAY_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv6 src is <ipv6 src> dst is <ipv6 dst> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

Subcase 4: ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_PAY_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv6 src is <ipv6 src>9 dst is <ipv6 dst> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

Subcase 5: ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_PAY_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv6 src is <ipv6 src> dst is <ipv6 dst> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

Test case 11: MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY
----------------------------------------------
This case is designed to check distribute MAC IPv4 PPPoL2TPV2 IPv6 data packets based on IP src+dest address and inner UDP src+dest port as input set.

Subcase 1: ipv6_udp_MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv6 dst is <ipv6 dst> / udp src is <inner sport> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst change inputset>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

Subcase 2: ipv6_udp_MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv6 src is <ipv6 src> / udp dst is <inner dport> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Subcase 3: ipv6_udp_MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv6 dst is <ipv6 dst> / udp src is <inner sport> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst change inputset>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

Subcase 4: ipv6_udp_MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv6 src is <ipv6 src> / udp dst is <inner dport> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Subcase 5: ipv6_udp_MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv6 dst is <ipv6 dst> / udp dst is <inner dport> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Test case 12: MAC_IPV4_PPPoL2TPV2_IPV6_TCP
------------------------------------------
This case is designed to check distribute MAC IPv4 PPPoL2TPV2 IPv6 data packets based on IP src+dest address and inner TCP src+dest port as input set.

Subcase 1: ipv6_tcp_MAC_IPV4_PPPoL2TPV2_IPV6_TCP_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv6 dst is <ipv6 dst> / tcp src is <inner sport> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst change inputset>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

Subcase 2: ipv6_tcp_MAC_IPV4_PPPoL2TPV2_IPV6_TCP_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv6 src is <ipv6 src> / tcp dst is <inner dport> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=72)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=72)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=72)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=72)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=72)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

Subcase 3: ipv6_tcp_MAC_IPV4_PPPoL2TPV2_IPV6_TCP_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv6 dst is <ipv6 dst> / tcp src is <inner sport> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst change inputset>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

Subcase 4: ipv6_tcp_MAC_IPV4_PPPoL2TPV2_IPV6_TCP_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv6 src is <ipv6 src> / tcp dst is <inner dport> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

Subcase 5: ipv6_tcp_MAC_IPV4_PPPoL2TPV2_IPV6_TCP_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv6 src is <ipv6 src> / tcp src is <inner sport> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(sport=<inner sport>)], iface="<tester interface>")

Test case 13: MAC_IPV6_PPPoL2TPV2_IPV4_PAY
------------------------------------------
This case is designed to check distribute MAC IPv6 PPPoL2TPV2 IPv4 data packets based on IP src+dest address as input set.

Subcase 1: ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_PAY_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

Subcase 2: ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_PAY_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

Subcase 3: ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_PAY_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

Subcase 4: ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_PAY_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

Subcase 5: ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_PAY_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>",dst="<ipv4 dst>")], iface="<tester interface>")

Test case 14: MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
----------------------------------------------
This case is designed to check distribute MAC IPv6 PPPoL2TPV2 IPv4 UDP data packets based on IP src+dest address and inner UDP src+dest port as input set.

Subcase 1: ipv4_udp_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv4 src is <ipv4 src> / udp dst is <inner dport> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Subcase 2: ipv4_udp_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv4 dst is <ipv4 dst> / udp src is <inner sport> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst change inputset>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

Subcase 3: ipv4_udp_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv4 src is <ipv4 src> / udp dst is <inner dport> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Subcase 4: ipv4_udp_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv4 dst is <ipv4 dst> / udp src is <inner sport> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")
  >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

  >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport change inputset>)], iface="<tester interface>")
  >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst change inputset>")/UDP(sport=<inner sport>)], iface="<tester interface>")
  >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

Subcase 5: ipv4_udp_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv4 dst is <ipv4 dst> / udp dst is <inner dport> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Test case 15: MAC_IPV6_PPPoL2TPV2_IPV4_TCP
------------------------------------------
This case is designed to check distribute MAC IPv6 PPPoL2TPV2 IPv4 TCP data packets based on IP src+dest address and inner TCP src+dest port as input set.

Subcase 1: ipv4_tcp_MAC_IPV6_PPPoL2TPV2_IPV4_TCP_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv4 src is <ipv4 src> / tcp dst is <inner dport> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

Subcase 2: ipv4_tcp_MAC_IPV6_PPPoL2TPV2_IPV4_TCP_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv4 dst is <ipv4 dst> / tcp src is <inner sport> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst change inputset>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

Subcase 3: ipv4_tcp_MAC_IPV6_PPPoL2TPV2_IPV4_TCP_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv4 src is <ipv4 src> / tcp dst is <inner dport> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

  >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport change inputset>)], iface="<tester interface>")
  >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src change inputset>")/TCP(dport=<inner dport>)], iface="<tester interface>")
  >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="<ipv4 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

Subcase 4: ipv4_tcp_MAC_IPV6_PPPoL2TPV2_IPV4_TCP_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv4 dst is <ipv4 dst> / tcp src is <inner sport> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst change inputset>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

Subcase 5: ipv4_tcp_MAC_IPV6_PPPoL2TPV2_IPV4_TCP_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv4 dst is <ipv4 dst> / tcp dst is <inner dport> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst change inputset>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="<ipv4 dst>")/TCP(dport=<inner dport>)], iface="<tester interface>")

Test case 16: MAC_IPV6_PPPoL2TPV2_IPV6_PAY
------------------------------------------
This case is designed to check distribute MAC IPv6 PPPoL2TPV2 IPv6 data packets based on IP src+dest address as input set.

Subcase 1: ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_PAY_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv6 src is <ipv6 src> dst is <ipv6 dst> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>7")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

Subcase 2: ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_PAY_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv6 src is <ipv6 src> dst is <ipv6 dst> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

Subcase 3: ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_PAY_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv6 src is <ipv6 src> dst is <ipv6 dst> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

Subcase 4: ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_PAY_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv6 src <ipv6 src> dst is <ipv6 dst> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
 
mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
 
Subcase 5: ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_PAY_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv6 src is <ipv6 src> dst is <ipv6 dst> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>",dst="<ipv6 dst>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst change inputset>")], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")], iface="<tester interface>")

Test case 17: MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
----------------------------------------------
This case is designed to check distribute MAC IPv6 PPPoL2TPV2 IPv6 UDP data packets based on IP src+dest address and inner UDP src+dest port as input set.

Subcase 1: ipv6_udp_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv6 dst is <ipv6 dst> / udp src is <inner sport> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst change inputset>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

Subcase 2: ipv6_udp_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv6 src is <ipv6 src> / udp dst is <inner dport> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Subcase 3: ipv6_udp_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv6 dst is <ipv6 dst> / udp src is <inner sport> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst change inputset>")/UDP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(sport=<inner sport>)], iface="<tester interface>")

Subcase 4: ipv6_udp_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv6 src is <ipv6 src> / udp dst is <inner dport> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Subcase 5: ipv6_udp_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv6 dst is <ipv6 dst> / udp dst is <inner dport> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst change inputset>")/UDP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/UDP(dport=<inner dport>)], iface="<tester interface>")

Test case 18: MAC_IPV6_PPPoL2TPV2_IPV6_TCP
------------------------------------------
This case is designed to check distribute MAC IPv6 PPPoL2TPV2 IPv6 TCP data packets based on IP src+dest address and inner TCP src+dest port as input set.

Subcase 1: ipv6_tcp_MAC_IPV6_PPPoL2TPV2_IPV6_TCP_DATA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv6 dst is <ipv6 dst> / tcp src is <inner sport> / end actions queue index 3 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst change inputset>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

Subcase 2: ipv6_tcp_MAC_IPV6_PPPoL2TPV2_IPV6_TCP_DATA_L
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv6 src is <ipv6 src> / tcp dst is <inner dport> / end actions queue index 5 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=72)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=72)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=72)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=72)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x400,len=72)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")

Subcase 3: ipv6_tcp_MAC_IPV6_PPPoL2TPV2_IPV6_TCP_DATA_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv6 dst is <ipv6 dst> / tcp src is <inner sport> / end actions rss queues 2 3 end / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst change inputset>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="<ipv6 dst>")/TCP(sport=<inner sport>)], iface="<tester interface>")

Subcase 4: ipv6_tcp_MAC_IPV6_PPPoL2TPV2_IPV6_TCP_DATA_O
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is <offset> / ppp / ipv6 src is <ipv6 src> / tcp dst is <inner dport> / end actions queue index 2 / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(dport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(sport=<inner dport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(sport=<inner dport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>")/TCP(sport=<inner dport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x020,offset=<offset>)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(sport=<inner dport>)], iface="<tester interface>")

Subcase 5: ipv6_tcp_MAC_IPV6_PPPoL2TPV2_IPV6_TCP_DATA_L_S
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
rules::

    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv6 src is <ipv6 src> / tcp src is <inner sport> / end actions drop / end

matched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac change inputset>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(sport=<inner sport>)], iface="<tester interface>")

mismatched packets::

    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(sport=<inner sport change inputset>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IPv6()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src change inputset>")/TCP(sport=<inner sport>)], iface="<tester interface>")
    >>> sendp([Ether(src="<src mac>")/IP()/UDP(dport=<dport>)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="<ipv6 src>")/TCP(sport=<inner sport>)], iface="<tester interface>")

