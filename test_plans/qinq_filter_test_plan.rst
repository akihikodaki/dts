.. Copyright (c) <2011-2017>, Intel Corporation
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
Cloud filters for QinQ steering
===============================
This document provides test plan for testing the function of Fortville:
QinQ filter function

Prerequisites
=============
1.Hardware:
   Fortville
   HarborChannel_DP_OEMGEN_8MB_J24798-001_0.65_80002DA4 
   firmware-version: 5.70 0x80002da4 1.3908.0(fortville 25G) or 6.0.0+
   
2.Software: 
  dpdk: http://dpdk.org/git/dpdk
  scapy: http://www.secdev.org/projects/scapy/
  disable vector mode when build dpdk

Test Case 1: test qinq packet type
==================================

Testpmd configuration - 4 RX/TX queues per port
------------------------------------------------

#. set up testpmd with fortville NICs::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x1f -n 4 -- -i --rxq=4 --txq=4 --txqflags=0x0  --disable-rss

#. enable qinq::

    testpmd command: vlan set qinq on 0
      
#. PMD fwd only receive the packets::

    testpmd command: set fwd rxonly
      
#. verbose configuration::

    testpmd command: set verbose 1
      
#. start packet receive::

    testpmd command: start

tester Configuration
-------------------- 

#. send dual vlan packet with scapy, verify it can be recognized as qinq packet::

    sendp([Ether(dst="3C:FD:FE:A3:A0:AE")/Dot1Q(type=0x8100,vlan=2)/Dot1Q(type=0x8100,vlan=3)/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x' * 20)], iface="eth17")

Test Case 2: qinq packet filter to PF queues
============================================

Testpmd configuration - 4 RX/TX queues per port
-----------------------------------------------

#. set up testpmd with fortville NICs::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x1f -n 4 -- -i --rxq=4 --txq=4 --txqflags=0x0  --disable-rss

#. enable qinq::

    testpmd command: vlan set qinq on 0
      
#. PMD fwd only receive the packets::

    testpmd command: set fwd rxonly
      
#. verbose configuration::

    testpmd command: set verbose 1
      
#. start packet receive::

    testpmd command: start

#. create filter rules::

    testpmd command: flow create 0 ingress pattern eth / vlan tci is 1 / vlan tci is 4093 / end actions pf / queue index 1 / end
    testpmd command: flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 4094 / end actions pf / queue index 2 / end

tester Configuration
-------------------- 

#. send dual vlan packet with scapy, verify packets can filter to queues::

    sendp([Ether(dst="3C:FD:FE:A3:A0:AE")/Dot1Q(type=0x8100,vlan=1)/Dot1Q(type=0x8100,vlan=4093)/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x' * 20)], iface="eth17")
    sendp([Ether(dst="3C:FD:FE:A3:A0:AE")/Dot1Q(type=0x8100,vlan=2)/Dot1Q(type=0x8100,vlan=4093)/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x' * 20)], iface="eth17")

Test Case 3: qinq packet filter to VF queues
============================================
#. create VF on dut::

    linux cmdline: echo 2 > /sys/bus/pci/devices/0000:81:00.0/max_vfs

#. bind igb_uio to vfs

    linux cmdline: ./usertools/dpdk-devbind.py -b igb_uio 81:02.0 81:02.1
 
#. set up testpmd with fortville PF NICs::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x1f -n 4 --socket-mem=1024,1024 --file-prefix=pf -w 81:00.0 -- -i --rxq=4 --txq=4 --txqflags=0x0

#. enable qinq::

    testpmd command: vlan set qinq on 0
      
#. PMD fwd only receive the packets::

    testpmd command: set fwd rxonly
      
#. verbose configuration::

    testpmd command: set verbose 1
      
#. start packet receive::

    testpmd command: start
       
#. create filter rules::
 
    testpmd command: flow create 0 ingress pattern eth / vlan tci is 1 / vlan tci is 4093 / end actions vf id 0 / queue index 2 / end
    testpmd command: flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 4094 / end actions vf id 1 / queue index 3 / end
    testpmd command: flow create 0 ingress pattern eth / vlan tci is 3 / vlan tci is 4094 / end actions pf / queue index 1 / end

#. set up testpmd with fortville VF0 NICs::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x3e0 -n 4 --socket-mem=1024,1024 --file-prefix=vf0 -w 81:02.0 -- -i --rxq=4 --txq=4 --rss-udp

#. PMD fwd only receive the packets::

    testpmd command: set fwd rxonly
      
#. verbose configuration::

    testpmd command: set verbose 1
      
#. start packet receive::

    testpmd command: start

#. set up testpmd with fortville VF0 NICs::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7c0 -n 4 --socket-mem=1024,1024 --file-prefix=vf1 -w 81:02.0 -- -i --rxq=4 --txq=4 --rss-udp

#. PMD fwd only receive the packets::

    testpmd command: set fwd rxonly
      
#. verbose configuration::

    testpmd command: set verbose 1
      
#. start packet receive::

    testpmd command: start
    
tester Configuration
-------------------- 

#. send dual vlan packet with scapy, verify packets can filter to the corresponding PF and VF queues::

    sendp([Ether(dst="3C:FD:FE:A3:A0:AE")/Dot1Q(type=0x8100,vlan=1)/Dot1Q(type=0x8100,vlan=4094)/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x' * 20)], iface="eth17")
    sendp([Ether(dst="3C:FD:FE:A3:A0:AE")/Dot1Q(type=0x8100,vlan=2)/Dot1Q(type=0x8100,vlan=4094)/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x' * 20)], iface="eth17")
    sendp([Ether(dst="3C:FD:FE:A3:A0:AE")/Dot1Q(type=0x8100,vlan=3)/Dot1Q(type=0x8100,vlan=4094)/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x' * 20)], iface="eth17")

Test Case 4: qinq packet filter with diffierent tpid
====================================================
#. create VF on dut::

    linux cmdline: echo 2 > /sys/bus/pci/devices/0000:81:00.0/max_vfs

#. bind igb_uio to vfs

    linux cmdline: ./usertools/dpdk-devbind.py -b igb_uio 81:02.0 81:02.1
 
#. set up testpmd with fortville PF NICs::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x1f -n 4 --socket-mem=1024,1024 --file-prefix=pf -w 81:00.0 -- -i --rxq=4 --txq=4 --txqflags=0x0

#. enable qinq::

    testpmd command: vlan set qinq on 0
      
#. PMD fwd only receive the packets::

    testpmd command: set fwd rxonly
      
#. verbose configuration::

    testpmd command: set verbose 1
      
#. start packet receive::

    testpmd command: start

#. change S-Tag+C-Tag VLAN TPIDs to 0x88A8 + 0x8100::

    testpmd command: vlan set outer tpid 0x88a8 0

#. create filter rules::
 
    testpmd command: flow create 0 ingress pattern eth / vlan tci is 1 / vlan tci is 4093 / end actions vf id 0 / queue index 2 / end
    testpmd command: flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 4094 / end actions vf id 1 / queue index 3 / end
    testpmd command: flow create 0 ingress pattern eth / vlan tci is 3 / vlan tci is 4094 / end actions pf / queue index 1 / end

#. set up testpmd with fortville VF0 NICs::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x3e0 -n 4 --socket-mem=1024,1024 --file-prefix=vf0 -w 81:02.0 -- -i --rxq=4 --txq=4 --rss-udp

#. PMD fwd only receive the packets::

    testpmd command: set fwd rxonly
      
#. verbose configuration::

    testpmd command: set verbose 1
      
#. start packet receive::

    testpmd command: start

#. set up testpmd with fortville VF0 NICs::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7c0 -n 4 --socket-mem=1024,1024 --file-prefix=vf1 -w 81:02.0 -- -i --rxq=4 --txq=4 --rss-udp

#. PMD fwd only receive the packets::

    testpmd command: set fwd rxonly
      
#. verbose configuration::

    testpmd command: set verbose 1
      
#. start packet receive::

    testpmd command: start

tester Configuration
-------------------- 

#. send dual vlan packet with scapy, verify packets can filter to the corresponding VF queues::    
7. send qinq packet with traffic generator, verify packets can filter to the corresponding VF queues.

Note
====================================================

#. How to send packet with specific TPID with scapy::

    1. wrpcap("qinq.pcap",[Ether(dst="3C:FD:FE:A3:A0:AE")/Dot1Q(type=0x8100,vlan=1)/Dot1Q(type=0x8100,vlan=4092)/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x' * 20)]).
    2. hexedit qinq.pcap; change tpid field, "ctrl+w" to save, "ctrl+x" to exit.
    3. sendp(rdpcap("qinq.pcap"), iface="eth17").
