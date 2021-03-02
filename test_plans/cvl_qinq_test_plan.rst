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

=========================
CVL support QinQ protocol
=========================
DPDK support QinQ protocol in CVL as below requirements:
* DCF support QinQ by add steering rule and vlan strip disable.
* DCF is able to set port vlan by port representor.
* AVF is able to configure inner VLAN filter when port vlan is enabled base on negotiation.
* AVF is able to configure outer VLAN (8100) if no port VLANis enabled to compatible with legacy mode.
this test plan contain 3 parts to cover above requirements:
* DCF switch filter for QinQ.
* DCF pvid support for QinQ.
* AVF VLAN offload for QinQ.


Prerequisites
=============
1. Hardware:
   columbiaville_25g/columbiaville_100g

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

6. Enable vlan prune flag::

    ethtool --set-priv-flags ens785f0 vf-vlan-prune-disable on

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

12. For test cases for DCF switch filter(01-06), use below cmd to launch testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf -a 0000:18:01.1 -a 0000:18:01.2 -a 0000:18:01.3 -- -i
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start
    testpmd> show port info all

   check the VF0 driver is net_ice_dcf.

   For test cases for DCF pvid(07-09), use below cmd to launch testpmd::

   ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf,representor=[1] -a 0000:18:01.1 -a 0000:18:01.2 -a 0000:18:01.3 -- -i
    testpmd> set fwd mac
    testpmd> set verbose 1
    testpmd> start
    testpmd> show port info all

   check the VF0 driver is net_ice_dcf.

13. For AVF QinQ test cases(10-14), recreate Generate 1 VFs on PF0, reconfig the VF then launch testpmd::

    echo 0 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    ethtool --set-priv-flags ens785f0 vf-vlan-prune-disable off
    echo 1 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    ip link set ens785f0 vf 0 mac 00:11:22:33:44:11
    ip link set dev ens785f0 vf 0 spoofchk off

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd> set fwd mac
    testpmd> set verbose 1
    testpmd> start

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
subcase: src ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv4 src is 196.222.232.221 / end actions vf id 1 / end
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

   check the packets are not to port 1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to port 1.

subcase: dst ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv4 dst is 196.222.232.221 / end actions vf id 1 / end
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

   check the packets are not to port 1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to port 1.


Test case 02: DCF switch for MAC_QINQ_IPV6_PAY
==============================================
subcase: src ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv6 src is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions vf id 1 / end
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

   check the packets are not to port 1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to port 1.

subcase: dst ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions vf id 1 / end
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

   check the packets are not to port 1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to port 1.


Test case 03: DCF switch for MAC_QINQ_PPPOE_PAY
===============================================

1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / end actions vf id 1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x21)/IP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/("X"*480)], iface="ens786f0")

   check the packets are not to port 1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to port 1.


Test case 04: DCF switch for MAC_QINQ_PPPOE_PAY_Proto
=====================================================

1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")

   check port 1 receive the packet.
   send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x57)/IPv6()/("X"*480)], iface="ens786f0")

   check the packets are not to port 1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to port 1.


Test case 05: DCF switch for MAC_QINQ_PPPOE_IPV4
================================================
subcase: src ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv4 src is 196.222.232.221 / end actions vf id 1 / end
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

   check the packets are not to port 1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to port 1.

subcase: dst ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv4 dst is 196.222.232.221 / end actions vf id 1 / end
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

   check the packets are not to port 1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to port 1.


Test case 06: DCF switch for MAC_QINQ_PPPOE_IPV6
================================================
subcase: src ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv6 src is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions vf id 1 / end
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

   check the packets are not to port 1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to port 1.

subcase: dst ip
---------------
1. create a rule::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions vf id 1 / end
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

   check the packets are not to port 1.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are not to port 1.


Test case 07: vlan strip when pvid enable
=========================================

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


Test case 08: vlan insertion when pvid enable
=============================================

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


Test case 09: vlan filter when pvid enable
==========================================

1. reset test environment, create vfs and disable vlan prune flag::

    ethtool --set-priv-flags ens785f0 vf-vlan-prune-disable off

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


Test case 10: Enable/Disable IAVF VLAN filtering
================================================

1. enable vlan filtering on port VF::

    testpmd> set fwd mac
    Set mac packet forwarding mode
    testpmd> vlan set filter on 0

2. check the vlan mode is set successfully::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    ......
    VLAN offload:
    strip off, filter on, extend off, qinq strip off

3. tester send qinq pkt and single vlan pkt which outer vlan id is 1 to VF::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

4. check the pkts can't be received in VF::

5. add rx_vlan in VF::

    testpmd> rx_vlan add 1 0

6. repeat step 3, check the pkts can be received by VF and fwd to tester::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=522 - nb_segs=1 - hw ptype: L2_ETHER  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN  - l2_len=18 - inner_l2_len=4 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER  - sw ptype: L2_ETHER_VLAN  - l2_len=18 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    tcpdump -i ens786f0 -nn -e -v

    16:50:38.807158 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype 0x0800,
    16:50:38.807217 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype 0x0800,

    16:51:06.083084 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype 0x0800,
    16:51:06.083127 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype 0x0800,

7. tester send qinq pkt and single vlan pkt which outer vlan id is 11 to VF::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=11,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=11,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

8. check the pkts can not be received by VF.

9. remove rx_vlan in VF1::

    testpmd> rx_vlan rm 1 0

10. repeat step 3, check the pkts can not be received by VF.


Test case 11: Enable/Disable IAVF VLAN header stripping
=======================================================

1. enable vlan filtering on port VF::

    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0

2. check the vlan mode is set successfully::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    ......
    VLAN offload:
    strip off, filter on, extend off, qinq strip off

3. enable vlan header stripping on VF::

    testpmd> vlan set strip on 0

4. check the vlan mode is set successfully::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    ......
    VLAN offload:
    strip on, filter on, extend off, qinq strip off

5. tester send qinq pkt and single vlan pkt which outer vlan id is 1 to VF::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

6. check the pkts can be received in VF and fwd to tester without outer vlan header::

    testpmd> port 0/queue 10: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0xc7b627aa - RSS queue=0xa - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0xa
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 0/queue 10: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xc7b627aa - RSS queue=0xa - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0xa
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    10:12:38.034948 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:12:38.035025 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    10:12:44.806825 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:12:44.806865 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

7. disable vlan header stripping on VF1::

    testpmd> vlan set strip off 0

8. check the vlan mode is set successfully::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    ......
    VLAN offload:
    strip off, filter on, extend off, qinq strip off

9. repeat step 5, check the pkts can be received in VF and fwd to tester with outer vlan header::

    testpmd> port 0/queue 10: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0xc7b627aa - RSS queue=0xa - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0xa
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 0/queue 10: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0xc7b627aa - RSS queue=0xa - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0xa
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    09:49:08.295172 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    09:49:08.295239 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    09:49:41.043101 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    09:49:41.043166 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480


Test case 12: Enable/Disable IAVF VLAN header insertion
=======================================================

1. enable vf-vlan-prune-disable flag::

    echo 0 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    ethtool --set-priv-flags ens785f0 vf-vlan-prune-disable on

2. set up test environment again::

    echo 1 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    ip link set ens785f0 vf 0 mac 00:11:22:33:44:11
    ip link set dev ens785f0 vf 0 spoofchk off
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd> set fwd mac
    testpmd> set verbose 1

3. enable vlan header insertion on VF::

    testpmd> port stop 0
    Stopping ports...
    Checking link statuses...
    Done
    testpmd> tx_vlan set 0 1
    testpmd> port start 0

4. tester send pkt to VF::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=11,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

5. check the pkts with vlan header can be received in tester::

    testpmd> port 0/queue 13: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xcaf4abfd - RSS queue=0xd - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0xd
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 0/queue 8: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0x28099b78 - RSS queue=0x8 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x8
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    10:32:55.566801 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:32:55.566856 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    06:29:32.281896 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 11, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    06:29:32.281940 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 11, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

6. disable vlan header insertion on VF1::

    testpmd> port stop 0
    Stopping ports...
    Checking link statuses...
    Done
    testpmd> tx_vlan reset 0
    testpmd> port start 0

7. repeat step 4, check the pkts without vlan tag can be received in tester::

    testpmd> port 0/queue 9: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xa63e8869 - RSS queue=0x9 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x9
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 0/queue 12: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0x6f5533bc - RSS queue=0xc - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0xc
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    10:34:40.070754 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:34:40.070824 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    06:36:57.641871 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 11, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    06:36:57.641909 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 11, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480


Test case 13: Enable/disable AVF CRC stripping
==============================================

1. start testpmd with "--disable-crc-strip"::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 20-23 -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16 --disable-crc-strip
    testpmd> set fwd mac
    testpmd> set verbose 1

2. send pkts to VF::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

3. check VF1 receive this pkts with CRC::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x890d9a70 - RSS queue=0x0 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  518
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  514

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################
    clear port stats all

4. enable crc strip in testpmd::

    testpmd> stop
    testpmd> port stop 0
    testpmd> port config 0 rx_offload keep_crc off
    testpmd> port start 0
    testpmd> start

5. repeat step 2, check VF receive this pkts without CRC::

    testpmd> port 0/queue 2: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xa94c21d2 - RSS queue=0x2 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x2
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  514
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  514

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################
    clear port stats all

6. disable crc strip in testpmd::

    testpmd> stop
    testpmd> port stop 0
    testpmd> port config 0 rx_offload keep_crc on
    testpmd> port start 0
    testpmd> start

7. repeat step 2, check VF1 receive this pkts with CRC::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x79c10190 - RSS queue=0x0 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  518
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  514

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################
    clear port stats all

8. re-launch testpmd without "--disable-crc-strip"::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 20-23 -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd> set fwd mac
    testpmd> set verbose 1

9. repeat step 2, check VF receive this pkts without CRC::

    testpmd> port 0/queue 2: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x898ada82 - RSS queue=0x2 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x2
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  514
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  514

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################


Test case 14: AVF CRC strip and Vlan strip co-exists
====================================================

1. start testpmd with crc strip enable, vlan strip disable::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 20-23 -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd> set fwd mac
    testpmd> set verbose 1
    testpmd> show port info 0
    ********************* Infos for port 0  *********************
    MAC address: 00:11:22:33:44:11
    Device name: 0000:18:01.1
    Driver name: net_iavf
    ......
    VLAN offload:
      strip off, filter off, extend off, qinq strip off

2. request disable vlan strip::

    testpmd> vlan set strip off 0

3. check the vlan strip still disable::

    testpmd> show port info 0
    ********************* Infos for port 0  *********************
    MAC address: 00:11:22:33:44:11
    Device name: 0000:18:01.1
    Driver name: net_iavf
    ......
    VLAN offload:
      strip off, filter off, extend off, qinq strip off

4. set vlan filter on and add rx_vlan 1::

    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> start

5. send qinq pkts to check vlan strip is off, crc strip is on::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

    testpmd> port 0/queue 6: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0xf6521426 - RSS queue=0x6 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0x6
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  522
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  522

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################

    09:07:45.863251 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    09:07:45.863340 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

6. request enable vlan strip::

    testpmd> vlan set strip on 0

7. check the vlan strip enable successfully::

    testpmd> show port info 0
    ********************* Infos for port 0  *********************
    MAC address: 00:11:22:33:44:11
    Device name: 0000:18:01.1
    Driver name: net_iavf
    ......
    VLAN offload:
      strip on, filter off, extend off, qinq strip off

8. repeat step 5, send qinq pkts to check vlan strip is on(tx-4), crc strip is on::

    testpmd> port 0/queue 6: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0xf6521426 - RSS queue=0x6 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0x6
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  522
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  518

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################

    11:09:03.918907 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    11:09:03.918952 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

9. request disable vlan strip::

    testpmd> vlan set strip off 0

10. check the vlan strip disable successfully::

    testpmd> show port info 0
    ********************* Infos for port 0  *********************
    MAC address: 00:11:22:33:44:11
    Device name: 0000:18:01.1
    Driver name: net_iavf
    ......
    VLAN offload:
      strip off, filter on, extend off, qinq strip off

11. request disable crc strip::

    testpmd> stop
    testpmd> port stop 0
    testpmd> port config 0 rx_offload keep_crc on
    testpmd> port start 0
    testpmd> start

12. repeat step 5, send qinq pkts to check vlan strip is off, crc strip is off(rx+4)::

    testpmd> port 0/queue 7: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0xbc8b1857 - RSS queue=0x7 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Tail/CRC: 0x58585858/0x6d870bf6 - Receive queue=0x7
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all
    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  526
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  522

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################

    10:23:57.350934 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:23:57.351008 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

13. request enable vlan strip::

    testpmd> vlan set strip on 0
    iavf_execute_vf_cmd(): No response or return failure (-64) for cmd 54
    iavf_config_vlan_strip_v2(): fail to execute command VIRTCHNL_OP_ENABLE_VLAN_STRIPPING_V2
    rx_vlan_strip_set(port_pi=0, on=1) failed diag=-5

14. repeat step 5, send qinq pkts to check the vlan strip can not enable::

    testpmd> port 0/queue 7: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0xbc8b1857 - RSS queue=0x7 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Tail/CRC: 0x58585858/0x6d870bf6 - Receive queue=0x7
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all
    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  526
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  522

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################

    10:26:08.346936 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:26:08.347006 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

15. request disable vlan strip::

    vlan set strip off 0

16. check the vlan strip still disable::

    testpmd> show port info 0
    ********************* Infos for port 0  *********************
    MAC address: 00:11:22:33:44:11
    Device name: 0000:18:01.1
    Driver name: net_iavf
    ......
    VLAN offload:
      strip off, filter on, extend off, qinq strip off

17. request enable crc strip::

    testpmd> stop
    testpmd> port stop 0
    testpmd> port config 0 rx_offload keep_crc off
    testpmd> port start 0
    testpmd> start

18. repeat step 5, send qinq pkts to check the crc strip enable successfully::

    testpmd> port 0/queue 3: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0x2b4ad203 - RSS queue=0x3 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Receive queue=0x3
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    port 0/queue 3: sent 1 packets
    src=00:11:22:33:44:11 - dst=02:00:00:00:00:00 - type=0x8100 - length=522 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Send queue=0x3
    ol_flags: PKT_RX_L4_CKSUM_UNKNOWN PKT_RX_IP_CKSUM_UNKNOWN PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all
    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  522
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  522

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################

    10:29:19.995352 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:29:19.995424 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480