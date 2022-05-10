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

=================================
ICE: VF support multicast address
=================================
VF support adding and removing multicast address


Prerequisites
=============

1. Hardware:
   Intel® Ethernet 800 Series: E810-XXVDA4/E810-CQ

2. Software:
   DPDK: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Generate 2 VFs on PF::

    echo 2 > /sys/bus/pci/devices/0000:86:00.0/sriov_numvfs
    ethtool --set-priv-flags enp134s0f0 vf-true-promisc-support on
    ip link set enp134s0f0 vf 0 trust on
    ip link set enp134s0f0 vf 1 trust on

   0000:86:00.0 generate 0000:86:01.0 and 0000:86:01.1
   define 86:01.0 as vf0, 86:01.1 as vf1.
   assign mac address of vf0 is FE:ED:84:92:64:DD,
   assign mac address of vf1 is 5E:8E:8B:4D:89:05.

4. Bind VFs to dpdk driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 86:01.0 86:01.1

5. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 6 -- -i --portmask=0x3 --rxq=16 --txq=16
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start
    testpmd> set promisc all off
    testpmd> set allmulti all off

6. show multicast address of port 0 and port 1::

    testpmd> show port 0 mcast_macs
    testpmd> show port 1 mcast_macs

   both of the ports show::

    Number of Multicast MAC address added: 0

Test case 1: one multicast address
==================================
1. send packets::

    sendp([Ether(dst="33:33:00:00:00:01")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:40:10:01")/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="FE:ED:84:92:64:DD")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="5E:8E:8B:4D:89:05")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   the pkt1-2 can't be received, pkt3 is received by port 0, pkt4 is received by port 1.

2. configure multicast address::

    mcast_addr add 0 33:33:00:00:00:01

3. show multicast address of port 0 and port 1::

    testpmd> show port 0 mcast_macs
    Number of Multicast MAC address added: 1
      33:33:00:00:00:01
    testpmd> show port 1 mcast_macs
    Number of Multicast MAC address added: 0

4. send same packets, pkt1 can be received by port 0, other packets get same result.

5. remove the multicast address configuration::

    mcast_addr remove 0 33:33:00:00:00:01

6. show multicast address of port 0 and port 1::

    testpmd> show port 0 mcast_macs
    Number of Multicast MAC address added: 0
    testpmd> show port 1 mcast_macs
    Number of Multicast MAC address added: 0

7. send same packets, get same result to step 1.

Test Case 2: two multicast address
==================================
1. send packets::

    sendp([Ether(dst="33:33:00:00:00:01")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:40:10:01")/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="FE:ED:84:92:64:DD")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="5E:8E:8B:4D:89:05")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   the pkt1-2 can't be received, pkt3 is received by port 0, pkt4 is received by port 1.

2. configure two multicast address::

    mcast_addr add 0 33:33:00:00:00:01
    mcast_addr add 0 33:33:00:40:10:01

3. show multicast address of port 0 and port 1::

    testpmd> show port 0 mcast_macs
    Number of Multicast MAC address added: 2
      33:33:00:00:00:01
      33:33:00:40:10:01
    testpmd> show port 1 mcast_macs
    Number of Multicast MAC address added: 0

4. send same packets, pkt1-2 can be received by queue 0, other packets get same result.

5. remove one multicast address configuration::

    mcast_addr remove 0 33:33:00:00:00:01

6. show multicast address of port 0 and port 1::

    testpmd> show port 0 mcast_macs
    Number of Multicast MAC address added: 1
      33:33:00:40:10:01
    testpmd> show port 1 mcast_macs
    Number of Multicast MAC address added: 0

7. send same packets, pkt1 can't be received, pkt2 can be received by port 0, other packets get same result.

Test Case 3: configure multicast address on two vf ports
========================================================
1. configure multicast address on port 0 and port 1::

    mcast_addr add 0 33:33:00:00:00:01
    mcast_addr add 1 33:33:00:00:00:01
    mcast_addr add 0 33:33:00:00:00:02
    mcast_addr add 1 33:33:00:00:00:03

2. show multicast address of port 0 and port 1::

    testpmd>  show port 0 mcast_macs
    Number of Multicast MAC address added: 2
      33:33:00:00:00:01
      33:33:00:00:00:02
    testpmd>  show port 1 mcast_macs
    Number of Multicast MAC address added: 2
      33:33:00:00:00:01
      33:33:00:00:00:03

3. send packets::

    sendp([Ether(dst="33:33:00:00:00:01")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:02")/IP(src="224.0.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:03")/IP(src="224.0.0.3")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   check pkt1 can be received by port 0 and port 1.
   pkt2 can be received by port 0.
   pkt3 can be received by port 1.

4. remove some configurations::

    mcast_addr remove 0 33:33:00:00:00:01
    mcast_addr remove 1 33:33:00:00:00:03

5. show multicast address of port 0 and port 1::

    testpmd> show port 0 mcast_macs
    Number of Multicast MAC address added: 1
      33:33:00:00:00:02
    testpmd> show port 1 mcast_macs
    Number of Multicast MAC address added: 1
      33:33:00:00:00:01

6. send same packets,
   check pkt1 can be only received by port 1.
   pkt2 can be received by port 0.
   pkt3 can't be received by any port.

Test Case 4: maxnum multicast address on two ports with vf trust off
====================================================================
1. set two VFs trust off::

    ip link set enp134s0f0 vf 0 trust off
    ip link set enp134s0f0 vf 1 trust off

2. configure 16 multicast address on port 0 and port 1::

    mcast_addr add 0 33:33:00:00:00:01
    mcast_addr add 0 33:33:00:00:00:02
    ......
    mcast_addr add 0 33:33:00:00:00:0f
    mcast_addr add 0 33:33:00:00:00:10
    mcast_addr add 1 33:33:00:00:00:01
    mcast_addr add 1 33:33:00:00:00:02
    ......
    mcast_addr add 1 33:33:00:00:00:0f
    mcast_addr add 1 33:33:00:00:00:10

   check all the settings are successful.

3. configure one more multicast address on each port::

    mcast_addr add 0 33:33:00:00:00:11
    iavf_execute_vf_cmd(): No response or return failure (-5) for cmd 10
    iavf_add_del_mc_addr_list(): fail to execute command OP_ADD_ETH_ADDR
    rte_eth_dev_set_mc_addr_list(port=0, nb=17) failed. diag=-1
    mcast_addr add 1 33:33:00:00:00:11
    iavf_execute_vf_cmd(): No response or return failure (-5) for cmd 10
    iavf_add_del_mc_addr_list(): fail to execute command OP_ADD_ETH_ADDR
    rte_eth_dev_set_mc_addr_list(port=1, nb=17) failed. diag=-1

   check there are still original 16 sets on both port 0 and port 1:

    testpmd> show port 0 mcast_macs
    testpmd> show port 1 mcast_macs

4. send packets::

    sendp([Ether(dst="33:33:00:00:00:01")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:02")/IP(src="224.0.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:03")/IP(src="224.0.0.3")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:04")/IP(src="224.0.0.4")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:05")/IP(src="224.0.0.5")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:06")/IP(src="224.0.0.6")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:07")/IP(src="224.0.0.7")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:08")/IP(src="224.0.0.8")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:09")/IP(src="224.0.0.9")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:0a")/IP(src="224.0.0.10")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:0b")/IP(src="224.0.0.11")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:0c")/IP(src="224.0.0.12")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:0d")/IP(src="224.0.0.13")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:0e")/IP(src="224.0.0.14")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:0f")/IP(src="224.0.0.15")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:10")/IP(src="224.0.0.16")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:11")/IP(src="224.0.0.17")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   check the packet, only the last packet can't be received by port 0 and port 1.
   other packets can be received both by port 0 and port 1.

5. remove one multicast address on port 0::

    mcast_addr remove 0 33:33:00:00:00:0b

   remove a multicast address on port 1::

    mcast_addr remove 1 33:33:00:00:00:01

5. connfigure the failed configuration again::

    mcast_addr add 0 33:33:00:00:00:11
    mcast_addr add 1 33:33:00:00:00:11

   the multicast address can be configured successfully.

6. send the same packets again, check the packet::

    sendp([Ether(dst="33:33:00:00:00:0b")/IP(src="224.0.0.11")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   can't be received by port 0, but can be received by port 1.
   check the packet::

    sendp([Ether(dst="33:33:00:00:00:01")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   can't be received by port 1, but can be received by port 0.
   other packets can be received by port 0 and port 1.

7. remove all the multicast address configuration on two ports::

    mcast_addr remove 0 33:33:00:00:00:01
    mcast_addr remove 0 33:33:00:00:00:02
    ......
    mcast_addr remove 0 33:33:00:00:00:11
    mcast_addr remove 1 33:33:00:00:00:02
    mcast_addr remove 1 33:33:00:00:00:03
    ......
    mcast_addr remove 1 33:33:00:00:00:11

   check all the packets can't be received by two ports.

Test Case 5: maxnum multicast address with vf trust on
======================================================
1. set two VFs trust on::

    ip link set enp134s0f0 vf 0 trust on
    ip link set enp134s0f0 vf 1 trust on

2. configure 64 multicast address on port 0 and port 1::

    mcast_addr add 0 33:33:00:00:00:00
    mcast_addr add 0 33:33:00:00:00:01
    ......
    mcast_addr add 0 33:33:00:00:00:3F
    mcast_addr add 1 33:33:00:00:00:00
    mcast_addr add 1 33:33:00:00:00:01
    ......
    mcast_addr add 1 33:33:00:00:00:3F

   show multicast address of port 0 and port 1::

    show port 0 mcast_macs
    show port 1 mcast_macs

   both of ports show::

    Number of Multicast MAC address added: 64

3. configure one more multicast address::

    testpmd> mcast_addr add 1 33:33:00:00:00:40
    rte_eth_dev_set_mc_addr_list(port=1, nb=65) failed. diag=-22
    testpmd> mcast_addr add 0 33:33:00:00:00:40
    rte_eth_dev_set_mc_addr_list(port=0, nb=65) failed. diag=-22

   check there are still original 64 sets on both port 0 and port 1:

4. send packets::

    sendp([Ether(dst="33:33:00:00:00:00")/IP(src="224.0.0.0")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:01")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    ......
    sendp([Ether(dst="33:33:00:00:00:3f")/IP(src="224.0.0.63")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:40")/IP(src="224.0.0.64")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   check the packet, only the last packet can't be received by port 0 and port 1.
   other packets can be received both by port 0 and port 1.

5. remove one multicast address on port 0::

    mcast_addr remove 0 33:33:00:00:00:0b

   remove a multicast address on port 1::

    mcast_addr remove 1 33:33:00:00:00:01

6. connfigure the failed configuration again::

    mcast_addr add 0 33:33:00:00:00:40
    mcast_addr add 1 33:33:00:00:00:40

   the multicast address can be configured successfully.

7. send the same packets again, check the packet::

    sendp([Ether(dst="33:33:00:00:00:0b")/IP(src="224.0.0.11")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   can't be received by port 0, but can be received by port 1.
   check the packet::

    sendp([Ether(dst="33:33:00:00:00:01")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   can't be received by port 1, but can be received by port 0.
   other packets can be received by port 0 and port 1.

8. remove all the multicast address configuration on port 0::

    mcast_addr remove 0 33:33:00:00:00:00
    mcast_addr remove 0 33:33:00:00:00:01
    ......
    mcast_addr remove 0 33:33:00:00:00:3F
    mcast_addr remove 0 33:33:00:00:00:40

   send the same packets again,
   port 0 can't receive any of the packets.
   port 1 can receive all the packets except::

    sendp([Ether(dst="33:33:00:00:00:01")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

9. remove all the multicast address on port 1, send the same packets again,
   port 0 and port 1 can't receive any of the packets.

Test Case 6: set allmulti on
============================
1. set allmulti on and promisc off after launch testpmd::

    set promisc all off
    set allmulti all on

2. send multicast and unicast packets::

    sendp([Ether(dst="33:33:00:00:00:01")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:01")/Dot1Q(vlan=1)/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:40:10:01")/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:40:10:01")/Dot1Q(vlan=2)/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="FE:ED:84:92:64:DD")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="5E:8E:8B:4D:89:05")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="FE:ED:84:92:64:DE")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   the pkt1-4 can be received by port 0 and port 1, pkt5 is received by port 0, pkt6 is received by port 1.
   pkt7 can't be received by any port.

3. set allmulti off and promisc on::

    set promisc all on
    set allmulti all off

4. send same packets, the pkt1-4 can't be received by port 0 and port 1,
   pkt5-7 can be received by both port 0 and port 1.

Test Case 7: negative case
==========================
1. send packet::

    sendp([Ether(dst="33:33:00:00:00:40")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   check the packet cannot be received by port 0.

2. add a multicast address::

    testpmd> mcast_addr add 0 33:33:00:00:00:40

3. send the packet again, check the packet can be received by port 0.

4. add a same multicast address::

    testpmd> mcast_addr add 0 33:33:00:00:00:40
    multicast address already filtered by port

5. send the packet again, check the packet can be received by port 0.

6. remove nonexistent multicast address::

    testpmd> mcast_addr remove 0 33:33:00:00:00:41
    multicast address not filtered by port 0

7. send the packet again, check the packet can be received by port 0.

8. add wrong multicast address::

    testpmd> mcast_addr add 0 32:33:00:00:00:41
    Invalid multicast addr 32:33:00:00:00:41

9. send the packet again, check the packet can be received by port 0.

10.remove the multicast address::

    mcast_addr remove 0 33:33:00:00:00:40

11.send the packet again, check the packet cannot be received by port 0.

Test Case 8: set vlan filter on
===============================
1. send multicast packets with/without vlan ID::

    sendp([Ether(dst="33:33:00:00:00:01")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:00:00:01")/Dot1Q(vlan=1)/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:40:10:01")/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")
    sendp([Ether(dst="33:33:00:40:10:01")/Dot1Q(vlan=1)/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f1")

   the pkt1-4 can't be received by any port.

2. configure multicast address::

    mcast_addr add 0 33:33:00:00:00:01

3. show multicast address of port 0 and port 1::

    testpmd> show port 0 mcast_macs
    Number of Multicast MAC address added: 1
      33:33:00:00:00:01
    testpmd> show port 1 mcast_macs
    Number of Multicast MAC address added: 0

4. send same packets, pkt1 can be received by port 0, other packets get same result.

5. set vlan filter on::

    vlan set filter on 0
    rx_vlan add 1 0

   send same packets, pkt1-2 can be received by port 0, other packets can't be received by any port.

6. remove the vlan filter::

    rx_vlan rm 1 0

   send same packets, pkt1 can be received by port 0, other packets can't be received by any port.

7. remove the multicast address configuration::

    mcast_addr remove 0 33:33:00:00:00:01

8. show multicast address of port 0 and port 1::

    testpmd> show port 0 mcast_macs
    Number of Multicast MAC address added: 0
    testpmd> show port 1 mcast_macs
    Number of Multicast MAC address added: 0

9. send same packets, the pkt1-4 can't be received by any port.
