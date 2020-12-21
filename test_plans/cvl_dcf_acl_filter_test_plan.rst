.. Copyright (c) <2020>, Intel Corporation
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

==================
CVL DCF ACL filter
==================

Description
===========
Support CPF on to program ACL rule to control packet to VFs.
Currently, only support the action "drop".
1. Deny packets according to IPV4 SRC/DST subnet
2. Deny packets according to L4 (UDP/TCP/SCTP) SRC/DST PORT
3. Deny packets according to IPV4 SRC/DST, TCP/UDP/SCTP SRC/DST PORT
4. Deny packets according to ETH SRC/DST MAC, IPV4 SRC/DST, TCP/UDP/SCTP SRC/DST PORT

Note: Each NIC has 16 TCAM blocks. Due to limited TCAM resource,
2 ports card can support denying packets according to ETH SRC/DST MAC.
4 ports card can't support denying packets according to ETH SRC/DST MAC.

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

    make -j install T=x86_64-native-linuxapp-gcc

5. Get the pci device id of DUT, for example::

    ./usertools/dpdk-devbind.py -s

    0000:86:00.0 'Device 1593' if=enp134s0f0 drv=ice unused=vfio-pci
    0000:86:00.1 'Device 1593' if=enp134s0f1 drv=ice unused=vfio-pci

6. Generate 2 VFs on PF0::

    echo 2 > /sys/bus/pci/devices/0000:86:00.0/sriov_numvfs

    ./usertools/dpdk-devbind.py -s
    0000:86:01.0 'Ethernet Adaptive Virtual Function 1889' if=enp134s1 drv=iavf unused=vfio-pci
    0000:86:01.1 'Ethernet Adaptive Virtual Function 1889' if=enp134s1f1 drv=iavf unused=vfio-pci

7. Set VF0 as trust::

    ip link set enp134s0f0 vf 0 trust on

   Set VF1 MAC address::

    ip link set enp134s0f0 vf 1 mac 00:01:23:45:67:89

8. Bind VFs to dpdk driver::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:86:01.0 0000:86:01.1

9. Launch dpdk on VF0, and VF0 request DCF mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -w 0000:86:01.0,cap=dcf --file-prefix=vf0 --log-level="ice,7" -- -i
    testpmd> set fwd mac
    testpmd> set verbose 1
    testpmd> start
    testpmd> show port info all

   check the VF0 driver is net_ice_dcf.
   the mac address is 42:52:CC:FD:CC:BB

10. Launch dpdk on VF1::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf0 -n 4 -w 86:01.1 --file-prefix=vf1 -- -i
     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start
     testpmd> show port info all


   check the VF1 driver is net_iavf.
   the mac address is 00:01:23:45:67:89

or launch one testpmd on VF0 and VF1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -w 0000:86:01.0,cap=dcf -w 86:01.1 --file-prefix=vf0 --log-level="ice,7" -- -i

Common steps of basic cases
===========================
1. create a rule successfully.
2. send matched packets, check the packets be dropped by VF1.
3. send unmatched packet, check the packet be received by VF1.
4. delete the rule.
5. send match packets again, check all the packets are received by VF1.


Test Case 1: pattern IPV4
=========================
Subcase 1: src mac(only 2ports NIC support)
-------------------------------------------
1. rule::

    flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask 00:ff:ff:ff:ff:ff / ipv4 / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2", frag=1)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="01:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="02:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="ff:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="01:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/ICMP()/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:66:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:66", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2", frag=1)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:66:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:66", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:32:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="01:11:22:33:44:66", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/ICMP()/Raw(load='X'*30)], iface="enp134s0f1")

Subcase 2: dst mac(only 2ports NIC support)
-------------------------------------------
On Rx side, the ACL filter follows switch filter in pipeline.
So we need set switch filter first, which switch some packets
with dst mac address which is not VF1's mac address.
Then the ACL filter can filter the packet with dst mac address.

1. rule::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / end actions vf id 1 / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:66 / ipv4 / end actions vf id 1 / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:66:55 / ipv4 / end actions vf id 1 / end
    flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:00 / ipv4 / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:02:00:00:00:01", dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:02:00:00:00:01", dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP()/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:02:00:00:00:01", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:02:00:00:00:01", dst="00:11:22:33:66:55")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")

Note: only delete ACL rule in step 4::

    flow destroy 0 rule 3

Subcase 3: src ipv4
-------------------
1. rule::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.0", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2",frag=1)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.158", dst="192.168.0.2")/UDP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.255", dst="192.168.0.2")/TCP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.255", dst="192.168.0.2")/SCTP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.255", dst="192.168.0.2")/ICMP()/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2",frag=1)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2")/UDP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2")/TCP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2")/SCTP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2")/ICMP()/Raw(load='X'*30)], iface="enp134s0f1")

Subcase 4: dst ipv4
-------------------
1. rule::

    flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.0 / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.0")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.0",frag=1)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.158")/UDP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.255")/TCP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.255")/SCTP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.255")/ICMP()/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.1.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.1.2",frag=1)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.1.2")/UDP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.1.2")/TCP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.1.2")/SCTP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.1.2")/ICMP()/Raw(load='X'*30)], iface="enp134s0f1")

Subcase 5: src ipv4 + dst ipv4
------------------------------
1. rule::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.255", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.255", dst="192.168.0.2",frag=1)/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.158", dst="192.168.255.2")/UDP()/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.0", dst="192.168.1.2")/TCP()/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.0", dst="192.168.1.2")/SCTP()/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.0", dst="192.168.1.2")/ICMP()/Raw(load='X'*30)], iface="enp216s0f0")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2",frag=1)/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2")/UDP()/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.3")/TCP()/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.3")/SCTP()/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.3")/ICMP()/Raw(load='X'*30)], iface="enp216s0f0")

Subcase 6: src mac + dst mac + src ipv4 + dst ipv4(only 2port NIC support)
--------------------------------------------------------------------------
1. rule::

    flow create 0 ingress pattern eth dst is 33:00:00:00:00:01 / ipv4 / end actions vf id 1 / end
    flow create 0 ingress pattern eth dst is 33:00:00:00:00:02 / ipv4 / end actions vf id 1 / end
    flow create 0 ingress pattern eth dst is 33:00:00:00:00:03 / ipv4 / end actions vf id 1 / end
    flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 33:00:00:00:00:02 dst mask ff:ff:ff:ff:ff:fe \
    / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:1b", dst="33:00:00:00:00:02")/IP(src="192.168.0.255", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:1b", dst="33:00:00:00:00:02")/IP(src="192.168.0.255", dst="192.168.0.2",frag=1)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:00", dst="33:00:00:00:00:03")/IP(src="192.168.0.158", dst="192.168.255.2")/UDP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:ff", dst="33:00:00:00:00:02")/IP(src="192.168.0.0", dst="192.168.1.2")/TCP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:ff", dst="33:00:00:00:00:02")/IP(src="192.168.0.0", dst="192.168.1.2")/SCTP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:ff", dst="33:00:00:00:00:02")/IP(src="192.168.0.0", dst="192.168.1.2")/ICMP()/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:66:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2",frag=1)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:01")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.1.1", dst="192.168.0.2")/TCP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.3")/SCTP()/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.3")/ICMP()/Raw(load='X'*30)], iface="enp134s0f1")

Note: only delete ACL rule in step 4::

    flow destroy 0 rule 3

Test Case 2: pattern IPV4_TCP
=============================
Subcase 1: src mac(only 2ports NIC support)
-------------------------------------------
1. rule::

    flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:fe / ipv4 / tcp / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:54", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:44:57", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IPv6()/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")

Subcase 2: dst mac(only 2ports NIC support)
-------------------------------------------
On Rx side, the ACL filter follows switch filter in pipeline.
So we need set switch filter first, which switch some packets
with dst mac address which is not VF1's mac address.
Then the ACL filter can filter the packet with dst mac address.

1. rule::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / tcp / end actions vf id 1 / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:66 / ipv4 / tcp / end actions vf id 1 / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:66:55 / ipv4 / tcp / end actions vf id 1 / end
    flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:00 / ipv4 / tcp / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:02:00:00:00:01", dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:02:00:00:00:01", dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:02:00:00:00:01", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:02:00:00:00:01", dst="00:11:22:33:66:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")

Note: only delete ACL rule in step 4::

    flow destroy 0 rule 3

Subcase 3: src ipv4
-------------------
1. rule::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / tcp / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.0", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.3", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")

Subcase 4: dst ipv4
-------------------
1. rule::

    flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.243 / tcp / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.14")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.3")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")

Subcase 5: src port
-------------------
1. rule::

    flow create 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP()/TCP(sport=8012)/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP()/TCP(sport=7985)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IPv6()/TCP(sport=8012)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP()/SCTP(sport=8012)/Raw(load='X'*30)], iface="enp134s0f1")

Subcase 6: dst port
-------------------
1. rule::

    flow create 0 ingress pattern eth / ipv4 / tcp dst spec 8010 dst mask 65520 / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP()/TCP(dport=8012)/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP()/TCP(dport=7985)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP()/UDP(dport=8012)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IPv6()/TCP(dport=8012)/Raw(load='X'*30)], iface="enp134s0f1")

Subcase 7: src ip + dst ip + src port + dst port
------------------------------------------------
1. rule::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 \
    / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.2", dst="192.168.255.2")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp216s0f0")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.3")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=7985,dport=8018)/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=7985)/Raw(load='X'*30)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp216s0f0")

Subcase 8: src mac + dst mac + src ip + dst ip + src port + dst port(only 2ports NIC support)
---------------------------------------------------------------------------------------------
1. rule::

    flow create 0 ingress pattern eth dst is 00:01:23:45:67:89 / ipv4 / tcp / end actions vf id 1 / end
    flow create 0 ingress pattern eth dst is 5E:8E:8B:4D:89:06 / ipv4 / tcp / end actions vf id 1 / end
    flow create 0 ingress pattern eth dst is 5E:8E:8B:4D:90:05 / ipv4 / tcp / end actions vf id 1 / end
    flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 00:01:23:45:67:89 dst mask ff:ff:ff:ff:00:ff \
    / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 \
    / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end

2. matched packets::

    sendp([Ether(src="00:11:22:33:44:66", dst="00:01:23:45:66:89")/IP(src="192.168.0.2", dst="192.168.255.2")/TCP(sport=8012,dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")

3. unmatched packets::

    sendp([Ether(src="00:11:22:33:66:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8010,dport=8017)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:90")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8010,dport=8017)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2")/TCP(sport=8010,dport=8017)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.3")/TCP(sport=8010,dport=8017)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=7985,dport=8017)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8010,dport=7985)/Raw(load='X'*30)], iface="enp134s0f1")

Note: only delete ACL rule in step 4::

    flow destroy 0 rule 3

Test Case 3: pattern IPV4_UDP
=============================
the rules and packets in this test case is similar to "Test case 2: pattern IPV4_TCP"
just change some parts of rules and packets:

    rule:
        change tcp to udp.
    packets:
        if the packet's L4 layer is UDP, change it to TCP;
        if the packet's L4 layer is TCP, change it to UDP;

Subcase 1: src mac(only 2ports NIC support)
-------------------------------------------
Subcase 2: dst mac(only 2ports NIC support)
-------------------------------------------
Subcase 3: src ipv4
-------------------
Subcase 4: dst ipv4
-------------------
Subcase 5: src port
-------------------
Subcase 6: dst port
-------------------
Subcase 7: src ip + dst ip + src port + dst port
------------------------------------------------
Subcase 8: src mac + src ip + dst ip + src port + dst port(only 2ports NIC support)
-----------------------------------------------------------------------------------

Test Case 4: pattern IPV4_SCTP
==============================
the rules and packets in this test case is similar to "Test case 2: pattern IPV4_TCP"
just change some parts of rules and packets:

    rule:
        change tcp to sctp.
    packets:
        if the packet's L4 layer is TCP, change it to SCTP;
        if the packet's L4 layer is SCTP, change it to UDP;

Subcase 1: src mac(only 2ports NIC support)
-------------------------------------------
Subcase 2: dst mac(only 2ports NIC support)
-------------------------------------------
note: switch rule don't support SCTP packet type,
so there is some difference to UDP/TCP case.

Subcase 3: src ipv4
-------------------
Subcase 4: dst ipv4
-------------------
Subcase 5: src port
-------------------
Subcase 6: dst port
-------------------
Subcase 7: src ip + dst ip + src port + dst port
------------------------------------------------
Subcase 8: src mac + src ip + dst ip + src port + dst port(only 2ports NIC support)
-----------------------------------------------------------------------------------
note: switch rule don't support SCTP packet type,
so there is some difference to UDP/TCP case.

Test Case 5: max entry number
=============================
Note: now the default entry number is 512.
if create a IPv4 rule, will generate 4 entries:
ipv4, ipv4-udp, ipv4-tcp, ipv4-sctp
So we can create 128 IPv4 rules at most.
while we can create 512 ipv4-udp/ipv4-tcp/ipv4-sctp rules at most.

1. launch DPDK on VF0, request DCF mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc -n 4 -w 86:01.0,cap=dcf -- -i --port-topology=loop

   Launch dpdk on VF1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf0 -n 4 -w 86:01.1 --file-prefix=vf1 -- -i

2. create a full mask rule, it's created as a switch rule::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.255 / udp / end actions drop / end

3. create 512 ipv4-udp ACL rules::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.0 src mask 255.255.255.254 / udp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / udp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.2 src mask 255.255.255.254 / udp / end actions drop / end
    ......
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.255 src mask 255.255.255.254 / udp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.0 src mask 255.255.255.254 / udp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.254 / udp / end actions drop / end
    ......
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.255 src mask 255.255.255.254 / udp / end actions drop / end

   all the rules can be created successfully as ACL rules.

4. list the rules, there are rule 0-512 listed.

5. send packet1::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.0", dst="192.168.100.2")/UDP(sport=8010,dport=8017)/Raw(load='X'*30)], iface="enp134s0f1")

   check the packet dropped.

6. create one more rule::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.2.1 src mask 255.255.255.254 / udp / end actions drop / end

   check the rule can't be created as an ACL rule successfully.

7. send packet2::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.2.1", dst="192.168.100.2")/UDP(sport=8010,dport=8017)/Raw(load='X'*30)], iface="enp134s0f1")

   check the packet can be received by VF1.

8. delete the rule 512::

    flow destroy 0 rule 512

   list the rules::

    flow list 0

   there are rule 0-511 listed.

9. create the rule in the step6 again,
   check the rule can be created successfully.
   list the rules, there are rule 0-512 listed.

10. send packet2 again, check the packet dropped.

Test Case 6: max entry number ipv4-other
========================================
1. launch DPDK on VF0, request DCF mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc -n 4 -w 86:01.0,cap=dcf -- -i --port-topology=loop

   Launch dpdk on VF1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf0 -n 4 -w 86:01.1 --file-prefix=vf1 -- -i

2. create a full mask rule, it's created as a switch rule::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.255 / end actions drop / end

3. create 128 ipv4-other ACL rules::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.254 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.2 src mask 255.255.255.254 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.3 src mask 255.255.255.254 / end actions drop / end
    ......
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.128 src mask 255.255.255.254 / end actions drop / end

   all the rules can be created successfully as ACL rules.

4. list the rules, there are rule 0-128 listed.

5. send packet1::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")

   check the packet dropped.

6. create one more rule::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.2 src mask 255.255.255.254 / udp / end actions drop / end

   check the rule can't be created as an ACL rule successfully.

7. send packet2::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.2", dst="192.168.1.2")/Raw(load='X'*30)], iface="enp134s0f1")

   check the packet can be received by VF1.

8. delete the rule 128::

    flow destroy 0 rule 128

   list the rules::

    flow list 0

   there are rule 0-127 listed.

9. create the rule in the step6 again,
   check the rule can be created successfully.
   list the rules, there are rule 0-128 listed.

10. send packet2 again, check the packet dropped.

Test Case 7: max entry number combined patterns
===============================================
1. launch DPDK on VF0, request DCF mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc -n 4 -w 86:01.0,cap=dcf -- -i --port-topology=loop

   Launch dpdk on VF1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf0 -n 4 -w 86:01.1 --file-prefix=vf1 -- -i

2. create 64 ipv4-other ACL rules::

    flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.0 dst mask 255.255.255.0 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 / end actions drop / end
    ......
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.62 src mask 255.255.255.0 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.63 src mask 255.255.255.0 / end actions drop / end

   all the rules can be created successfully as ACL rules.

3. create 256 ipv4-udp ACL rules::

    flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.0 dst mask 255.255.255.254 / udp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / udp / end actions drop / end
    ......
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.254 src mask 255.255.255.254 / udp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.255 src mask 255.255.255.254 / udp / end actions drop / end

   all the rules can be created successfully as ACL rules.

4. list the rules, there are rule 0-319 listed.

5. create one more ACl rule failed, it is created as a switch rule::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.2.255 src mask 255.255.255.254 / udp / end actions drop / end

6. delete one ACL rule, create the rule in step5 again, it's created as an ACL rule successfully.

7. delete the switch rule, send packet1::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.2.255", dst="192.168.0.2")/UDP(sport=8010,dport=8017)/Raw(load='X'*30)], iface="enp134s0f1")

   check the packet dropped.

8. delete all the rules, check the packet is received by vf1.

Test Case 8: negative case
==========================
Note:
4 ports NIC doesn't support eth input set.
the rule with eth input set can be created successfully,
but can't take effect on 4 ports NIC.

1. create an ACL rule without spec or mask::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src mask 255.255.255.0 / end actions drop / end
    flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 / ipv4 / tcp / end actions drop / end
    flow create 0 ingress pattern eth src mask ff:ff:ff:ff:ff:00 / ipv4 / tcp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / tcp src spec 8010 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / tcp src mask 65520 / end actions drop / end

   check the rule can't be created successfully.

2. create an ACL rule with all "0" mask::

    flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.1 dst mask 0.0.0.0 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / tcp dst spec 8010 dst mask 0 / end actions drop / end
    flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask 00:00:00:00:00:00 / ipv4 / tcp / end actions drop / end

   check the rule can't be created successfully.

3. create acl rules combined "0" mask and not "0" mask::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 0.0.0.0 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 0 / end actions drop / end
    flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 00:11:22:33:44:66 dst mask 00:00:00:00:00:00 / ipv4 / tcp / end actions drop / end

   check the rules created successfully.
   send matched packets::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.1",dst="192.168.1.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1",dst="192.168.0.2")/TCP(sport=8012,dport=23)/("X"*480)], iface="enp216s0f0")
    sendp([Ether(src="00:11:22:33:44:55",dst="00:01:23:45:67:89")/IP(src="192.168.1.1",dst="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)], iface="enp216s0f0")

   check the packets dropped by port 1.

Note: the last rule and last packet can only test on 2 ports NIC.

4. create inconsistent spec and mask rule::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 dst mask 255.255.255.0 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / tcp src spec 8010 dst mask 65520 / end actions drop / end

   check the rules created successfully.
   send matched packets::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1",dst="0.0.0.0")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.1",dst="192.168.0.2")/TCP(sport=22,dport=0)/("X"*480)], iface="enp216s0f0")

   check the packets dropped by port 1.

5. create ACL rule with full mask, for 4 ports NIC::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.255 dst spec 192.168.0.2 dst mask 255.255.255.255 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.255 dst spec 192.168.1.2 dst mask 255.255.255.255 \
    / tcp src spec 8010 src mask 65535 dst spec 8017 dst mask 65535 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.2.1 src mask 255.255.255.255 dst spec 192.168.2.2 dst mask 255.255.255.0 \
    / udp src spec 8010 src mask 65520 dst spec 8017 dst mask 65535 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.2.1 src mask 255.255.255.255 dst spec 192.168.2.2 dst mask 255.255.255.255 \
    / sctp src spec 8012 src mask 65535 dst spec 8018 dst mask 65535 / end actions drop / end

   for 2 ports NIC::

    / ipv4 src spec 192.168.0.1 src mask 255.255.255.255 dst spec 192.168.0.2 dst mask 255.255.255.255 / end actions drop / end
    flow create 0 ingress pattern eth src spec 00:01:23:45:67:89 src mask ff:ff:ff:ff:ff:ff dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:ff \
    / ipv4 src spec 192.168.1.1 src mask 255.255.255.255 dst spec 192.168.1.2 dst mask 255.255.255.255 \
    / tcp src spec 8010 src mask 65535 dst spec 8017 dst mask 65535 / end actions drop / end
    flow create 0 ingress pattern eth src spec 00:01:23:45:67:89 src mask ff:ff:ff:ff:ff:ff dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:ff \
    / ipv4 src spec 192.168.2.1 src mask 255.255.255.255 dst spec 192.168.2.2 dst mask 255.255.255.0 \
    / udp src spec 8010 src mask 65520 dst spec 8017 dst mask 65535 / end actions drop / end
    flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:ff dst spec 00:01:23:45:67:89 dst mask ff:ff:ff:ff:ff:ff \
    / ipv4 src spec 192.168.2.1 src mask 255.255.255.255 dst spec 192.168.2.2 dst mask 255.255.255.255 \
    / sctp src spec 8012 src mask 65535 dst spec 8018 dst mask 65535 / end actions drop / end

   check the rules created successfully only as switch rule.

Test Case 9: multirules with different pattern or input set
===========================================================
1. create rule 0::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 / end actions drop / end

2. send packets::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.3", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.3.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.3", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.3.3", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.3.3", dst="192.168.1.2")/UDP(sport=8012, dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")

   check the packet 1 is dropped, packet 2-5 are not dropped.

3. create rule 1, same inputset field, same spec, different mask::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.0.255 / end actions drop / end

4. send same packets, check packet 1 is dropped by rule 0, packet 2 is dropped by rule 1.
   packet 3-5 are not dropped.

5. create rule 2, same inputset field, different spec, same mask::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.0 / end actions drop / end

6. send same packets, check packet 1 is dropped by rule 0, packet 2 is dropped by rule 1.
   packet 3 is dropped by rule 2, packet 4-5 are not dropped.

7. create rule 3, same pattern, different input set field::

    flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.1 dst mask 255.255.255.0 / end actions drop / end

8. send same packets, check packet 1 is dropped by rule 0, packet 2 is dropped by rule 1.
   packet 3 is dropped by rule 2, packet 4 is dropped by rule 3, packet 5 is not dropped.

9. create rule 4, different pattern, same input set field::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.2.3 src mask 255.255.0.255 / udp / end actions drop / end

10. send same packets, check packet 1 is dropped by rule 0, packet 2 is dropped by rule 1.
    packet 3 is dropped by rule 2, packet 4 is dropped by rule 3, packet 5 is dropped by rule4.

Test Case 10: multirules with all patterns
==========================================
1. create multirules with different pattern or input set::

    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.0 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / tcp dst spec 8017 dst mask 65520 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / tcp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.254 / tcp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / udp src spec 8017 src mask 65520 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / udp dst spec 8010 dst mask 65520 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.254.255 / udp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.254.255 / udp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / udp src spec 8017 src mask 65520 dst spec 8010 dst mask 65520 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / sctp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.254 / sctp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / sctp src spec 8010 src mask 65520 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / sctp dst spec 8010 dst mask 65520 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / sctp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end

   check all the rules can be created successfully.

2. send ipv4-pay packets::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.3", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.1.2")/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.1.2")/Raw(load='X'*30)], iface="enp134s0f1")

   check ipv4-pay packets 1-3 are dropped, packet 4 is not dropped.

3. send ipv4-tcp packets::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=8012, dport=7985)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=7985, dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.0", dst="192.168.1.2")/TCP(sport=7984, dport=7985)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.3")/TCP(sport=7984, dport=7985)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.3", dst="192.168.1.2")/TCP(sport=8012, dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=8018, dport=8012)/Raw(load='X'*30)], iface="enp134s0f1")

   check ipv4-tcp packets 1-5 are dropped, packet 6 is not dropped.

4. send ipv4-udp packets::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=8017, dport=7985)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=7985, dport=8012)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.3")/UDP(sport=7984, dport=7985)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.3", dst="192.168.1.2")/UDP(sport=7984, dport=7985)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.3", dst="192.168.1.2")/UDP(sport=8018, dport=8012)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.0", dst="192.168.0.3")/UDP(sport=8012, dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")

   check ipv4-udp packets 1-6 are dropped.

5. send ipv4-sctp packets::

    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=8012, dport=7985)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=7985, dport=8012)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.3")/SCTP(sport=7984, dport=7985)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.1", dst="192.168.1.2")/SCTP(sport=7984, dport=7985)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.3", dst="192.168.1.2")/SCTP(sport=8012, dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")
    sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.1.0", dst="192.168.1.3")/SCTP(sport=8017, dport=8018)/Raw(load='X'*30)], iface="enp134s0f1")

   check ipv4-sctp packets 1-5 are dropped, packet 6 is not dropped.

Test Case 11: switch/acl/fdir/rss rules combination
===================================================
1. launch testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc -n 4 -w 86:01.0,cap=dcf -w 86:01.1 --log-level="ice,7" -- -i --port-topology=loop --rxq=4 --txq=4

2. create rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.20 / tcp / end actions vf id 1 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.20 / tcp / end actions vf id 1 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.20 / tcp / end actions vf id 1 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.4 dst is 192.168.0.20 / tcp / end actions vf id 1 / end
    flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.2 src mask 255.255.255.254 / tcp / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.21 dst mask 255.255.0.255 / tcp / end actions drop / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.20 / tcp src is 22 dst is 23 / end actions queue index 3 / mark / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.20 / tcp src is 22 dst is 23 / end actions queue index 3 / mark / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.1.1 dst is 192.168.0.20 / tcp src is 22 dst is 23 / end actions queue index 3 / mark / end

3. check the rule list::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 TCP => VF
    1       0       0       i--     ETH IPV4 TCP => VF
    2       0       0       i--     ETH IPV4 TCP => VF
    3       0       0       i--     ETH IPV4 TCP => VF
    4       0       0       i--     ETH IPV4 TCP => DROP
    5       0       0       i--     ETH IPV4 TCP => DROP
    testpmd> flow list 1
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 TCP => QUEUE MARK
    1       0       0       i--     ETH IPV4 TCP => QUEUE MARK
    2       0       0       i--     ETH IPV4 TCP => QUEUE MARK

4. send packets::

    sendp(Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.1", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30), iface="enp216s0f0")
    sendp(Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.1", dst="192.168.0.20")/TCP(sport=32,dport=33)/Raw(load="x"*30), iface="enp216s0f0")
    sendp(Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.2", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30), iface="enp216s0f0")
    sendp(Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.3", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30), iface="enp216s0f0")
    sendp(Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.4", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30), iface="enp216s0f0")
    sendp(Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.1.1", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30), iface="enp216s0f0")
    sendp(Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30), iface="enp216s0f0")
    sendp(Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:89")/IP(src="192.168.1.1", dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw(load="x"*30), iface="enp216s0f0")

5. check packet 1 is received by port 1 and redirected to queue 3 with FDIR matched ID=0x0.
   packet 2 is received by port 1 and distributed by RSS without mark ID.
   packet 3 is dropped by port 1.
   packet 4 is dropped by port 1.
   packet 5 is received by port 1 and distributed by RSS without mark ID.
   packet 6 is can't received by port 0 and port 1.
   packet 7 is received by port 1 and redirected to queue 3 with FDIR matched ID=0x0.
   packet 8 is dropped by port 1.

6. delete rule ID 4 from port 0 and list the rules::

    testpmd> flow destroy 0 rule 4
    Flow rule #4 destroyed
    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 TCP => VF
    1       0       0       i--     ETH IPV4 TCP => VF
    2       0       0       i--     ETH IPV4 TCP => VF
    3       0       0       i--     ETH IPV4 TCP => VF
    5       0       0       i--     ETH IPV4 TCP => DROP

7. send packets::

    sendp(Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.2", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30), iface="enp216s0f0")
    sendp(Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.3", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30), iface="enp216s0f0")

8. check packet 1 is received by port 1 and redirected to queue 3 with FDIR matched ID=0x0.
   packet 2 is received by port 1 and distributed by RSS without mark ID.
