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

================================
CVL IAVF Support GTPoGRE in FDIR
================================

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
And DPDK need to support both RSS and FDIR in CVL IAVF.

This test plan is designed to check the FDIR of GTPoGRE.
Supported input set: inner most l3/l4 src/dst, outer l3 src/dst, gtpu teid, qfi
Supported action: queue index, rss queues, passthru, drop, mark rss


Prerequisites
=============
1. Hardware:
   columbiaville_25g/columbiaville_100g

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

    ip link set ens785f0 vf 0 mac 00:11:22:33:44:55
    ip link set ens785f0 vf 1 mac 00:11:22:33:44:11
    ip link set ens785f0 vf 2 mac 00:11:22:33:44:22
    ip link set ens785f0 vf 3 mac 00:11:22:33:44:33

8. Bind VFs to dpdk driver::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0 0000:18:01.1 0000:18:01.2 0000:18:01.3

9. launch testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

10. start scapy and configuration GTP profile in tester
    scapy::

    >>> import sys
    >>> from scapy.contrib.gtp import *


test steps for supported pattern
================================
1. validate rules.
2. create rules and list rules.
3. send matched packets, check the action is right:
    queue index: to right queue with mark id
    rss queues: to right queue group with mark id
    passthru: distributed by rss with mark id
    drop: not receive pkt
    rss+mark: distributed by rss with mark id
4. send mismatched packets, check the action is not right:
    queue index: not to right queue without mark id
    rss queues: not to right queue group without mark id
    passthru: distributed by rss without mark id
    drop: receive pkt
    rss+mark: distributed by rss without mark id
5. destroy rule, list rules.
6. send matched packets, check the action is not right.


supported pattern and inputset
==============================
.. table::

    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    | combination            | Packet type                      | inputset                                                                                                         |
    +========================+==================================+==================================================================================================================+
    | IP*+IP*+IP*            | MAC_IP*_GRE_IP*_GTPU_IP*         | outer l3 src, outer l3 dst, inner most l3 src, inner most l3 dst                                                 |
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_IP*_UDP     | outer l3 src, outer l3 dst, inner most l3 src, inner most l3 dst, inner most l4 src, inner most l4 dst           |
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_IP*_TCP     | outer l3 src, outer l3 dst, inner most l3 src, inner most l3 dst, inner most l4 src, inner most l4 dst           |
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_EH_IP*      | outer l3 src, outer l3 dst, teid, qfi, inner most l3 src, inner most l3 dst                                      |
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_EH_IP*_UDP  | outer l3 src, outer l3 dst, teid, qfi, inner most l3 src, inner most l3 dst, inner most l4 src, inner most l4 dst|
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_EH_IP*_TCP  | outer l3 src, outer l3 dst, teid, qfi, inner most l3 src, inner most l3 dst, inner most l4 src, inner most l4 dst|
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_UL_IP*      | outer l3 src, outer l3 dst, teid, qfi, inner most l3 src, inner most l3 dst                                      |
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_UL_IP*_UDP  | outer l3 src, outer l3 dst, teid, qfi, inner most l3 src, inner most l3 dst, inner most l4 src, inner most l4 dst|
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_UL_IP*_TCP  | outer l3 src, outer l3 dst, teid, qfi, inner most l3 src, inner most l3 dst, inner most l4 src, inner most l4 dst|
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_DL_IP*      | outer l3 src, outer l3 dst, teid, qfi, inner most l3 src, inner most l3 dst                                      |
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_DL_IP*_UDP  | outer l3 src, outer l3 dst, teid, qfi, inner most l3 src, inner most l3 dst, inner most l4 src, inner most l4 dst|
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+
    |                        | MAC_IP*_GRE_IP*_GTPU_DL_IP*_TCP  | outer l3 src, outer l3 dst, teid, qfi, inner most l3 src, inner most l3 dst, inner most l4 src, inner most l4 dst|
    +------------------------+----------------------------------+------------------------------------------------------------------------------------------------------------------+

each combination just need to change the IP* with IPV4 or IPV6, the inputset is same. there are 8 combinations in total:
1. IPV4+IPV4+IPV4
2. IPV6+IPV4+IPV4
3. IPV4+IPV6+IPV4
4. IPV4+IPV4+IPV6
5. IPV6+IPV6+IPV4
6. IPV4+IPV6+IPV6
7. IPV6+IPV4+IPV6
8. IPV6+IPV6+IPV6


1. IPV4+IPV4+IPV4

MAC_IPV4_GRE_IPV4_GTPU_IPV4
===========================
matched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")

unmatched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IPv6()],iface="ens786f0")

queue index
------------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 13 / end

rss queues
-----------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions rss queues 4 5 end / mark id 23 / end

passthru
---------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions passthru / mark id 33 / end

drop
-----
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions drop / end

mark+rss
--------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions mark / rss / end


MAC_IPV4_GRE_IPV4_GTPU_IPV4_UDP
===============================
matched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")

unmatched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.13")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(dport=33, sport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(dport=13, sport=33)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IPv6()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IPv6()/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")

queue index
------------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 3 / mark id 13 / end

rss queues
-----------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions rss queues 4 5 end / mark id 23 / end

passthru
---------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions passthru / mark id 33 / end

drop
-----
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions drop / end

mark+rss
--------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions mark / rss / end


MAC_IPV4_GRE_IPV4_GTPU_IPV4_TCP
===============================
matched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")

unmatched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.13")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/TCP(dport=33, sport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/TCP(dport=13, sport=33)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IPv6()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IPv6()/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")

queue index
------------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions queue index 3 / mark id 13 / end

rss queues
-----------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions rss queues 4 5 end / mark id 23 / end

passthru
---------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions passthru / mark id 33 / end

drop
-----
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions drop / end

mark+rss
--------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions mark / rss / end


MAC_IPV4_GRE_IPV4_GTPU_EH_IPV4
==============================
matched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")

unmatched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.14", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.15")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()],iface="ens786f0")

queue index
------------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 13 / end

rss queues
-----------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions rss queues 4 5 end / mark id 23 / end

passthru
---------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions passthru / mark id 33 / end

drop
-----
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions drop / end

mark+rss
--------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions mark / rss / end


MAC_IPV4_GRE_IPV4_GTPU_EH_IPV4_UDP
==================================
matched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")

unmatched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.13")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.14", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(dport=33, sport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(dport=13, sport=33)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IPv6()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")

queue index
------------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 3 / mark id 13 / end

rss queues
-----------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions rss queues 4 5 end / mark id 23 / end

passthru
---------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions passthru / mark id 33 / end

drop
-----
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions drop / end

mark+rss
--------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions mark / rss / end


MAC_IPV4_GRE_IPV4_GTPU_EH_IPV4_TCP
==================================
matched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")

unmatched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.13")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.14", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.15")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.15")/TCP(dport=33, sport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.15")/TCP(dport=13, sport=33)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IPv6()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")

queue index
------------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions queue index 3 / mark id 13 / end

rss queues
-----------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions rss queues 4 5 end / mark id 23 / end

passthru
---------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions passthru / mark id 33 / end

drop
-----
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions drop / end

mark+rss
--------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions mark / rss / end


MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4
==============================
matched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")

unmatched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.13")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IPv6()/UDP()/GTP_U_Header(type=1, P=1, QFI=0x34)/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header(type=1, P=1, QFI=0x34)/GTPPDUSessionContainer()/IPv6()],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")

queue index
------------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 13 / end

rss queues
-----------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions rss queues 4 5 end / mark id 23 / end

passthru
---------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions passthru / mark id 33 / end

drop
-----
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions drop / end

mark+rss
--------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions mark / rss / end


MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4_UDP
==================================
matched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")

unmatched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.13")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(dport=33, sport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(dport=13, sport=33)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x341)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IPv6()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x341)/IPv6()/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")

queue index
------------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 3 / mark id 13 / end

rss queues
-----------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions rss queues 4 5 end / mark id 23 / end

passthru
---------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions passthru / mark id 33 / end

drop
-----
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions drop / end

mark+rss
--------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions mark / rss / end


MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4_TCP
==================================
matched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")

unmatched pkt::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x341)/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.13")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x341)/IP(src="1.1.2.14", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x341)/IP(src="1.1.2.4", dst="1.1.2.15")/TCP(dport=33, sport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/TCP(dport=13, sport=33)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x341)/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IPv6()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6()/TCP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)],iface="ens786f0")

queue index
------------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions queue index 3 / mark id 13 / end

rss queues
-----------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions rss queues 4 5 end / mark id 23 / end

passthru
---------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions passthru / mark id 33 / end

drop
-----
flow create 0 ingress pattern eth / ipv6 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions drop / end

mark+rss
--------
flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions mark / rss / end


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


2. IPV6+IPV4+IPV4

reconfig all the cases of IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.

3. IPV4+IPV6+IPV4

reconfig all the cases of IPV4+IPV4+IPV4

    packets: change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
    rule: change the inner ipv4 to ipv6.

4. IPV4+IPV4+IPV6

reconfig all the cases of IPV4+IPV4+IPV4

    packets: change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.

5. IPV6+IPV6+IPV4

reconfig all the cases of IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner ipv4 to ipv6.

6. IPV4+IPV6+IPV6

reconfig all the cases of IPV4+IPV4+IPV4

    packets: change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
    rule: change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner ipv4 to ipv6.

7. IPV6+IPV4+IPV6

reconfig all the cases of IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.

8. IPV6+IPV6+IPV6

reconfig all the cases of IPV4+IPV4+IPV4

    packets: change the packet's outer l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
             change the packet's inner l3 layer from IP to IPv6(or IPv6 to IP).
             change the packet's inner most l3 layer from IP to IPv6(or IPv6 to IP), change the ipv4 address to ipv6 address.
    rule: change the outer ipv4 to ipv6, change the ipv4 address to ipv6 address.
          change the inner ipv4 to ipv6.
          change the inner most ipv4 to ipv6, change the ipv4 address to ipv6 address.


negative test case
==================

1. create rules and check all the rules fail::

    testpmd> flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp dst is 13 / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 33 / mark id 13 / end
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

    testpmd> flow create 0 ingress pattern eth / ipv6 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is a/ ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions mark / rss / end
    Bad arguments

    testpmd> flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc pdu_t is 2 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions queue index 3 / mark id 13 / end
    iavf_fdir_add(): Failed to add rule request due to the hw doesn't support
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv6 / udp / gtpu teid is 0x12 / gtp_psc pdu_t is 1 qfi is 0x100 / end actions rss queues 4 5 end / mark id 23 / end
    Bad arguments

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc pdu_t is 1 qfi is 0x3 / end actions drop / end
    Bad arguments


exclusive test case
===================

subcase 1: inner rule + outer rule
----------------------------------
when the inner rule and outer rule co-exist, always the second rule will work.
And the first rule will work when the second rule is destroyed.

1. create 1 rule using inner as input set and 1 rule using outer as input set::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 13 / mark id 13 / end
    flow create 0 ingress pattern eth / ipv4 src is 1.1.2.14 dst is 1.1.2.15 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc qfi is 0x3 / end actions queue index 14 / mark id 14 / end

2. send pkts which hit both 2 rules, check the pkt will hit the outer rule::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.14", dst="1.1.2.15")/GRE()/IP()/UDP()/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    testpmd> port 0/queue 14: received 1 packets
    src=A4:BF:01:69:38:A2 - dst=00:11:22:33:44:55 - type=0x0800 - length=110 - nb_segs=1 - RSS hash=0x1474171b - RSS queue=0xe - FDIR matched ID=0xe - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0xe
    ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_UNKNOWN

3. destroy the outer rule, send the pkt in step 2, check the pkt will hit the inner rule::

    flow destroy 0 rule 1
    Flow rule #1 destroyed
    testpmd> port 0/queue 13: received 1 packets
    src=A4:BF:01:69:38:A2 - dst=00:11:22:33:44:55 - type=0x0800 - length=110 - nb_segs=1 - RSS hash=0x1474171b - RSS queue=0xd - FDIR matched ID=0xd - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0xd
    ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_UNKNOWN

4. destroy the inner rule, send the pkt in step 2, check the pkt won't hit any rule::

    flow destroy 0 rule 0
    Flow rule #0 destroyed
    testpmd> port 0/queue 11: received 1 packets
    src=A4:BF:01:69:38:A2 - dst=00:11:22:33:44:55 - type=0x0800 - length=110 - nb_segs=1 - RSS hash=0x1474171b - RSS queue=0xb - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0xb
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

subcase 2: without eh rule + with eh rule
-----------------------------------------
when the rule with eh and another rule without eh co-exist, 2 rules do not affect each other.

1. create 1 rule with eh and 1 rule without eh::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 13 / mark id 13 / end
    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 3 / mark id 3 / end

2. send pkts which hit 2 rules separately, check the pkt will hit the each rule::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")

    testpmd> port 0/queue 13: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=110 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0xd - FDIR matched ID=0xd - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0xd
    ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_BAD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    port 0/queue 3: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=102 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0x3 - FDIR matched ID=0x3 - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x3
    ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_BAD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_UNKNOWN

3. destroy the rule without eh, send the pkt in step 2, check the eh pkt will hit eh rule, and the pkt without eh won't hit any rule::

    flow destroy 0 rule 1
    Flow rule #1 destroyed
    testpmd> port 0/queue 2: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=102 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0x2 - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x2
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    port 0/queue 13: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=110 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0xd - FDIR matched ID=0xd - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0xd
    ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_BAD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_UNKNOWN

4. destroy the rule with eh, send the pkt in step 2, check the pkts won't hit any rule::

    flow destroy 0 rule 0
    Flow rule #0 destroyed
    testpmd> port 0/queue 2: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=110 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0x2 - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x2
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

subcase 3: without l4 rule + with l4 rule
-----------------------------------------
the rule without l4 has a larger coverage than the rule with l4. if user need to create these two rule at the same time.
user should create rule without l4 firstly then create rule with l4.
when 2 rules exist, each pattern hit each rule. destroy l4 rule, l4 pattern hit l3 rule. destroy l3 rule, l3 pattern will not hit l4 rule.

1. create 1 rule with l4 and 1 rule without l4::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 13 / mark id 13 / end
    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 3 / mark id 3 / end

2. send pkts which hit 2 rules separately, check the pkt will hit the each rule::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)],iface="ens786f0")

    testpmd> port 0/queue 13: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=102 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0xd - FDIR matched ID=0xd - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0xd
    ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    port 0/queue 3: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=110 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0x3 - FDIR matched ID=0x3 - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x3
    ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_BAD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_UNKNOWN

3. destroy the rule with l4, send the pkt with l4, check it will hit the rule without l4::

    flow destroy 0 rule 1
    Flow rule #1 destroyed
    testpmd> port 0/queue 13: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=110 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0xd - FDIR matched ID=0xd - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0xd
    ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_BAD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_UNKNOWN

4. destroy the rule without l4, send the pkts in step 2, check the pkts won't hit any rule::

    flow destroy 0 rule 0
    Flow rule #0 destroyed
    testpmd> port 0/queue 2: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=110 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0x2 - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x2
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    port 0/queue 2: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=102 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0x2 - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x2
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

subcase 4: with eh but without ul/dl + ul
-----------------------------------------
when 2 rules exist, each pattern hit each rule. destroy ul rule, ul pattern hit eh rule without ul/dl.

1. create 1 rule with ul and 1 rule without ul/dl::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 13 / mark id 13 / end
    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 3 / end

2. send ul pkt, check the pkt will hit ul rule::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")],iface="ens786f0")

    testpmd> port 0/queue 3: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=106 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0x3 - FDIR matched ID=0x3 - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x3
    ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_UNKNOWN

3. destroy the ul rule, send the pkt in step 2, check the pkt will hit the eh rule without ul/dl::

    flow destroy 0 rule 1
    Flow rule #1 destroyed
    testpmd> port 0/queue 13: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=106 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0xd - FDIR matched ID=0xd - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0xd
    ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_UNKNOWN

4. destroy the eh rule without ul/dl, send the pkt in step 2, check the pkt won't hit any rules::

    flow destroy 0 rule 0
    Flow rule #0 destroyed
    testpmd> port 0/queue 2: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=106 - nb_segs=1 - RSS hash=0x489dd1c2 - RSS queue=0x2 - sw ptype: L2_ETHER L3_IPV4 TUNNEL_GRE INNER_L3_IPV4 INNER_L4_UDP  - l2_len=14 - l3_len=20 - tunnel_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x2
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

subcase 5: ipv4/ipv4/ipv4 rule + ipv4/ipv6/ipv4 rule
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

