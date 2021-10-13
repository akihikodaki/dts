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

========================
CVL Limit Value Test
========================

Description
===========

Supported function type
-----------------------

    validate
    create
    destroy
    flush
    list

Supported action type
---------------------

    queue index
    drop
    rss queues
    passthru
    mark
    mark/rss

Prerequisites
=============

1. Hardware:
   columbiaville_25g/columbiaville_100g

2. Software:
   DPDK: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Support ice pkg::

    os default/comms/wireless

4. Generate 2 VFs on each PF and set mac address for each VF::

    echo 2 > /sys/bus/pci/devices/0000:86:00.0/sriov_numvfs
    echo 2 > /sys/bus/pci/devices/0000:86:00.1/sriov_numvfs
    ip link set enp134s0f0 vf 0 mac 00:11:22:33:44:55
    ip link set enp134s0f0 vf 1 mac 00:11:22:33:44:66
    ip link set enp134s0f1 vf 0 mac 00:11:22:33:44:77
    ip link set enp134s0f1 vf 1 mac 00:11:22:33:44:88

   0000:86:00.0 generate 0000:86:01.0 and 0000:86:01.1
   0000:86:00.1 generate 0000:86:11.0 and 0000:86:11.1
   define 86:01.0 as vf00, 86:01.1 as vf01, 86:11.0 as vf10, 86:11.1 as vf11.
   assign mac address of pf0 is 68:05:ca:a3:1a:60,
   assign mac address of pf1 is 68:05:ca:a3:1a:61.

5. Bind VFs to dpdk driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 86:01.0 86:01.1 86:11.0 86:11.1

5. Launch the app ``testpmd`` with the following arguments::

    ./testpmd -c 0xff -n 6 -a 86:01.0 -a 86:01.1 --file-prefix=vf -- -i --rxq=16 --txq=16
    testpmd> set fwd rxonly
    testpmd> set verbose 1

6. on tester side, copy the layer python file to /root::

    cp pfcp.py to /root

   then import layers when start scapy::

    >>> import sys
    >>> sys.path.append('/root')
    >>> from pfcp import PFCP
    >>> from scapy.contrib.gtp import *
    >>> from scapy.contrib.mpls import *

Test case: Max number
======================

All the max number cases are designed based on 2*100G NIC.
If the hardware is 4*25G NIC, the guaranteed rule number of PF is 512.
So in subcase 3 and subcase 4, there can be created at most 14848 rules on 1pf and 2vfs.

Subcase 1: 14336 rules on 1 vf
-------------------------------

1. create 14336 rules on vf00::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.0 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / end actions queue index 1 / mark / end
    ......
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.55.255 / end actions queue index 1 / mark / end

   all the rules are created successfully.

2. create one more rule::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.56.0 / end actions queue index 1 / mark / end

   the rule failed to create. return the error message.

3. check the rule list, there are 14336 rules listed.

4. send matched packets for rule 0 and rule 14335::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.0")/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.55.255")/Raw('x' * 80)],iface="enp134s0f1")

   check all packets are redirected to expected queue with FDIR matched ID=0x0

5. create a rule on vf01, it failed,
   check the error message, the rule number has expired the max rule number.

6. create a rule on vf10, it failed,
   check the error message, the rule number has expired the max rule number.

7. flush all the rules, check the rule list,
   there is no rule listed.

8. verify matched packets for rule 0  and rule 14335 received without FDIR matched ID.

Subcase 2: 14336 rules on 2 vfs of 2pfs
---------------------------------------
For chapman beach 100g*2 NIC, if 2 vfs generated by one pf port,they will share 14336 rules,
if 2 vfs generated by 2 pf port, each vf can create 14336 rules at most.

1. start testpmd on vf00::

    ./testpmd -c 0xf -n 6 -a 86:01.0 --file-prefix=vf00 -- -i --rxq=4 --txq=4

   create 1 rule on vf00::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.0 / end actions queue index 1 / mark / end

   created successfully, check the rule is listed.

2. start testpmd on vf10::

    ./testpmd -c 0xf0 -n 6 -a 86:0a.0 --file-prefix=vf10 -- -i --rxq=4 --txq=4

   create 14336 rules on vf10::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.0 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / end actions queue index 1 / mark / end
    ......
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.55.255 / end actions queue index 1 / mark / end

   all the rules except the last one are created successfully.
   check the rule list, there listed 14335 rules.

3. send matched packet to vf00 and matched packet for rule 14334 to vf10,
   check all packets are redirected to expected queue with FDIR matched ID=0x0

4. flush all the rules, check the rule list,
   there is no rule listed.

5. verify matched packet received without FDIR matched ID.

Subcase 3: 1025 rules on 1pf and 14335 rules on 2vfs
----------------------------------------------------

each pf can create 1024 rules at least in 2 ports card.
each pf can create 512 rules at least in 4 ports card.
there are 14k rules shared by pfs and vfs.
so 1 pf and 2 vfs can create 15360 rules at most on 2 ports card.
1 pf and 2 vfs can create 14848 rules at most on 4 ports card.
if hardware is chapman beach 100g*2, 1 pf can create 2048 rules,vfs generated by the same pf share 14336 rules,so
this card can create (2048 + 14336)*2=32768 rules.

1. create 1025 rules on pf0::

    ethtool -N enp134s0f0 flow-type tcp4 src-ip 192.168.0.0 dst-ip 192.168.100.2 src-port 32 dst-port 33 action 8
    ethtool -N enp134s0f0 flow-type tcp4 src-ip 192.168.0.1 dst-ip 192.168.100.2 src-port 32 dst-port 33 action 8
    ......
    ethtool -N enp134s0f0 flow-type tcp4 src-ip 192.168.3.255 dst-ip 192.168.100.2 src-port 32 dst-port 33 action 8
    ethtool -N enp134s0f0 flow-type tcp4 src-ip 192.168.4.0 dst-ip 192.168.100.2 src-port 32 dst-port 33 action 8

   all the rules can be created successfully::

    Added rule with ID <Rule ID>

   List the rules on pf0::

    ethtool -n enp134s0f0

2. start testpmd on vf00::

    ./testpmd -c 0xf -n 6 -a 86:01.0 --file-prefix=vf00 -- -i --rxq=4 --txq=4

   create 1 rule on vf00::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.0 / end actions queue index 1 / mark / end

   created successfully, check the rule is listed.

2. start testpmd on vf10::

    ./testpmd -c 0xf0 -n 6 -a 86:0a.0 --file-prefix=vf10 -- -i --rxq=4 --txq=4

   create 14335 rules on vf10::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.0 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / end actions queue index 1 / mark / end
    ......
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.55.254 / end actions queue index 1 / mark / end

   all the rules except the last one are created successfully.
   check the rule list, there listed 14334 rules.

3. send matched packet to vf00 and matched packet for rule 14333 to vf10,
   check all packets are redirected to expected queue with FDIR matched ID=0x0

4. delete 1 rule on pf0::

    ethtool -N enp134s0f0 delete <Rule ID>

5. create one more rule on vf10::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.55.254 / end actions queue index 1 / mark / end

   the rule can be created successfully.

6. send matched packet to vf10, it can be redirected to queue 1 with FDIR matched ID=0x0.

7. flush all the rules, check the rule list,
   there is no rule listed.

8. verify matched packet received without FDIR matched ID.

Subcase 4: 15360 rules on 1pf and 0 rules on 2vfs
-------------------------------------------------

each pf can create 1024 rules at least in 2 ports card.
each pf can create 512 rules at least in 4 ports card.
there are 14k rules shared by pfs and vfs.
so 1 pf and 2 vfs can create 15360 rules at most on 2 ports card.
1 pf and 2 vfs can create 14848 rules at most on 4 ports card.
so if create 15360/14848 rules on 1 pf, there can't create rule on vf successfully.
if hardware is chapman beach 100g*2, 1 pf can create 2048 rules,vfs generated by the same pf share 14336 rules,
so if create 16384 rules on pf1,check failed to create rule on vf00 and vf10(vf00 and vf10 generated by pf1).

1. create 15360 rules on pf0::

    ethtool -N enp134s0f0 flow-type tcp4 src-ip 192.168.0.0 dst-ip 192.168.100.2 src-port 32 dst-port 33 action 8
    ethtool -N enp134s0f0 flow-type tcp4 src-ip 192.168.0.1 dst-ip 192.168.100.2 src-port 32 dst-port 33 action 8
    ......
    ethtool -N enp134s0f0 flow-type tcp4 src-ip 192.168.57.255 dst-ip 192.168.100.2 src-port 32 dst-port 33 action 8

   all the rules can be created successfully::

    Added rule with ID <Rule ID>

2. failed to create one more rule on pf0::

    ethtool -N enp134s0f0 flow-type tcp4 src-ip 192.168.58.0 dst-ip 192.168.100.2 src-port 32 dst-port 33 action 8

3. start testpmd on vf00 and vf10::

    ./testpmd -c 0xf -n 6 -a 86:01.0 -a 86:11.0 --file-prefix=vf00 -- -i --rxq=4 --txq=4

   create 1 rule on vf00::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.0 / end actions queue index 1 / mark / end

   failed to create the rule, check there is no rule listed.

   create 1 rule on vf10::

    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.0 / end actions queue index 1 / mark / end

   failed to create the rule, check there is no rule listed.

4. delete 1 rule on pf0::

    ethtool -N enp134s0f0 delete <Rule ID>

5. create 1 rule on vf00::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.55.254 / end actions queue index 1 / mark / end

   the rule can be created successfully.

   create 1 rule on vf10::

    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.0 / end actions queue index 1 / mark / end

   failed to create the rule, check there is no rule listed.

6. send matched packet to vf00, it can be redirected to queue 1 with FDIR matched ID=0x0.
   send matched packet to vf10, it is received without FDIR matched ID.

7. delete 1 more rule on pf0::

    ethtool -N enp134s0f0 delete <Rule ID>

8. create 1 rule on vf10::

    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.0 / end actions queue index 1 / mark / end

   the rule can be created successfully.

9. send matched packet to vf00, it can be redirected to queue 1 with FDIR matched ID=0x0.
   send matched packet to vf10, it can be redirected to queue 1 with FDIR matched ID=0x0.

Test case: Stress test
======================

Subcase 1: add/delete rules
---------------------------

1. create two rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / mark id 1 / end

   return the message::

    Flow rule #0 created
    Flow rule #1 created

   list the rules::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => QUEUE MARK
    1       0       0       i--     ETH IPV4 TCP => RSS MARK

2. delete the rules::

    testpmd> flow flush 0

3. repeat the create and delete operations in step1-2 14336 times.

4. create the two rules one more time, check the rules listed.

5. send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   check packet 1 is redirected to queue 1 with FDIR matched ID=0x0
   check packet 2 is redirected to queue 2 or queue 3 with FDIR matched ID=0x1

Subcase 2: add/delete rules on two VFs
--------------------------------------

1. create a rule on each vf::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / end

   return the message::

    Flow rule #0 created
    Flow rule #0 created

   list the rules::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 TCP => QUEUE
    testpmd> flow list 1
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 TCP => QUEUE

2. delete the rules::

    flow destroy 0 rule 0
    flow destroy 1 rule 0

3. repeate the create and delete operations in step1-2 14336 times with different IP src address.

4. create the rule on each vf one more time, check the rules listed::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / end

5. send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.56.0",dst="192.1.0.0",tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:66")/IP(src="192.168.56.0",dst="192.1.0.0",tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   check the packet is redirected to queue 5 of two vfs.

Prerequisites
=============

1. Hardware:
   columbiaville_25g/columbiaville_100g
   design the cases with 2 ports card.

2. Software:
   DPDK: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Copy specific ice package to /lib/firmware/intel/ice/ddp/ice.pkg
   Then reboot server, and compile DPDK

4. Bind the pf to dpdk driver::

    ./usertools/dpdk-devbind.py -b igb_uio 86:00.0 86:00.1

5. Launch the app ``testpmd`` with the following arguments::

    ./testpmd -c 0xff -n 6 -a 86:00.0 --log-level="ice,7" -- -i --portmask=0xff --rxq=64 --txq=64 --port-topology=loop
    testpmd> set fwd rxonly
    testpmd> set verbose 1

   If set UDP tunnel flow rule::

    testpmd> port config 0 udp_tunnel_port add vxlan 4789
    testpmd> start

   Notes: if need two ports environment, launch ``testpmd`` with the following arguments::

    ./testpmd -c 0xff -n 6 -a 86:00.0 -a 86:00.1 --log-level="ice,7" -- -i --portmask=0xff --rxq=64 --txq=64 --port-topology=loop

Test case: add/delete rules
============================

1. create two rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / mark id 1 / end

   return the message::

    Flow rule #0 created
    Flow rule #1 created

   list the rules::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => QUEUE MARK
    1       0       0       i--     ETH IPV4 TCP => RSS MARK

2. delete the rules::

    testpmd> flow flush 0

3. repeate the create and delete operations in step1-2 15360 times.

4. create the two rules one more time, check the rules listed.

5. send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")

   check packet 1 is redirected to queue 1 with FDIR matched ID=0x0
   check packet 2 is redirected to queue 2 or queue 3 with FDIR matched ID=0x1

Prerequisites
=============

1. Hardware:
   columbiaville_25g/columbiaville_100g
   design the cases with 2 ports card.

2. Software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Copy specific ice package to /lib/firmware/updates/intel/ice/ddp/ice.pkg,
   then load driver::

     rmmod ice
     insmod ice.ko

4. Get the pci device id of DUT, for example::

     ./usertools/dpdk-devbind.py -s

     0000:18:00.0 'Device 1593' if=enp24s0f0 drv=ice unused=vfio-pci
     0000:18:00.1 'Device 1593' if=enp24s0f1 drv=ice unused=vfio-pci

5. Generate 4 VFs on PF0::

     echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

     ./usertools/dpdk-devbind.py -s
     0000:18:01.0 'Ethernet Adaptive Virtual Function 1889' if=enp24s1 drv=iavf unused=vfio-pci
     0000:18:01.1 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f1 drv=iavf unused=vfio-pci
     0000:18:01.2 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f2 drv=iavf unused=vfio-pci
     0000:18:01.3 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f3 drv=iavf unused=vfio-pci

6. Set VF0 as trust::

     ip link set enp24s0f0 vf 0 trust on

7. Bind VFs to dpdk driver::

     modprobe vfio-pci
     ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0 0000:18:01.1 0000:18:01.2 0000:18:01.3

8. Launch dpdk on VF0 and VF1, and VF0 request DCF mode::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf -a 0000:18:01.1 -- -i
     testpmd> set portlist 1
     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start
     testpmd> show port info all

   check the VF0 driver is net_ice_dcf.

9. on tester side, copy the layer python file to /root::

      cp pfcp.py to /root

    then import layers when start scapy::

      >>> import sys
      >>> sys.path.append('/root')
      >>> from pfcp import PFCP
      >>> from scapy.contrib.igmp import *

Test case: max rule number
==========================

Description: 32k switch filter rules can be created on a CVL card,
and all PFs and VFs share the 32k rules. But the system will first create
some MAC_VLAN rules in switch table, and as the number of rules increased,
the hash conflicts in the switch filter table are increased, so we can
create a total of 32500 switch filter rules on a DCF.

1. create 32500 rules with the same pattern, but different input set::

     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions vf id 1 / end
     ......
     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.127.114 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rules exist in the list.

2. create one more rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.127.178 / end actions vf id 1 / end

   check the rule can not be created successfully, and
   testpmd provide a friendly output, showing::

     ice_flow_create(): Failed to create flow
     port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): switch filter create flow fail: Invalid argument

3. check the rule list

     testpmd> flow list 0

   check the rule in step 2 not exists in the list.

4. send 32500 matched packets for rule 0-32499::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.0")/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1")/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
     ......
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.127.114")/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)

   check port 1 receive the 32500 packets.
   send 1 mismatched packet::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.167.0.1")/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)

   check the packet are not to port 1.

5. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send 32500 matched packets, check the packets are not to port 1.
