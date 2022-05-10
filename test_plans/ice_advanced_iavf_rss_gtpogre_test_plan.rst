.. Copyright (c) <2021>, Intel Corporation
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

===============================
ICE IAVF Support GTPoGRE in RSS
===============================

Description
===========
The GTPoGRE pkt structure is shown below:
.. table::

  +------------+------------+-----------+------------+-----------+-----+------------+----------+--------+
  | MAC header | Eth header | IP Packet | GRE header | IP packet | UDP | GTP header | IP packet| TCP/UDP|
  +------------+------------+-----------+------------+-----------+-----+------------+----------+--------+

As previous(dpdk-21.05) DDP limitation, the outer IP layer of an GTP over GRE packet will be mapped to the outer layer of IP/GTPU/IP packet type,
while customers need the second IP layer.
A new DDP package is required in dpdk-21.08, the new DDP's parser will be able to generate 3 layer's IP protocol header,
so it will not allow a GTP over GRE packet to share the same profile with a normal GTP packet.
And DPDK need to support both RSS and FDIR in Intel® Ethernet 800 Series IAVF.

This test plan is designed to check the RSS of GTPoGRE.
Supported input set: inner most l3/l4 src/dst
Supported function: toeplitz, symmetric


Prerequisites
=============
1. Hardware:
   Intel® Ethernet 800 Series E810-XXVDA4/E810-CQ

2. Software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Copy specific gtpogre(ice_gtp-o-gre-1.3.5.0.pkg) package to /lib/firmware/updates/intel/ice/ddp/ice.pkg,
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

6. Generate 4 VFs on PF0(not all the VFs are used)::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

    ./usertools/dpdk-devbind.py -s
    0000:18:01.0 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v0 drv=iavf unused=vfio-pci
    0000:18:01.1 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v1 drv=iavf unused=vfio-pci
    0000:18:01.2 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v2 drv=iavf unused=vfio-pci
    0000:18:01.3 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v3 drv=iavf unused=vfio-pci

7. Set mac addr for VFs::

    ip link set ens785f0 vf 1 mac 00:11:22:33:44:00
    ip link set ens785f0 vf 1 mac 00:11:22:33:44:11
    ip link set ens785f0 vf 2 mac 00:11:22:33:44:22
    ip link set ens785f0 vf 3 mac 00:11:22:33:44:33

8. Bind VFs to dpdk driver::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0 0000:18:01.1 0000:18:01.2 0000:18:01.3

9. launch testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

10. start scapy and configuration GTP profile in tester
    scapy::

    >>> import sys
    >>> from scapy.contrib.gtp import *


toeplitz cases test steps
=========================
1. validate rules.
2. create rules and list rules.
3. send a basic hit pattern packet,record the hash value.
   check the packet distributed to queue by rss.
4. send hit pattern packets with changed input set in the rule.
   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.
5. send hit pattern packets with changed input set not in the rule.
   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.
6. destroy the rule and list rule. check the flow list has no rule.


symmetric cases test steps
==========================
1. validate rules.
2. create rules and list rules.
3. send a basic hit pattern packet,record the hash value.
4. send a hit pattern packet with switched value of input set in the rule.
   check the received packets have same hash value.
   check both the packets are distributed to queues by rss.
5. destroy the rule and list rule.
6. send the packet in step 4.
   check the received packet has different hash value with which in step 3(including the case has no hash value).


supported pattern and inputset
==============================
.. table::

    +----------------------------------------------------------------------------------------------------------------------------------------------+
    | Hash function: toeplitz                                                                                                                      |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    | combination            | Packet Type                        | All the Input Set options in combination                                       |
    +========================+====================================+================================================================================+
    | IP*+IP*+IP*            | MAC_IP*_GRE_IP*_GTPU_IP*           | ip*, l3-src-only, l3-dst-only                                                  |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_IP*_UDP       | ip*, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ip*-udp               |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_IP*_TCP       | ip*, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ip*-tcp               |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_EH_IP*        | ip*, l3-src-only, l3-dst-only                                                  |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_EH_IP*_UDP    | ip*, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ip*-udp               |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_EH_IP*_TCP    | ip*, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ip*-tcp               |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_UL_IP*        | ip*, l3-src-only, l3-dst-only                                                  |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_UL_IP*_UDP    | ip*, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ip*-udp               |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_UL_IP*_TCP    | ip*, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ip*-tcp               |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_DL_IP*        | ip*, l3-src-only, l3-dst-only                                                  |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_DL_IP*_UDP    | ip*, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ip*-udp               |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_DL_IP*_TCP    | ip*, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ip*-tcp               |
    +------------------------+------------------------------------+--------------------------------------------------------------------------------+

.. table::

    +-------------------------------------------------------------------------------------------------------------+
    | Hash function: symmetric                                                                                    |
    +------------------------+------------------------------------+-----------------------------------------------+
    | combination            | Packet Type                        | All the Input Set options in combination      |
    +========================+====================================+===============================================+
    | IP*+IP*+IP*            | MAC_IP*_GRE_IP*_GTPU_IP*           | ip*                                           |
    +------------------------+------------------------------------+-----------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_IP*_UDP       | ip*-udp                                       |
    +------------------------+------------------------------------+-----------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_IP*_TCP       | ip*-tcp                                       |
    +------------------------+------------------------------------+-----------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_EH_IP*        | ip*                                           |
    +------------------------+------------------------------------+-----------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_EH_IP*_UDP    | ip*-udp                                       |
    +------------------------+------------------------------------+-----------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_EH_IP*_TCP    | ip*-tcp                                       |
    +------------------------+------------------------------------+-----------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_UL_IP*        | ip*                                           |
    +------------------------+------------------------------------+-----------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_UL_IP*_UDP    | ip*-udp                                       |
    +------------------------+------------------------------------+-----------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_UL_IP*_TCP    | ip*-tcp                                       |
    +------------------------+------------------------------------+-----------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_DL_IP*        | ip*                                           |
    +------------------------+------------------------------------+-----------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_DL_IP*_UDP    | ip*-udp                                       |
    +------------------------+------------------------------------+-----------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_DL_IP*_TCP    | ip*-tcp                                       |
    +------------------------+------------------------------------+-----------------------------------------------+

each combination just need to change the IP* and ip* with IPV4/IPV6 and ipv4/ipv6, the inputset is same. there are 8 combinations in total:
1. IPV4+IPV4+IPV4
2. IPV6+IPV4+IPV4
3. IPV4+IPV6+IPV4
4. IPV4+IPV4+IPV6
5. IPV6+IPV6+IPV4
6. IPV4+IPV6+IPV6
7. IPV6+IPV4+IPV6
8. IPV6+IPV6+IPV6


1. toeplitz: IPV4+IPV4+IPV4

MAC_IPV4_GRE_IPV4_GTPU_IPV4
===========================
basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")],iface="ens786f0")

L3SRC
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")],iface="ens786f0")

L3DST
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")],iface="ens786f0")

IPV4
----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.17")],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")],iface="ens786f0")


MAC_IPV4_GRE_IPV4_GTPU_IPV4_UDP
===============================
basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")

L3SRC
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=14)],iface="ens786f0")

L3DST
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=14)],iface="ens786f0")

L4SRC
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=12, sport=4)],iface="ens786f0")

L4DST
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=2, sport=14)],iface="ens786f0")

L3SRC+L4SRC
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=4)],iface="ens786f0")

L3SRC+L4DST
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=14)],iface="ens786f0")

L3DST+L4SRC
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")

L3DST+L4DST
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

IPV4-UDP
--------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")


MAC_IPV4_GRE_IPV4_GTPU_IPV4_TCP
===============================
reconfig all the cases in MAC_IPV4_GRE_IPV4_GTPU_IPV4_UDP:
packets: change the inner most UDP to TCP
rules: change the inner most udp to tcp, ipv4-udp to ipv4-tcp


MAC_IPV4_GRE_IPV4_GTPU_EH_IPV4
==============================
basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")],iface="ens786f0")

L3SRC
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")],iface="ens786f0")

L3DST
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")],iface="ens786f0")

IPV4
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.17")],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")],iface="ens786f0")


MAC_IPV4_GRE_IPV4_GTPU_EH_IPV4_UDP
==================================
basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")

L3SRC
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=14)],iface="ens786f0")

L3DST
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=14)],iface="ens786f0")

L4SRC
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=12, sport=4)],iface="ens786f0")

L4DST
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=2, sport=14)],iface="ens786f0")

L3SRC+L4SRC
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=4)],iface="ens786f0")

L3SRC+L4DST
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=14)],iface="ens786f0")

L3DST+L4SRC
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")

L3DST+L4DST
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

IPV4-UDP
--------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")


MAC_IPV4_GRE_IPV4_GTPU_EH_IPV4_TCP
==================================
reconfig all test cases in MAC_IPV4_GRE_IPV4_GTPU_EH_IPV4_UDP:
packets: change the inner most UDP to TCP
rules: change the inner most udp to tcp, ipv4-udp to ipv4-tcp


MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4
==============================
basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")],iface="ens786f0")

L3SRC
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")],iface="ens786f0")

L3DST
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")],iface="ens786f0")

IPV4
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.17")],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")],iface="ens786f0")


MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4_UDP
==================================
basic packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")

L3SRC
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=14)],iface="ens786f0")

L3DST
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=14)],iface="ens786f0")

L4SRC
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=12, sport=4)],iface="ens786f0")

L4DST
-----
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=2, sport=14)],iface="ens786f0")

L3SRC+L4SRC
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=4)],iface="ens786f0")

L3SRC+L4DST
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=14)],iface="ens786f0")

L3DST+L4SRC
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")

L3DST+L4DST
-----------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

IPV4-UDP
--------
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern and defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=12, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=14)],iface="ens786f0")

hit pattern but not defined input set::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")


MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4_TCP
==================================
reconfig all test cases in MAC_IPV4_GRE_IPV4_GTPU_EH_IPV4_UDP:
packets: change the inner most UDP to TCP
rules: change the inner most udp to tcp, ipv4-udp to ipv4-tcp


MAC_IPV4_GRE_IPV4_GTPU_DL_IPV4
==============================
packets: change the type value(1->0/0->1) of MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4
rule: change the pdu_t value(1->0) of MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4


MAC_IPV4_GRE_IPV4_GTPU_DL_IPV4_UDP
==================================
packets: change the type value(1->0/0->1) of MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4_UDP
rule: change the pdu_t value(1->0) of MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4_UDP


MAC_IPV4_GRE_IPV4_GTPU_DL_IPV4_TCP
==================================
packets: change the type value(1->0/0->1) of MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4_TCP
rule: change the pdu_t value(1->0) of MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4_TCP


2. toeplitz: IPV6+IPV4+IPV4

reconfig all the cases of toeplitz: IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.

3. toeplitz: IPV4+IPV6+IPV4

reconfig all the cases of toeplitz: IPV4+IPV4+IPV4

    packets: change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
    rule: change the inner ipv4 to ipv6.

4. toeplitz: IPV4+IPV4+IPV6

reconfig all the cases of toeplitz: IPV4+IPV4+IPV4

    packets: change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.

5. toeplitz: IPV6+IPV6+IPV4

reconfig all the cases of toeplitz: IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner ipv4 to ipv6.

6. toeplitz: IPV4+IPV6+IPV6

reconfig all the cases of toeplitz: IPV4+IPV4+IPV4

    packets: change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
    rule: change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner ipv4 to ipv6.

7. toeplitz: IPV6+IPV4+IPV6

reconfig all the cases of toeplitz: IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.

8. toeplitz: IPV6+IPV6+IPV6

reconfig all the cases of toeplitz: IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
             change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner ipv4 to ipv6.
          change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.


9. symmetric: IPV4+IPV4+IPV4

MAC_IPV4_GRE_IPV4_GTPU_IPV4
===========================
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.7", dst="1.1.2.6")],iface="ens786f0")


MAC_IPV4_GRE_IPV4_GTPU_EH_IPV4_UDP
==================================
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.7", dst="1.1.2.6")/UDP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=4, sport=2)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.7", dst="1.1.2.6")/UDP(dport=4, sport=2)],iface="ens786f0")


MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4_TCP
==================================
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end

packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/TCP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.7", dst="1.1.2.6")/TCP(dport=2, sport=4)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/TCP(dport=4, sport=2)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.7", dst="1.1.2.6")/TCP(dport=4, sport=2)],iface="ens786f0")


MAC_IPV4_GRE_IPV4_GTPU_DL_IPV4
==============================
rule::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.7", dst="1.1.2.6")],iface="ens786f0")


10. symmetric: IPV6+IPV4+IPV4

reconfig all the cases of symmetric: IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.

11. symmetric: IPV4+IPV6+IPV4

reconfig all the cases of symmetric: IPV4+IPV4+IPV4

    packets: change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
    rule: change the inner ipv4 to ipv6.

12. symmetric: IPV4+IPV4+IPV6

reconfig all the cases of symmetric: IPV4+IPV4+IPV4

    packets: change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.

13. symmetric: IPV6+IPV6+IPV4

reconfig all the cases of symmetric: IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner ipv4 to ipv6.

14. symmetric: IPV4+IPV6+IPV6

reconfig all the cases of symmetric: IPV4+IPV4+IPV4

    packets: change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
    rule: change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner ipv4 to ipv6.

15. symmetric: IPV6+IPV4+IPV6

reconfig all the cases of symmetric: IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.

16. symmetric: IPV6+IPV6+IPV6

reconfig all the cases of symmetric: IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
             change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner ipv4 to ipv6.
          change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.


negative test case
==================
1. create rules and check all the rules fail::

    testpmd> flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv4-udp gtpu end key_len 0 queues end / end
    Bad arguments

    testpmd> flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv6-tcp end key_len 0 queues end / end
    Bad arguments

    testpmd> flow create 0 ingress pattern eth / ipv6 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / end actions rss types ipv4 l4-dst-only end key_len 0 queues end / end
    Bad arguments

    testpmd> flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 l2-src-only end key_len 0 queues end / end
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

    testpmd> flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc is 1 / ipv6 / tcp / end actions rss func symmetric_toeplitz types l3-src-only end key_len 0 queues end / end
    Bad arguments

    testpmd> flow create 0 ingress pattern eth / ipv6 / gre / ipv6 / udp / gtpu / gtp_psc is 1 / ipv4 / end actions rss func symmetric_toeplitz types l4-src-only end key_len 0 queues end / end
    Bad arguments


exclusive test case
===================

subcase 1: without eh rule + with eh rule
-----------------------------------------
when the rule with eh and another rule without eh co-exist, 2 rules do not affect each other.

1. create 1 rule with eh and 1 rule without eh::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

2. send pkts which hit 2 rules separately, check the pkt will hit each rule::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()],iface="ens786f0")

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()],iface="ens786f0")

subcase 2: without l4 rule + with l4 rule
-----------------------------------------
the rule without l4 has a larger coverage than the rule with l4. if user need to create these two rule at the same time.
user should create rule without l4 firstly then create rule with l4.
when 2 rules exist, each pattern hit each rule. destroy l4 rule, l4 pattern hit l3 rule. destroy l3 rule, l3 pattern will not hit l4 rule.

1. create 1 rule with l4 and 1 rule without l4::

    flow create 0 ingress pattern eth / ipv6 / gre / ipv6 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / gre / ipv6 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

2. send pkts which hit 2 rules separately, check the pkt will hit each rule::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")],iface="ens786f0")

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()],iface="ens786f0")

3. destroy l4 rule, repeat step 2, check the l4 pkts will hit l3 rule.

subcase 3: with eh but without ul/dl + ul
-----------------------------------------
when 2 rules exist, each pattern hit each rule. destroy ul rule, ul pattern hit eh rule without ul/dl.

1. create 1 rule with ul and 1 rule without ul/dl::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

2. send pkts which hit 2 rules separately, check the pkt will hit each rule::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()],iface="ens786f0")

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()],iface="ens786f0")

3. destroy ul rule, send pkts in step 2, check the pkt will hit the eh rule without ul/dl.

subcase 4: ipv4/ipv4/ipv4 rule + ipv4/ipv6/ipv4 rule
----------------------------------------------------
currently, the inner ip do not make distinction between ipv4 and ipv6, these two patterns use same profile.
so when create two rules of these two patterns with same input set, the second rule can not be created.

1. create two rules of these two patterns with same input set, check the second rule can not be created::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 13 / mark id 13 / end
    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 3 / end

    testpmd> flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 13 / mark id 13 / end
    Flow rule #0 created
    testpmd> flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 3 / end
    iavf_fdir_add(): Failed to add rule request due to the rule is already existed
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

