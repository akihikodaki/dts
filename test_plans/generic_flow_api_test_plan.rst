.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2016 Intel Corporation

=======================
Generic filter/flow api
=======================

Prerequisites
=============

1. Hardware:
   Intel® Ethernet 700 Series, Intel® Ethernet 800 Series and 82599
  
2. software: 
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. bind the pf to dpdk driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 05:00.0
 
Note: validate the rules first before create it in each case.
All the rules that can be validated correctly should be created successfully.
The rules can't be validated correctly shouldn't be created successfully.

Test case: Intel® Ethernet 700 Series ethertype
===============================================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=16 --txq=16
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules::

    testpmd> flow validate 0 ingress pattern eth type is 0x0806 / end actions queue index 1 / end
    testpmd> flow create 0 ingress pattern eth type is 0x0806 / end actions queue index 2 / end
    testpmd> flow validate 0 ingress pattern eth type is 0x08bb / end actions queue index 16 / end
    testpmd> flow create 0 ingress pattern eth type is 0x88bb / end actions queue index 3 / end
    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 type is 0x88e5 / end actions queue index 4 / end
    testpmd> flow create 0 ingress pattern eth type is 0x8864 / end actions drop / end
    testpmd> flow validate 0 ingress pattern eth type is 0x88cc / end actions queue index 5 / end
    testpmd> flow create 0 ingress pattern eth type is 0x88cc / end actions queue index 6 / end

3. send packets::

    pkt1 = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.1.1")
    pkt2 = Ether(dst="00:11:22:33:44:55", type=0x88BB)/Raw('x' * 20)
    pkt3 = Ether(dst="00:11:22:33:44:55", type=0x88e5)/Raw('x' * 20)
    pkt4 = Ether(dst="00:11:22:33:44:55", type=0x8864)/Raw('x' * 20)
    pkt5 = Ether(dst="00:11:22:33:44:55", type=0x88cc)/Raw('x' * 20)

   verify pkt1 to queue 2, and pkt2 to queue 3, pkt3 to queue 4, pkt4 dropped, pkt5 to queue 6.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    verify pkt1 to queue 0, and pkt2 to queue 3, pkt3 to queue 4, pkt4 dropped, pkt5 to queue 6.
    testpmd> flow list 0
    testpmd> flow flush 0
    verify pkt1 to queue 0, and pkt2 to queue 0, pkt3 to queue 0, pkt4 to queue 0, pkt5 to queue 0.
    testpmd> flow list 0


Test case: Intel® Ethernet 700 Series fdir for L2 payload
=========================================================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. validate and create filter rules::

    testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / end actions queue index 1 / end
    testpmd> flow validate 0 ingress pattern eth type is 0x0807 / end actions queue index 2 / end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / end actions queue index 1 / end
    testpmd> flow create 0 ingress pattern eth type is 0x0807 / end actions queue index 2 / end

3. send packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/Raw('x' * 20)
    pkt2 = Ether(dst="00:11:22:33:44:55", type=0x0807)/Dot1Q(vlan=1)/Raw('x' * 20)
    pkt3 = Ether(dst="00:11:22:33:44:55", type=0x0807)/IP(src="192.168.0.5", dst="192.168.0.6")/Raw('x' * 20)

   check pkt1 to queue 1, pkt2 to queue 2, pkt3 to queue 2.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0


Test case: Intel® Ethernet 700 Series fdir for flexbytes
========================================================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. validate and create filter rules

   l2-payload::

    testpmd> flow create 0 ingress pattern eth type is 0x0807 / raw relative is 1 pattern is ab / end actions queue index 1 / end

   ipv4-other::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 4095 / ipv4 proto is 255 ttl is 40 / raw relative is 1 offset is 2 pattern is ab / raw relative is 1 offset is 10 pattern is abcdefghij / raw relative is 1 offset is 0 pattern is abcd / end actions queue index 2 / end

   ipv4-udp::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / udp src is 22 dst is 23 / raw relative is 1 offset is 2 pattern is fhds / end actions queue index 3 / end

   ipv4-tcp::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 tos is 4 ttl is 3 / tcp src is 32 dst is 33 / raw relative is 1 offset is 2 pattern is hijk / end actions queue index 4 / end

   ipv4-sctp::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / sctp src is 42 / raw relative is 1 offset is 2 pattern is abcdefghijklmnop / end actions queue index 5 / end

   ipv6-tcp::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / ipv6 src is 2001::1 dst is 2001::2 tc is 3 hop is 30 / tcp src is 32 dst is 33 / raw relative is 1 offset is 0 pattern is hijk / raw relative is 1 offset is 8 pattern is abcdefgh / end actions queue index 6 / end

   spec-mask(not supportted now, 6wind will update lately)
   restart testpmd, create new rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / tcp src is 32 dst is 33 / raw relative is 1 offset is 2 pattern spec \x61\x62\x63\x64 pattern mask \x00\x00\xff\x01 / end actions queue index 7 / end
 
3. send packets::

    pkt1 = Ether(dst="00:11:22:33:44:55", type=0x0807)/Raw(load="\x61\x62\x63\x64")
    pkt2 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=4095)/IP(src="192.168.0.1", dst="192.168.0.2", proto=255, ttl=40)/Raw(load="xxabxxxxxxxxxxabcdefghijabcdefg")
    pkt3 = Ether(dst="00:11:22:33:44:55")/IP(src="2.2.2.4", dst="2.2.2.5")/UDP(sport=22,dport=23)/Raw(load="fhfhdsdsfwef")
    pkt4 = Ether(dst="00:11:22:33:44:55")/IP(src="2.2.2.4", dst="2.2.2.5", tos=4, ttl=3)/TCP(sport=32,dport=33)/Raw(load="fhhijk")
    pkt5 = Ether(dst="00:11:22:33:44:55")/IP(src="2.2.2.4", dst="2.2.2.5")/SCTP(sport=42,dport=43,tag=1)/Raw(load="xxabcdefghijklmnopqrst")
    pkt6 = Ether(dst="00:11:22:33:44:55")/IP(src="2.2.2.4", dst="2.2.2.5")/SCTP(sport=42,dport=43,tag=1)/Raw(load="xxabxxxabcddxxabcdefghijklmn")
    pkt7 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="2001::1", dst="2001::2", tc=3, hlim=30)/TCP(sport=32,dport=33)/Raw(load="hijkabcdefghabcdefghijklmn")

   pkt8-pkt10 are not supported now::

    pkt8 = Ether(dst="00:11:22:33:44:55")/IP(src="2.2.2.4", dst="2.2.2.5")/TCP(sport=32,dport=33)/Raw(load="\x68\x69\x61\x62\x63\x64")
    pkt9 = Ether(dst="00:11:22:33:44:55")/IP(src="2.2.2.4", dst="2.2.2.5")/TCP(sport=32,dport=33)/Raw(load="\x68\x69\x68\x69\x63\x74")
    pkt10 = Ether(dst="00:11:22:33:44:55")/IP(src="2.2.2.4", dst="2.2.2.5")/TCP(sport=32,dport=33)/Raw(load="\x68\x69\x61\x62\x63\x65")

   check pkt1 to pkt5 are received by queue 1 to queue 5, pkt6 to queue 0,
   pkt7 to queue6. pkt8 to queue7, pkt8 and pkt9 to queue 0.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0

5. verify rules can be recreated successfully after deleted::

    testpmd> flow create 0 ingress pattern eth type is 0x0807 / raw relative is 1 pattern is ab / end actions queue index 1 / end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 4095 / ipv4 proto is 255 ttl is 40 / raw relative is 1 offset is 2 pattern is ab / raw relative is 1 offset is 10 pattern is abcdefghij / raw relative is 1 offset is 0 pattern is abcd / end actions queue index 2 / end
    testpmd> flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / udp src is 22 dst is 23 / raw relative is 1 offset is 2 pattern is fhds / end actions queue index 3 / end
    testpmd> flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 tos is 4 ttl is 3 / tcp src is 32 dst is 33 / raw relative is 1 offset is 2 pattern is hijk / end actions queue index 4 / end
    testpmd> flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / sctp src is 42 / raw relative is 1 offset is 2 pattern is abcdefghijklmnop / end actions queue index 5 / end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / ipv6 src is 2001::1 dst is 2001::2 tc is 3 hop is 30 / tcp src is 32 dst is 33 / raw relative is 1 offset is 0 pattern is hijk / raw relative is 1 offset is 8 pattern is abcdefgh / end actions queue index 6 / end

Test case: Intel® Ethernet 700 Series fdir for ipv4
===================================================

Subcase1: fdir for ipv4 (DPDK PF)
---------------------------------

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. validate and create the filter rules::

    testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 157.141.168.166 src is 86.233.197.55 proto is 255  / end actions queue index 2 /  end
    testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 144.91.80.195 src is 244.178.159.128 ttl is 131 / udp dst is 63365 src is 62851  / end actions queue index 2 /  end
    testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 38.114.30.109 src is 42.1.193.75 tos is 93 / tcp dst is 9460 src is 58942  / end actions queue index 3 /  end
    testpmd> flow validate 0 ingress pattern eth / vlan tci is 3691 / ipv4 dst is 58.172.170.63 src is 203.118.95.141 tos is 211 ttl is 56 / sctp dst is 51725 src is 43652 tag is 1  / end actions queue index 8 /  end
    testpmd> flow validate 0 ingress pattern eth / vlan tci is 434 / ipv4 dst is 71.116.114.22 src is 173.153.191.177 tos is 2 ttl is 37 / sctp dst is 17941 src is 38115 tag is 1  / end actions drop /  end
    testpmd> flow validate 0 ingress pattern eth / vlan tci is 3287 / ipv4 dst is 219.249.106.92 src is 42.187.118.192 tos is 25 ttl is 161 / sctp dst is 5762 src is 58896 tag is 1  / end actions passthru / flag /  end
    testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 29.191.154.55 src is 69.31.207.25 ttl is 134 / udp dst is 997 src is 42348  / end actions queue index 1 / flag /  end
    testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 53.166.31.5 src is 158.221.82.64 tos is 90 / tcp dst is 28429 src is 36277  / end actions queue index 7 / mark id 3 /  end
    testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 195.39.132.177 src is 65.239.163.18 proto is 255  / end actions passthru / mark id 3 /  end

    testpmd> flow create 0 ingress pattern eth / ipv4 dst is 33.178.41.216 src is 157.159.41.179 proto is 255  / end actions queue index 1 /  end
    testpmd> flow create 0 ingress pattern eth / ipv4 dst is 141.4.179.232 src is 38.102.237.108 ttl is 47 / udp dst is 50235 src is 55057  / end actions queue index 2 /  end
    testpmd> flow create 0 ingress pattern eth / ipv4 dst is 109.167.0.48 src is 2.233.109.45 tos is 130 / tcp dst is 20779 src is 64541  / end actions queue index 3 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 1881 / ipv4 dst is 100.140.14.188 src is 210.226.229.15 tos is 105 ttl is 190 / sctp dst is 62829 src is 39503 tag is 1  / end actions queue index 4 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 3893 / ipv4 dst is 141.77.203.35 src is 99.49.193.226 tos is 227 ttl is 22 / sctp dst is 33682 src is 22991 tag is 1  / end actions drop /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 1575 / ipv4 dst is 160.99.116.93 src is 123.114.110.144 tos is 21 ttl is 72 / sctp dst is 31363 src is 34136 tag is 1  / end actions passthru / flag /  end
    testpmd> flow create 0 ingress pattern eth / ipv4 dst is 213.99.143.236 src is 55.130.28.195 ttl is 201 / udp dst is 25119 src is 31609  / end actions queue index 5 / flag /  end
    testpmd> flow create 0 ingress pattern eth / ipv4 dst is 224.12.140.222 src is 118.34.141.171 tos is 41 / tcp dst is 32602 src is 17691  / end actions queue index 6 / mark id 3 /  end
    testpmd> flow create 0 ingress pattern eth / ipv4 dst is 124.168.113.3 src is 253.237.216.240 proto is 255  / end actions passthru / mark id 3 /  end

3. send packets::

    pkt1 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP(dst='33.178.41.216', src='157.159.41.179', proto=255)/Raw('x' * 20)
    pkt2 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP(dst='141.4.179.232', src='38.102.237.108', ttl=47)/UDP(dport=50235, sport=55057)/Raw('x' * 20)
    pkt3 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP(dst='109.167.0.48', src='2.233.109.45', tos=130)/TCP(dport=20779, sport=64541)/Raw('x' * 20)
    pkt4 = Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=1881)/IP(dst='100.140.14.188', src='210.226.229.15', tos=105, ttl=190)/SCTP(dport=62829, sport=39503, tag=1)/Raw('x' * 20)
    pkt5 = Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=3893)/IP(dst='141.77.203.35', src='99.49.193.226', tos=227, ttl=22)/SCTP(dport=33682, sport=22991, tag=1)/Raw('x' * 20)
    pkt6 = Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=1575)/IP(dst='160.99.116.93', src='123.114.110.144', tos=21, ttl=72)/SCTP(dport=31363, sport=34136, tag=1)/Raw('x' * 20)
    pkt7 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP(dst='213.99.143.236', src='55.130.28.195', ttl=201)/UDP(dport=25119, sport=31609)/Raw('x' * 20)
    pkt8 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP(dst='224.12.140.222', src='118.34.141.171', tos=41)/TCP(dport=32602, sport=17691)/Raw('x' * 20)
    pkt9 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP(dst='124.168.113.3', src='253.237.216.240', proto=255)/Raw('x' * 20)
    pkt10 = Ether(dst="3c:fd:fe:9c:5b:b8")/IP(src="192.168.0.3", dst="192.168.0.4", proto=255)/Raw("x" * 20)

    verify packet
    pkt1 to queue 1, pkt2 to queue 2, pkt3 to queue 3, pkt4 to queue 4, pkt5 can't be received,
    pkt6/9/10 to queue 0, pkt7 to queue 5, pkt8 to queue 6.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 => QUEUE
    1       0       0       i--     ETH IPV4 UDP => QUEUE
    2       0       0       i--     ETH IPV4 TCP => QUEUE
    3       0       0       i--     ETH VLAN IPV4 SCTP => QUEUE
    4       0       0       i--     ETH VLAN IPV4 SCTP => DROP
    5       0       0       i--     ETH VLAN IPV4 SCTP => PASSTHRU FLAG
    6       0       0       i--     ETH IPV4 UDP => QUEUE FLAG
    7       0       0       i--     ETH IPV4 TCP => QUEUE MARK
    8       0       0       i--     ETH IPV4 => PASSTHRU MARK

Subcase2: fdir for ipv4 (DPDK PF + DPDK VF)
-------------------------------------------

   Prerequisites:
   
   add two vfs on dpdk pf, then bind the vfs to vfio-pci::

    echo 2 >/sys/bus/pci/devices/0000:05:00.0/max_vfs
    ./usertools/dpdk-devbind.py -b vfio-pci 05:02.0 05:02.1

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1e0000 -n 4 -a 05:02.0 --file-prefix=vf0 --socket-mem=1024,1024 -- -i --rxq=4 --txq=4 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1e00000 -n 4 -a 05:02.1 --file-prefix=vf1 --socket-mem=1024,1024 -- -i --rxq=4 --txq=4 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. validate and create the filter rules.

   ipv4-other::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 proto is 3 / end actions queue index 1 / end

   ipv4-udp::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 ttl is 3 / udp src is 22 dst is 23 / end actions queue index 2 / end

   ipv4-tcp::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 3 / tcp src is 32 dst is 33 / end actions queue index 3 / end

   ipv4-sctp::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 3 ttl is 3 / sctp src is 44 dst is 45 tag is 1 / end actions queue index 4 / end

   ipv4-other-vf0::

    testpmd> flow create 0 ingress transfer pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 proto is 3 / vf id is 0 / end actions queue index 1 / end

   ipv4-sctp-vf1::

    testpmd> flow create 0 ingress transfer pattern eth / vlan tci is 2 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 4 / sctp src is 46 dst is 47 tag is 1 / vf id is 1 / end actions queue index 2 / end

   ipv4-sctp drop::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.5 dst is 192.168.0.6 tos is 3 ttl is 3 / sctp src is 44 dst is 45 tag is 1 / end actions drop / end

   ipv4-sctp passthru-flag::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 3 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 4 / sctp src is 44 dst is 45 tag is 1 / end actions passthru / flag / end

   ipv4-udp queue-flag::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 ttl is 4 / udp src is 22 dst is 23 / end actions queue index 5 / flag / end

   ipv4-tcp queue-mark::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 / tcp src is 32 dst is 33 / end actions queue index 6 / mark id 3 / end

   ipv4-other passthru-mark::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.4 proto is 3 / end actions passthru / mark id 4 / end

3. send packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2", proto=3)/Raw('x' * 20)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2", ttl=3)/UDP(sport=22,dport=23)/Raw('x' * 20)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2", tos=3)/TCP(sport=32,dport=33)/Raw('x' * 20)
    pkt4 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.0.1", dst="192.168.0.2", tos=3, ttl=3)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="X" * 20)
    pkt5 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=2)/IP(src="192.168.0.1", dst="192.168.0.2", tos=4, ttl=4)/SCTP(sport=46,dport=47,tag=1)/Raw('x' * 20)
    pkt6 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.5", dst="192.168.0.6", tos=3, ttl=3)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="X" * 20)
    pkt7 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.0.1", dst="192.168.0.2", tos=4, ttl=4)/SCTP(sport=44,dport=45,tag=1)/Raw('x' * 20)
    pkt8 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2", ttl=4)/UDP(sport=22,dport=23)/Raw('x' * 20)
    pkt9 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2", tos=4)/TCP(sport=32,dport=33)/Raw('x' * 20)
    pkt10 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3", dst="192.168.0.4", proto=3)/Raw('x' * 20)

   verify packet 
   pkt1 to queue 1 and vf0 queue 1, pkt2 to queue 2, pkt3 to queue 3,
   pkt4 to queue 4, pkt5 to vf1 queue 2, pkt6 can't be received by pf.
   if not "--disable-rss",
   pkt7 to queue 0, FDIR matched hash 0 ID 0, pkt8 to queue 5,
   FDIR matched hash 0 ID 0, pkt9 to queue 6, FDIR matched ID 3,
   pkt10 queue determined by rss rule, FDIR matched ID 4.
   if "--disable-rss"
   pkt7-9 has same result with above, pkt10 to queue 0, FDIR matched ID 4.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0


Test case: Intel® Ethernet 700 Series fdir for ipv6
===================================================

Subcase1: fdir for ipv6 (DPDK PF)
---------------------------------

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. validate and create the filter rules::

    testpmd> flow validate 0 ingress pattern eth / vlan tci is 1615 / ipv6 src is f47e:d08c:3856:2e75:2f6b:7b92:c5ee:8f3c dst is 3d29:55bc:c137:3bd9:32b6:afe7:2db6:358f proto is 255 tc is 31 hop is 47  / end actions queue index 0 /  end
    testpmd> flow validate 0 ingress pattern eth / vlan tci is 2144 / ipv6 src is 776c:1445:230:8421:7813:c142:5eab:3224 dst is 32c0:348d:90c:cd0a:5e7:f950:6db9:f686 tc is 70 hop is 185 / udp dst is 18871 src is 40861  / end actions queue index 7 /  end
    testpmd> flow validate 0 ingress pattern eth / vlan tci is 827 / ipv6 src is 79a1:1122:ab30:112:bbc4:f043:a68b:2261 dst is 14a4:d730:69d1:d6b3:f39a:6f9c:398e:e510 tc is 245 hop is 72 / tcp dst is 63094 src is 13170  / end actions queue index 15 /  end
    testpmd> flow validate 0 ingress pattern eth / vlan tci is 1063 / ipv6 src is cb74:80d7:c1fd:b5ad:1016:1b4d:29a6:24f1 dst is 22c9:69f:a52d:6826:3f95:5ac:be54:f88c tc is 216 hop is 180 / sctp dst is 2661 src is 24787 tag is 1  / end actions queue index 1 /  end
    testpmd> flow validate 0 ingress pattern eth / vlan tci is 2212 / ipv6 src is a457:e86a:a531:d6d1:af33:c06a:b1f6:e96f dst is f13b:3245:f84f:af9c:42b7:cd48:63c:c168 tc is 243 hop is 11 / sctp dst is 31788 src is 10570 tag is 1  / end actions drop /  end

    testpmd> flow create 0 ingress pattern eth / vlan tci is 120 / ipv6 src is 3a69:6b77:3c17:87b:dad1:3559:c2d4:f8f9 dst is f15e:7045:9ce9:c217:5cda:8710:6704:1166 proto is 255 tc is 63 hop is 175  / end actions queue index 1 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 1438 / ipv6 src is 3d0a:40ca:7efa:6501:f13e:5559:a3da:fab dst is 23f5:1:fe7d:c59e:160b:22ec:f102:82c5 tc is 107 hop is 34 / udp dst is 46416 src is 57148  / end actions queue index 2 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 78 / ipv6 src is 4701:9a42:995:f2c:b75a:87eb:8dde:991d dst is 24ec:dd03:991d:5fb6:5e07:47ba:531a:e897 tc is 180 hop is 137 / tcp dst is 3940 src is 52731  / end actions queue index 3 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 59 / ipv6 src is caeb:64ff:2216:5334:16df:e93c:c5f5:9680 dst is 46a:6625:57f9:915:19a6:ecc7:3131:f702 tc is 52 hop is 253 / sctp dst is 48514 src is 49861 tag is 1  / end actions queue index 4 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 4014 / ipv6 src is a484:b7d9:ee51:e67c:d668:6304:f612:b814 dst is 8ff1:1185:2084:454d:ff90:a7b1:675d:31c4 tc is 248 hop is 22 / sctp dst is 54472 src is 48229 tag is 1  / end actions drop /  end


3. send packets::

    pkt1 = Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=120)/IPv6(src='3a69:6b77:3c17:87b:dad1:3559:c2d4:f8f9', dst='f15e:7045:9ce9:c217:5cda:8710:6704:1166', nh=255, tc=63, hlim=175)/Raw('x' * 20)
    pkt2 = Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=1438)/IPv6(src='3d0a:40ca:7efa:6501:f13e:5559:a3da:fab', dst='23f5:1:fe7d:c59e:160b:22ec:f102:82c5', tc=107, hlim=34)/UDP(dport=46416, sport=57148)/Raw('x' * 20)
    pkt3 = Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=78)/IPv6(src='4701:9a42:995:f2c:b75a:87eb:8dde:991d', dst='24ec:dd03:991d:5fb6:5e07:47ba:531a:e897', tc=180, hlim=137)/TCP(dport=3940, sport=52731)/Raw('x' * 20)
    pkt4 = Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=59)/IPv6(src='caeb:64ff:2216:5334:16df:e93c:c5f5:9680', dst='46a:6625:57f9:915:19a6:ecc7:3131:f702', tc=52, hlim=253, nh=132)/SCTP(dport=48514, sport=49861, tag=1)/Raw('x' * 20)
    pkt5 = Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=1438)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/UDP(sport=22,dport=23)/Raw("x" * 20)
    pkt6 = Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=2734)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/UDP(sport=22,dport=23)/Raw("x" * 20)

    verify packet
    pkt1 to queue 1, pkt2 to queue 2, pkt3 to queue 3, pkt4 to queue 4, pkt5 can't be received,	pkt6 to queue 0.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH VLAN IPV6 => QUEUE
    1       0       0       i--     ETH VLAN IPV6 UDP => QUEUE
    2       0       0       i--     ETH VLAN IPV6 TCP => QUEUE
    3       0       0       i--     ETH VLAN IPV6 SCTP => QUEUE
    4       0       0       i--     ETH VLAN IPV6 SCTP => DROP

Subcase2: fdir for ipv6 (DPDK PF + DPDK VF)
-------------------------------------------

   Prerequisites:

   add two vfs on dpdk pf, then bind the vfs to vfio-pci::

    echo 2 >/sys/bus/pci/devices/0000:05:00.0/max_vfs
    ./usertools/dpdk-devbind.py -b vfio-pci 05:02.0 05:02.1

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1e0000 -n 4 -a 05:02.0 --file-prefix=vf0 --socket-mem=1024,1024 -- -i --rxq=4 --txq=4 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1e00000 -n 4 -a 05:02.1 --file-prefix=vf1 --socket-mem=1024,1024 -- -i --rxq=4 --txq=4 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. validated and create filter rules

   ipv6-other::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / ipv6 src is 2001::1 dst is 2001::2 tc is 1 proto is 5 hop is 10 / end actions queue index 1 / end

   ipv6-udp::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2 / ipv6 src is 2001::1 dst is 2001::2 tc is 2 hop is 20 / udp src is 22 dst is 23 / end actions queue index 2 / end

   ipv6-tcp::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 3 / ipv6 src is 2001::1 dst is 2001::2 tc is 3 hop is 30 / tcp src is 32 dst is 33 / end actions queue index 3 / end

   ipv6-sctp::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 4 / ipv6 src is 2001::1 dst is 2001::2 tc is 4 hop is 40 / sctp src is 44 dst is 45 tag is 1 / end actions queue index 4 / end

   ipv6-other-vf0::

    testpmd> flow create 0 ingress transfer pattern eth / vlan tci is 5 / ipv6 src is 2001::3 dst is 2001::4 tc is 5 proto is 5 hop is 50 / vf id is 0 / end actions queue index 1 / end

   ipv6-tcp-vf1::

    testpmd> flow create 0 ingress transfer pattern eth / vlan tci is 4095 / ipv6 src is 2001::3 dst is 2001::4 tc is 6 hop is 60 / tcp src is 32 dst is 33 / vf id is 1 / end actions queue index 3 / end

   ipv6-sctp-drop::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 7 / ipv6 src is 2001::1 dst is 2001::2 tc is 7 hop is 70 / sctp src is 44 dst is 45 tag is 1 / end actions drop / end

   ipv6-tcp-vf1-drop::

    testpmd> flow create 0 ingress transfer pattern eth / vlan tci is 8 / ipv6 src is 2001::3 dst is 2001::4 tc is 8 hop is 80 / tcp src is 32 dst is 33 / vf id is 1 / end actions drop / end

3. send packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="2001::1", dst="2001::2", tc=1, nh=5, hlim=10)/Raw('x' * 20)
    pkt2 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=2)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/UDP(sport=22,dport=23)/Raw('x' * 20)
    pkt3 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IPv6(src="2001::1", dst="2001::2", tc=3, hlim=30)/TCP(sport=32,dport=33)/Raw('x' * 20)
    pkt4 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=4)/IPv6(src="2001::1", dst="2001::2", tc=4, nh=132, hlim=40)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="X" * 20)
    pkt5 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="2001::3", dst="2001::4", tc=5, nh=5, hlim=50)/Raw('x' * 20)
    pkt6 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=4095)/IPv6(src="2001::3", dst="2001::4", tc=6, hlim=60)/TCP(sport=32,dport=33)/Raw('x' * 20)
    pkt7 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=7)/IPv6(src="2001::1", dst="2001::2", tc=7, nh=132, hlim=70)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="X" * 20)
    pkt8 = Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=8)/IPv6(src="2001::3", dst="2001::4", tc=8, hlim=80)/TCP(sport=32,dport=33)/Raw('x' * 20)

   verify packet
   pkt1 to queue 1 and vf queue 1, pkt2 to queue 2, pkt3 to queue 3,
   pkt4 to queue 4, pkt5 to vf0 queue 1, pkt6 to vf1 queue 3,
   pkt7 can't be received by pf, pkt8 can't be received by vf1.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0

Test case: Intel® Ethernet 700 Series fdir for vlan
===================================================

Subcase1: fdir for vlan (DPDK PF)
---------------------------------

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 --legacy-mem -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

    if the i40e firmware version >= 8.4 the dpdk can only add 'extend on' to make the single VLAN filter work normally:
    testpmd> vlan set extend on 0

2. create and validated filter rules::

    testpmd> flow create 0 ingress pattern eth / vlan tci is 91 / ipv4  / end actions queue index 1 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 1978 / ipv4 / udp  / end actions queue index 2 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 2391 / ipv4 / tcp  / end actions queue index 3 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 4028 / ipv4 / sctp  / end actions queue index 4 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 986 / ipv4 / sctp  / end actions drop /  end

    testpmd> flow create 0 ingress pattern eth / vlan tci is 2477 / ipv6  / end actions queue index 1 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 3407 / ipv6 / udp  / end actions queue index 2 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 2283 / ipv6 / tcp  / end actions queue index 3 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 2709 / ipv6 / sctp  / end actions queue index 4 /  end
    testpmd> flow create 0 ingress pattern eth / vlan tci is 3734 / ipv6 / sctp  / end actions drop /  end

3. send the packets::

    pkt1 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=91)/IP()/Raw('x' * 20)]
    pkt2 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=91)/IP(src="192.168.0.1", dst="192.168.0.2", proto=3)/Raw("x" * 20)]

    pkt3 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=1978)/IP()/UDP()/Raw('x' * 20)]
    pkt4 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=1978)/IP(src="192.168.0.1", dst="192.168.0.2", tos=3)/UDP()/Raw("x" * 20)]

    pkt5 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=2391)/IP()/TCP()/Raw('x' * 20)]
    pkt6 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=2391)/IP(src="192.168.0.1", dst="192.168.0.2", ttl=3)/TCP()/Raw("x" * 20)]

    pkt7 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=4028)/IP()/SCTP()/Raw('x' * 20)]
    pkt8 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=4028)/IP(src="192.168.0.1", dst="192.168.0.2", tos=3, ttl=3)/SCTP()/Raw("x" * 20)]

    pkt9 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=2391)/IP()/UDP()/Raw("x" * 20)]
    pkt10 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=4028)/IP(src="192.168.0.1", dst="192.168.0.2", ttl=3)/TCP()/Raw("x" * 20)]

    pkt13 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=986)/IP()/SCTP()/Raw('x' * 20)]
    pkt14 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=986)/IP(src="192.168.0.5", dst="192.168.0.6", tos=3, ttl=3)/SCTP(sport=44,dport=45,tag=1)/Raw("x" * 20)]

    pkt17 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=2477)/IPv6(src='cb5:c4a9:8855:e022:c66a:a5dc:f2b8:a4d9', dst='922c:9e24:a730:2c66:9b65:c00a:cfed:986')/Raw('x' * 20)]
    pkt18 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=2477)/IPv6(src="2001::1", dst="2001::2", tc=1, nh=5, hlim=10)/Raw("x" * 20)]
    pkt19 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=3407)/IPv6(src='4cff:139f:dad7:cb9f:bb6d:3e28:42b2:99b', dst='cb9e:cd92:b178:d273:de4d:c9fa:9952:5088')/UDP()/Raw('x' * 20)]
    pkt20 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=3407)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/UDP(sport=22,dport=23)/Raw("x" * 20)]
    pkt21 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=2283)/IPv6(src='5548:dace:bc41:5829:ee11:1944:a56:18f9', dst='9ef3:710f:b492:778c:f87a:455f:4508:893e')/TCP()/Raw('x' * 20)]
    pkt22 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=2283)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/TCP(sport=32,dport=33)/Raw("x" * 20)]
    pkt23 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=2709)/IPv6(src='7d7d:ca46:bd95:676e:b680:b7e9:4c21:d7cc', dst='c7bc:8b28:a48a:a7eb:bfd0:3313:1548:7579', nh=132)/SCTP()/Raw('x' * 20)]
    pkt24 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=2709)/IPv6(src="2001::1", dst="2001::2", tc=4, nh=132, hlim=40)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="X" * 20)]

    pkt27 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=3734)/IPv6(src='1529:7d1c:6f:914a:2fe2:269f:3b16:3f60', dst='fd68:fd59:bb7c:12d4:3b19:20b2:1ef3:7100', nh=132)/SCTP()/Raw('x' * 20)]
    pkt28 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=3734)/IPv6(src="2001::1", dst="2001::2", tc=4, nh=132, hlim=40)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="X" * 20)]

    verify packet
    pkt1,pkt2 to queue 1, pkt3,pkt4 to queue 2, pkt5,pkt6 to queue 3,
    pkt7,pkt8 to queue 4, pkt9,pkt10 to queue 0, pkt13, pkt14 can't be received by pf,
    pkt17,pkt18 to queue 1, pkt19,pkt20 to queue 2, pkt21,pkt22 to queue 3,
    pkt23,pkt24 to queue 4, pkt27, pkt28 can't be received by pf.

4. verify rules can be listed and destroyed.

Subcase2: fdir for vlan (DPDK PF + DPDK VF)
-------------------------------------------

Prerequisites:

   add 2 vf on dpdk pf, then bind the vf to vfio-pci::

    echo 2 >/sys/bus/pci/devices/0000:05:00.0/max_vfs
    ./usertools/dpdk-devbind.py -b vfio-pci 05:02.0 05:02.1

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 --legacy-mem -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

    if the i40e firmware version >= 8.4 the dpdk can only add 'extend on' to make the single VLAN filter work normally:
    testpmd> vlan set extend on 0

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1e0000 -n 4 -a 05:02.0 --file-prefix=vf0 --socket-mem=1024,1024 --legacy-mem -- -i --rxq=4 --txq=4 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1e00000 -n 4 -a 05:02.1 --file-prefix=vf1 --socket-mem=1024,1024 --legacy-mem -- -i --rxq=4 --txq=4 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. validated and create filter rules

   testpmd> flow create 0 ingress pattern eth / vlan tci is 91 / ipv4  / end actions queue index 1 /  end
   testpmd> flow create 0 ingress pattern eth / vlan tci is 1978 / ipv4 / udp  / end actions queue index 2 /  end
   testpmd> flow create 0 ingress pattern eth / vlan tci is 2391 / ipv4 / tcp  / end actions queue index 3 /  end
   testpmd> flow create 0 ingress pattern eth / vlan tci is 4028 / ipv4 / sctp  / end actions queue index 4 /  end
   testpmd> flow create 0 ingress transfer pattern eth / vlan tci is 1276 / ipv4 / vf id is 0 / end actions queue index 2 /  end
   testpmd> flow create 0 ingress transfer pattern eth / vlan tci is 2221 / ipv4 / sctp / vf id is 1 / end actions queue index 3 /  end
   testpmd> flow create 0 ingress pattern eth / vlan tci is 986 / ipv4 / sctp  / end actions drop /  end
   testpmd> flow create 0 ingress transfer pattern eth / vlan tci is 2446 / ipv4 / udp / vf id is 1 / end actions drop /  end

   testpmd> flow create 0 ingress pattern eth / vlan tci is 2477 / ipv6  / end actions queue index 1 /  end
   testpmd> flow create 0 ingress pattern eth / vlan tci is 3407 / ipv6 / udp  / end actions queue index 2 /  end
   testpmd> flow create 0 ingress pattern eth / vlan tci is 2283 / ipv6 / tcp  / end actions queue index 3 /  end
   testpmd> flow create 0 ingress pattern eth / vlan tci is 2709 / ipv6 / sctp  / end actions queue index 4 /  end
   testpmd> flow create 0 ingress transfer pattern eth / vlan tci is 2972 / ipv6 / vf id is 0 / end actions queue index 0 /  end
   testpmd> flow create 0 ingress transfer pattern eth / vlan tci is 942 / ipv6 / tcp / vf id is 1 / end actions queue index 1 /  end
   testpmd> flow create 0 ingress pattern eth / vlan tci is 3734 / ipv6 / sctp  / end actions drop /  end
   testpmd> flow create 0 ingress transfer pattern eth / vlan tci is 3455 / ipv6 / tcp / vf id is 1 / end actions drop /  end

   testpmd> flow validate 0 ingress pattern eth / vlan tci is 1967 / ipv4  / end actions queue index 7 /  end
   testpmd> flow validate 0 ingress pattern eth / vlan tci is 1611 / ipv4 / udp  / end actions queue index 3 /  end
   testpmd> flow validate 0 ingress pattern eth / vlan tci is 3211 / ipv4 / tcp  / end actions queue index 12 /  end
   testpmd> flow validate 0 ingress pattern eth / vlan tci is 1198 / ipv4 / sctp  / end actions queue index 7 /  end
   testpmd> flow validate 0 ingress transfer pattern eth / vlan tci is 144 / ipv4 / vf id is 0 / end actions queue index 2 /  end
   testpmd> flow validate 0 ingress transfer pattern eth / vlan tci is 2469 / ipv4 / sctp / vf id is 1 / end actions queue index 3 /  end
   testpmd> flow validate 0 ingress pattern eth / vlan tci is 2615 / ipv4 / sctp  / end actions drop /  end
   testpmd> flow validate 0 ingress transfer pattern eth / vlan tci is 1048 / ipv4 / udp / vf id is 1 / end actions drop /  end

   testpmd> flow validate 0 ingress pattern eth / vlan tci is 31 / ipv6  / end actions queue index 9 /  end
   testpmd> flow validate 0 ingress pattern eth / vlan tci is 2220 / ipv6 / udp  / end actions queue index 3 /  end
   testpmd> flow validate 0 ingress pattern eth / vlan tci is 1772 / ipv6 / tcp  / end actions queue index 5 /  end
   testpmd> flow validate 0 ingress pattern eth / vlan tci is 3101 / ipv6 / sctp  / end actions queue index 9 /  end
   testpmd> flow validate 0 ingress transfer pattern eth / vlan tci is 3353 / ipv6 / vf id is 0 / end actions queue index 1 /  end
   testpmd> flow validate 0 ingress transfer pattern eth / vlan tci is 210 / ipv6 / tcp / vf id is 1 / end actions queue index 0 /  end
   testpmd> flow validate 0 ingress pattern eth / vlan tci is 1249 / ipv6 / sctp  / end actions drop /  end
   testpmd> flow validate 0 ingress transfer pattern eth / vlan tci is 3771 / ipv6 / tcp / vf id is 1 / end actions drop /  end

3. send the packets with dst/src ip and dst/src port::

    pkt1 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=91)/IP()/Raw('x' * 20)]
    pkt2 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=91)/IP(src="192.168.0.1", dst="192.168.0.2", proto=3)/Raw("x" * 20)]

    pkt3 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=1978)/IP()/UDP()/Raw('x' * 20)]
    pkt4 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=1978)/IP(src="192.168.0.1", dst="192.168.0.2", tos=3)/UDP()/Raw("x" * 20)]

    pkt5 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=2391)/IP()/TCP()/Raw('x' * 20)]
    pkt6 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=2391)/IP(src="192.168.0.1", dst="192.168.0.2", ttl=3)/TCP()/Raw("x" * 20)]

    pkt7 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=4028)/IP()/SCTP()/Raw('x' * 20)]
    pkt8 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=4028)/IP(src="192.168.0.1", dst="192.168.0.2", tos=3, ttl=3)/SCTP()/Raw("x" * 20)]

    pkt9 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=2391)/IP()/UDP()/Raw("x" * 20)]
    pkt10 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=4028)/IP(src="192.168.0.1", dst="192.168.0.2", ttl=3)/TCP()/Raw("x" * 20)]
    pkt11 = [Ether(dst='00:11:22:33:44:77')/Dot1Q(vlan=1276)/IP()/Raw('x' * 20)]
    pkt12 = [Ether(dst='00:11:22:33:44:77')/Dot1Q(vlan=2221)/IP()/SCTP()/Raw('x' * 20)]

    pkt13 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=986)/IP()/SCTP()/Raw('x' * 20)]
    pkt14 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=986)/IP(src="192.168.0.5", dst="192.168.0.6", tos=3, ttl=3)/SCTP(sport=44,dport=45,tag=1)/Raw("x" * 20)]

    pkt15 = [Ether(dst='00:11:22:33:44:77')/Dot1Q(vlan=2446)/IP()/UDP()/Raw('x' * 20)]
    pkt16 = [Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=2446)/IP(src="192.168.0.5", dst="192.168.0.6", tos=3, ttl=3)/UDP(sport=44,dport=45)/SCTPChunkData(data="X" * 20)]
      verify packet
      pkt1,pkt2 to queue 1, pkt3,pkt4 to queue 2, pkt5,pkt6 to queue 3,
      pkt7,pkt8 to queue 4, pkt9,pkt10 to queue 0, pkt11 to vf0 queue 2, pkt12 to vf1 queue 3,
      pkt13, pkt14 can't be received by pf, pkt15, pkt16 can't be received by vf1.

    pkt17 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=2477)/IPv6(src='cb5:c4a9:8855:e022:c66a:a5dc:f2b8:a4d9', dst='922c:9e24:a730:2c66:9b65:c00a:cfed:986')/Raw('x' * 20)]
    pkt18 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=2477)/IPv6(src="2001::1", dst="2001::2", tc=1, nh=5, hlim=10)/Raw("x" * 20)]
    pkt19 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=3407)/IPv6(src='4cff:139f:dad7:cb9f:bb6d:3e28:42b2:99b', dst='cb9e:cd92:b178:d273:de4d:c9fa:9952:5088')/UDP()/Raw('x' * 20)]
    pkt20 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=3407)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/UDP(sport=22,dport=23)/Raw("x" * 20)]
    pkt21 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=2283)/IPv6(src='5548:dace:bc41:5829:ee11:1944:a56:18f9', dst='9ef3:710f:b492:778c:f87a:455f:4508:893e')/TCP()/Raw('x' * 20)]
    pkt22 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=2283)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/TCP(sport=32,dport=33)/Raw("x" * 20)]
    pkt23 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=2709)/IPv6(src='7d7d:ca46:bd95:676e:b680:b7e9:4c21:d7cc', dst='c7bc:8b28:a48a:a7eb:bfd0:3313:1548:7579', nh=132)/SCTP()/Raw('x' * 20)]
    pkt24 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=2709)/IPv6(src="2001::1", dst="2001::2", tc=4, nh=132, hlim=40)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="X" * 20)]

    pkt25 = [Ether(dst='00:11:22:33:44:77')/Dot1Q(vlan=2972)/IPv6(src='816d:2dfd:17f8:69bd:ec68:581f:740f:42db', dst='68c8:243:b709:3a8b:658:9ebb:f60f:c493')/Raw('x' * 20)]
    pkt26 = [Ether(dst='00:11:22:33:44:77')/Dot1Q(vlan=942)/IPv6(src='9550:be5c:599b:705e:275c:6164:c034:b4e7', dst='3450:bddc:a4a6:23cd:b8e:f85f:7424:4f8f')/TCP()/Raw('x' * 20)]
    pkt27 = [Ether(dst='3c:fd:fe:9c:5b:b8')/Dot1Q(vlan=3734)/IPv6(src='1529:7d1c:6f:914a:2fe2:269f:3b16:3f60', dst='fd68:fd59:bb7c:12d4:3b19:20b2:1ef3:7100', nh=132)/SCTP()/Raw('x' * 20)]
    pkt28 = [Ether(dst="3c:fd:fe:9c:5b:b8")/Dot1Q(vlan=3734)/IPv6(src="2001::1", dst="2001::2", tc=4, nh=132, hlim=40)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="X" * 20)]
    pkt29 = [Ether(dst='00:11:22:33:44:77')/Dot1Q(vlan=3455)/IPv6(src='ffdf:e23b:9cc4:b99b:cdc:a881:6b7a:bac2', dst='c90b:3b2a:2c42:6d12:e51f:8657:e941:1fe1')/TCP()/Raw('x' * 20)]
    pkt30 = [Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3455)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/TCP(sport=32,dport=33)/Raw("x" * 20)]
     verify packet
     pkt17,pkt18 to queue 1, pkt19,pkt20 to queue 2, pkt21,pkt22 to queue 3,
     pkt23,pkt24 to queue 4, pkt25 to vf0 queue 0, pkt26 to vf1 queue 1,
     pkt27, pkt28 can't be received by pf, pkt29, pkt30 can't be received by vf1.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
      ID	Group	Prio	Attr	Rule
      0	    0	0	i--	ETH VLAN IPV4 => QUEUE
      1	    0	0	i--	ETH VLAN IPV4 UDP => QUEUE
      2	    0	0	i--	ETH VLAN IPV4 TCP => QUEUE
      3	    0	0	i--	ETH VLAN IPV4 SCTP => QUEUE
      4	    0	0	i-t	ETH VLAN IPV4 VF => QUEUE
      5	    0	0	i-t	ETH VLAN IPV4 SCTP VF => QUEUE
      6	    0 	0 	i--	ETH VLAN IPV4 SCTP => DROP
      7	    0 	0	i-t	ETH VLAN IPV4 UDP VF => DROP
      8 	0	0	i--	ETH VLAN IPV6 => QUEUE
      9 	0	0	i--	ETH VLAN IPV6 UDP => QUEUE
      10	0	0	i--	ETH VLAN IPV6 TCP => QUEUE
      11	0	0	i--	ETH VLAN IPV6 SCTP => QUEUE
      12	0	0	i-t	ETH VLAN IPV6 VF => QUEUE
      13	0	0	i-t	ETH VLAN IPV6 TCP VF => QUEUE
      14	0	0	i--	ETH VLAN IPV6 SCTP => DROP
      15	0	0	i-t	ETH VLAN IPV6 TCP VF => DROP
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0


Test case: Intel® Ethernet 700 Series fdir wrong parameters
===========================================================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules

1) Exceeds maximum payload limit::

    testpmd> flow validate 0 ingress pattern eth type is 0x0807 / raw relative is 1 pattern is abcdefghijklmnopq / end actions queue index 1 / end
    testpmd> flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / sctp src is 42 / raw relative is 1 offset is 2 pattern is abcdefghijklmnopq / end actions queue index 5 / end

   it shows "Caught error type 9 (specific pattern item): cause: 0x7fd87ff60160
   exceeds maximum payload limit".

2) can't set mac_addr when setting fdir filter::

    testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 4095 / ipv6 src is 2001::3 dst is 2001::4 tc is 6 hop is 60 / tcp src is 32 dst is 33 / end actions queue index 2 / end
    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 4095 / ipv6 src is 2001::3 dst is 2001::4 tc is 6 hop is 60 / tcp src is 32 dst is 33 / end actions queue index 3 / end

   it shows "Caught error type 9 (specific pattern item): cause: 0x7f463ff60100
   Invalid MAC_addr mask".

3) can't change the configuration of the same packet type::
    testpmd> flow create 0 ingress pattern eth / vlan tci is 3 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 4 / sctp src is 44 dst is 45 tag is 1 / end actions passthru / flag / end
    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 4 / sctp src is 34 dst is 35 tag is 1 / end actions passthru / flag / end

   it shows "Caught error type 9 (specific pattern item): cause: 0x7feabff60120
   Conflict with the first rule's input set".

4) invalid queue ID::

    testpmd> flow validate 0 ingress pattern eth / ipv6 src is 2001::3 dst is 2001::4 tc is 6 hop is 60 / tcp src is 32 dst is 33 / end actions queue index 16 / end
    testpmd> flow create 0 ingress pattern eth / ipv6 src is 2001::3 dst is 2001::4 tc is 6 hop is 60 / tcp src is 32 dst is 33 / end actions queue index 16 / end

   it shows "Caught error type 11 (specific action): cause: 0x7ffc7bb9a338,
   Invalid queue ID for FDIR".

Note:

/// not support IP fragment ///


Test case: Intel® Ethernet 700 Series tunnel vxlan
==================================================

Subcase1: tunnel vxlan (DPDK PF)
--------------------------------

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 --legacy-mem  -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> rx_vxlan_port add 4789 0
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 1 /  end
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / vxlan vni is 794 / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 2 /  end
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth dst is 00:11:22:33:44:66 / vlan tci is 3478  / end actions pf / queue index 3 /  end
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / vxlan vni is 2611 / eth dst is 00:11:22:33:44:66 / vlan tci is 2434  / end actions pf / queue index 4 /  end
    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / udp / vxlan vni is 1909 / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 5 /  end

    testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / vxlan / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 2 /  end
    testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / vxlan vni is 423 / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 5 /  end
    testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / vxlan / eth dst is 00:11:22:33:44:66 / vlan tci is 2503  / end actions pf / queue index 4 /  end
    testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / vxlan vni is 330 / eth dst is 00:11:22:33:44:66 / vlan tci is 1503  / end actions pf / queue index 8 /  end
    testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / udp / vxlan vni is 513 / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 9 /  end

3. send packets::

    pkt1 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP()/UDP()/VXLAN()/Ether(dst='00:11:22:33:44:66')/Raw('x' * 20)
    pkt2 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP()/UDP()/VXLAN(vni=794, flags=8)/Ether(dst='00:11:22:33:44:66')/Raw('x' * 20)
    pkt3 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP()/UDP()/VXLAN()/Ether(dst='00:11:22:33:44:66')/Dot1Q(vlan=3478)/Raw('x' * 20)
    pkt4 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP()/UDP()/VXLAN(vni=2611, flags=8)/Ether(dst='00:11:22:33:44:66')/Dot1Q(vlan=2434)/Raw('x' * 20)
    pkt5 = Ether(dst='00:11:22:33:44:55')/IP()/UDP()/VXLAN(vni=1909, flags=8)/Ether(dst='00:11:22:33:44:66')/Raw('x' * 20)
    pkt6 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/Dot1Q(vlan=11)/IP()/TCP()/Raw("x" * 20)
    pkt7 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=5)/Ether(dst="00:11:22:33:44:77")/IP()/TCP()/Raw("x" * 20)

    verify pkt1 received by pf queue 1, pkt2 to pf queue 2, pkt3 to pf queue 3, pkt4 to pf queue 4, pkt5 to pf queue 5, pkt6 to pf queue 1, pkt7 to pf queue 0.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP VXLAN ETH => PF QUEUE
    1       0       0       i--     ETH IPV4 UDP VXLAN ETH => PF QUEUE
    2       0       0       i--     ETH IPV4 UDP VXLAN ETH VLAN => PF QUEUE
    3       0       0       i--     ETH IPV4 UDP VXLAN ETH VLAN => PF QUEUE
    4       0       0       i--     ETH IPV4 UDP VXLAN ETH => PF QUEUE

Subcase2: tunnel vxlan (DPDK PF + DPDK VF)
------------------------------------------

   Prerequisites:

   add a vf on dpdk pf, then bind the vf to vfio-pci::

    echo 1 >/sys/bus/pci/devices/0000:05:00.0/max_vfs
    ./usertools/dpdk-devbind.py -b vfio-pci 05:02.0

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> rx_vxlan_port add 4789 0
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> set promisc all off
    testpmd> start
    the pf's mac address is 00:00:00:00:01:00

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1e0000 -n 4 -a 05:02.0 --file-prefix=vf --socket-mem=1024,1024 -- -i --rxq=4 --txq=4 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> set promisc all off
    testpmd> start

   the vf's mac address is D2:8C:1A:50:2A:78

2. create filter rules

   inner mac + actions pf::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth dst is 00:11:22:33:44:55 / end actions pf / queue index 1 / end

   vni + inner mac + actions pf::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / vxlan vni is 2 / eth dst is 00:11:22:33:44:55 / end actions pf / queue index 2 / end

   inner mac + inner vlan +actions pf::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth dst is 00:11:22:33:44:55 / vlan tci is 10 / end actions pf / queue index 3 / end

   vni + inner mac + inner vlan + actions pf::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / vxlan vni is 4 / eth dst is 00:11:22:33:44:55 / vlan tci is 20 / end actions pf / queue index 4 / end

   inner mac + outer mac + vni + actions pf::

    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:66 / ipv4 / udp / vxlan vni is 5 /  eth dst is 00:11:22:33:44:55 / end actions pf / queue index 5 / end

   vni + inner mac + inner vlan + actions vf::

    testpmd> flow create 0 ingress transfer pattern eth / ipv4 / udp / vxlan vni is 6 / eth dst is 00:11:22:33:44:55 / vlan tci is 30 / end actions vf id 0 / queue index 1 / end

   inner mac + outer mac + vni + actions vf::

    testpmd> flow create 0 ingress transfer pattern eth dst is 00:11:22:33:44:66 / ipv4 / udp / vxlan vni is 7 /  eth dst is 00:11:22:33:44:55 / end actions vf id 0 / queue index 3 / end

3. send packets::

    pkt1 = Ether(dst="00:11:22:33:44:66")/IP()/UDP()/Vxlan()/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt2 = Ether(dst="00:11:22:33:44:66")/IP()/UDP()/Vxlan(vni=2)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt31 = Ether(dst="00:11:22:33:44:66")/IP()/UDP()/Vxlan()/Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=10)/IP()/TCP()/Raw('x' * 20)
    pkt32 = Ether(dst="00:11:22:33:44:66")/IP()/UDP()/Vxlan()/Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=11)/IP()/TCP()/Raw('x' * 20)
    pkt4 = Ether(dst="00:11:22:33:44:66")/IP()/UDP()/Vxlan(vni=4)/Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=20)/IP()/TCP()/Raw('x' * 20)
    pkt51 = Ether(dst="00:11:22:33:44:66")/IP()/UDP()/Vxlan(vni=5)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt52 = Ether(dst="00:11:22:33:44:66")/IP()/UDP()/Vxlan(vni=4)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt53 = Ether(dst="00:00:00:00:01:00")/IP()/UDP()/Vxlan(vni=5)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt54 = Ether(dst="00:11:22:33:44:77")/IP()/UDP()/Vxlan(vni=5)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt55 = Ether(dst="00:00:00:00:01:00")/IP()/UDP()/Vxlan(vni=5)/Ether(dst="00:11:22:33:44:77")/IP()/TCP()/Raw('x' * 20)
    pkt56 = Ether(dst="00:11:22:33:44:66")/IP()/UDP()/Vxlan(vni=5)/Ether(dst="00:11:22:33:44:77")/IP()/TCP()/Raw('x' * 20)
    pkt61 = Ether(dst="00:11:22:33:44:66")/IP()/UDP()/Vxlan(vni=6)/Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=30)/IP()/TCP()/Raw('x' * 20)
    pkt62 = Ether(dst="00:11:22:33:44:66")/IP()/UDP()/Vxlan(vni=6)/Ether(dst="00:11:22:33:44:77")/Dot1Q(vlan=30)/IP()/TCP()/Raw('x' * 20)
    pkt63 = Ether(dst="D2:8C:1A:50:2A:78")/IP()/UDP()/Vxlan(vni=6)/Ether(dst="00:11:22:33:44:77")/Dot1Q(vlan=30)/IP()/TCP()/Raw('x' * 20)
    pkt64 = Ether(dst="00:00:00:00:01:00")/IP()/UDP()/Vxlan(vni=6)/Ether(dst="00:11:22:33:44:77")/Dot1Q(vlan=30)/IP()/TCP()/Raw('x' * 20)
    pkt71 = Ether(dst="00:11:22:33:44:66")/IP()/UDP()/Vxlan(vni=7)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt72 = Ether(dst="D2:8C:1A:50:2A:78")/IP()/UDP()/Vxlan(vni=7)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt73 = Ether(dst="D2:8C:1A:50:2A:78")/IP()/UDP()/Vxlan(vni=7)/Ether(dst="00:11:22:33:44:77")/IP()/TCP()/Raw('x' * 20)
    pkt74 = Ether(dst="00:00:00:00:01:00")/IP()/UDP()/Vxlan(vni=7)/Ether(dst="00:11:22:33:44:77")/IP()/TCP()/Raw('x' * 20)

   verify pkt1 received by pf queue 1, pkt2 to pf queue 2,
   pkt31 to pf queue 3, pkt32 to pf queue 1, pkt4 to pf queue 4,
   pkt51 to pf queue 5, pkt52 to pf queue 1, pkt53 to pf queue 1,
   pkt54 to pf queue 1, pkt55 to pf queue 0, pf can't receive pkt56.
   pkt61 to vf queue 1 and pf queue 1, pf and vf can't receive pkt62,
   pkt63 to vf queue 0, pkt64 to pf queue 0, vf can't receive pkt64,
   pkt71 to vf queue 3 and pf queue 1, pkt72 to pf queue 1, vf can't receive
   pkt72, pkt73 to vf queue 0, pkt74 to pf queue 0, vf can't receive pkt74.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0

   verify pkt51 to pf queue 5, pkt53 and pkt55 to pf queue 0,
   pf can't receive pkt52,pkt54 and pkt56. pkt71 to vf queue 3,
   pkt72 and pkt73 to vf queue 0, pkt74 to pf queue 0, vf can't receive pkt74.
   Then::

    testpmd> flow flush 0
    testpmd> flow list 0

Test case: Intel® Ethernet 700 Series tunnel nvgre
==================================================

Subcase1: tunnel nvgre (DPDK PF)
--------------------------------

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 --legacy-mem  -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / nvgre / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 1 /  end
    testpmd> flow create 0 ingress pattern eth / ipv4 / nvgre tni is 2835 / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 2 /  end
    testpmd> flow create 0 ingress pattern eth / ipv4 / nvgre / eth dst is 00:11:22:33:44:66 / vlan tci is 1009  / end actions pf / queue index 3 /  end
    testpmd> flow create 0 ingress pattern eth / ipv4 / nvgre tni is 2570 / eth dst is 00:11:22:33:44:66 / vlan tci is 170  / end actions pf / queue index 4 /  end
    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / nvgre tni is 568 / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 5 /  end

    testpmd> flow validate 0 ingress pattern eth / ipv4 / nvgre / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 11 /  end
    testpmd> flow validate 0 ingress pattern eth / ipv4 / nvgre tni is 1987 / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 0 /  end
    testpmd> flow validate 0 ingress pattern eth / ipv4 / nvgre / eth dst is 00:11:22:33:44:66 / vlan tci is 266  / end actions pf / queue index 8 /  end
    testpmd> flow validate 0 ingress pattern eth / ipv4 / nvgre tni is 3114 / eth dst is 00:11:22:33:44:66 / vlan tci is 1776  / end actions pf / queue index 9 /  end
    testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / nvgre tni is 836 / eth dst is 00:11:22:33:44:66  / end actions pf / queue index 1 /  end

3. send packets::

    pkt1 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP()/GRE(key_present=1,proto=0x6558,key=0x00000100)/Ether(dst='00:11:22:33:44:66')/Raw('x' * 20)
    pkt2 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP()/GRE(key_present=1,proto=0x6558,key=725760)/Ether(dst='00:11:22:33:44:66')/Raw('x' * 20)
    pkt3 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP()/GRE(key_present=1,proto=0x6558,key=0x00000100)/Ether(dst='00:11:22:33:44:66')/Dot1Q(vlan=1009)/Raw('x' * 20)
    pkt4 = Ether(dst='3c:fd:fe:9c:5b:b8')/IP()/GRE(key_present=1,proto=0x6558,key=657920)/Ether(dst='00:11:22:33:44:66')/Dot1Q(vlan=170)/Raw('x' * 20)
    pkt5 = Ether(dst='00:11:22:33:44:55')/IP()/GRE(key_present=1,proto=0x6558,key=145408)/Ether(dst='00:11:22:33:44:66')/Raw('x' * 20)
    pkt6 = Ether(dst="00:11:22:33:44:55")/IP()/GRE(key_present=1,proto=0x6558,key=0x00000100)/Ether(dst="00:11:22:33:44:66")/Dot1Q(vlan=1)/IP()/TCP()/Raw("x" * 20)
    pkt7 = Ether(dst="00:11:22:33:44:55")/IP()/GRE(key_present=1,proto=0x6558,key=145408)/Ether(dst="00:11:22:33:44:77")/IP()/TCP()/Raw("x" * 20)

    verify pkt1 received by pf queue 1, pkt2 to pf queue 2, pkt3 to pf queue 3, pkt4 to pf queue 4, pkt5 to pf queue 5, pkt6 to pf queue 1, pkt7 to pf queue 0.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 NVGRE ETH => PF QUEUE
    1       0       0       i--     ETH IPV4 NVGRE ETH => PF QUEUE
    2       0       0       i--     ETH IPV4 NVGRE ETH VLAN => PF QUEUE
    3       0       0       i--     ETH IPV4 NVGRE ETH VLAN => PF QUEUE
    4       0       0       i--     ETH IPV4 NVGRE ETH => PF QUEUE

Subcase2: tunnel nvgre (DPDK PF + DPDK VF)
------------------------------------------

   Prerequisites:

   add two vfs on dpdk pf, then bind the vfs to vfio-pci::

    echo 2 >/sys/bus/pci/devices/0000:05:00.0/max_vfs
    ./usertools/dpdk-devbind.py -b vfio-pci 05:02.0 05:02.1

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -a 05:00.0 --file-prefix=pf --socket-mem=1024,1024 -- -i --rxq=16 --txq=16
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> set promisc all off
    testpmd> start

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1e0000 -n 4 -a 05:02.0 --file-prefix=vf0 --socket-mem=1024,1024 -- -i --rxq=4 --txq=4
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> set promisc all off
    testpmd> start

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1e00000 -n 4 -a 05:02.1 --file-prefix=vf1 --socket-mem=1024,1024 -- -i --rxq=4 --txq=4
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> set promisc all off
    testpmd> start

   the pf's mac address is 00:00:00:00:01:00
   the vf0's mac address is 54:52:00:00:00:01
   the vf1's mac address is 54:52:00:00:00:02

2. create filter rules

   inner mac + actions pf::

    testpmd> flow create 0 ingress pattern eth / ipv4 / nvgre / eth dst is 00:11:22:33:44:55 / end actions pf / queue index 1 / end

   tni + inner mac + actions pf::

    testpmd> flow create 0 ingress pattern eth / ipv4 / nvgre tni is 2 / eth dst is 00:11:22:33:44:55 / end actions pf / queue index 2 / end

   inner mac + inner vlan + actions pf::

    testpmd> flow create 0 ingress pattern eth / ipv4 / nvgre / eth dst is 00:11:22:33:44:55 / vlan tci is 30 / end actions pf / queue index 3 / end

   tni + inner mac + inner vlan + actions pf::

    testpmd> flow create 0 ingress pattern eth / ipv4 / nvgre tni is 0x112244 / eth dst is 00:11:22:33:44:55 / vlan tci is 40 / end actions pf / queue index 4 / end

   inner mac + outer mac + tni + actions pf::

    testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:66 / ipv4 / nvgre tni is 0x112255 /  eth dst is 00:11:22:33:44:55 / end actions pf / queue index 5 / end

   tni + inner mac + inner vlan + actions vf::

    testpmd> flow create 0 ingress transfer pattern eth / ipv4 / nvgre tni is 0x112266 / eth dst is 00:11:22:33:44:55 / vlan tci is 60 / end actions vf id 0 / queue index 1 / end

   inner mac + outer mac + tni + actions vf::

    testpmd> flow create 0 ingress transfer pattern eth dst is 00:11:22:33:44:66 / ipv4 / nvgre tni is 0x112277 /  eth dst is 00:11:22:33:44:55 / end actions vf id 1 / queue index 3 / end

3. send packets::

    pkt1 = Ether(dst="00:11:22:33:44:66")/IP()/NVGRE()/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt2 = Ether(dst="00:11:22:33:44:66")/IP()/NVGRE(TNI=2)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt31 = Ether(dst="00:11:22:33:44:66")/IP()/NVGRE()/Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=30)/IP()/TCP()/Raw('x' * 20)
    pkt32 = Ether(dst="00:11:22:33:44:66")/IP()/NVGRE()/Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=31)/IP()/TCP()/Raw('x' * 20)
    pkt4 = Ether(dst="00:11:22:33:44:66")/IP()/NVGRE(TNI=0x112244)/Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=40)/IP()/TCP()/Raw('x' * 20)
    pkt51 = Ether(dst="00:11:22:33:44:66")/IP()/NVGRE(TNI=0x112255)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt52 = Ether(dst="00:11:22:33:44:66")/IP()/NVGRE(TNI=0x112256)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt53 = Ether(dst="00:00:00:00:01:00")/IP()/NVGRE(TNI=0x112255)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt54 = Ether(dst="00:11:22:33:44:77")/IP()/NVGRE(TNI=0x112255)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt55 = Ether(dst="00:00:00:00:01:00")/IP()/NVGRE(TNI=0x112255)/Ether(dst="00:11:22:33:44:77")/IP()/TCP()/Raw('x' * 20)
    pkt56 = Ether(dst="00:11:22:33:44:66")/IP()/NVGRE(TNI=0x112255)/Ether(dst="00:11:22:33:44:77")/IP()/TCP()/Raw('x' * 20)
    pkt61 = Ether(dst="00:11:22:33:44:66")/IP()/NVGRE(TNI=0x112266)/Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=60)/IP()/TCP()/Raw('x' * 20)
    pkt62 = Ether(dst="00:11:22:33:44:66")/IP()/NVGRE(TNI=0x112266)/Ether(dst="00:11:22:33:44:77")/Dot1Q(vlan=60)/IP()/TCP()/Raw('x' * 20)
    pkt63 = Ether(dst="54:52:00:00:00:01")/IP()/NVGRE(TNI=0x112266)/Ether(dst="00:11:22:33:44:77")/Dot1Q(vlan=60)/IP()/TCP()/Raw('x' * 20)
    pkt64 = Ether(dst="00:00:00:00:01:00")/IP()/NVGRE(TNI=0x112266)/Ether(dst="00:11:22:33:44:77")/Dot1Q(vlan=60)/IP()/TCP()/Raw('x' * 20)
    pkt71 = Ether(dst="00:11:22:33:44:66")/IP()/NVGRE(TNI=0x112277)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt72 = Ether(dst="54:52:00:00:00:02")/IP()/NVGRE(TNI=0x112277)/Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw('x' * 20)
    pkt73 = Ether(dst="54:52:00:00:00:02")/IP()/NVGRE(TNI=0x112277)/Ether(dst="00:11:22:33:44:77")/IP()/TCP()/Raw('x' * 20)
    pkt74 = Ether(dst="00:00:00:00:01:00")/IP()/NVGRE(TNI=0x112277)/Ether(dst="00:11:22:33:44:77")/IP()/TCP()/Raw('x' * 20)

   verify pkt1 received by pf queue 1, pkt2 to pf queue 2,
   pkt31 to pf queue 3, pkt32 to pf queue 1, pkt4 to pf queue 4,
   pkt51 to pf queue 5, pkt52 to pf queue 1, pkt53 to pf queue 1,
   pkt54 to pf queue 1, pkt55 to pf queue 0, pf can't receive pkt56.
   pkt61 to vf0 queue 1 and pf queue 1, pf and vf0 can't receive pkt62,
   pkt63 to vf0 queue 0, pkt64 to pf queue 0, vf0 can't receive pkt64,
   pkt71 to vf1 queue 3 and pf queue 1, pkt72 to pf queue 1, vf1 can't receive
   pkt72, pkt73 to vf1 queue 0, pkt74 to pf queue 0, vf1 can't receive pkt74.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0

   verify pkt51 to pf queue 5, pkt53 and pkt55 to pf queue 0,
   pf can't receive pkt52,pkt54 and pkt56. pkt71 to vf1 queue 3,
   pkt72 and pkt73 to vf1 queue 0, pkt74 to pf queue 0, vf1 can't receive pkt74.
   Then::
    
    testpmd> flow flush 0
    testpmd> flow list 0

Test case: IXGBE SYN
====================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules

   ipv4::

    testpmd> flow create 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 3 / end

   ipv6::

    testpmd> flow destroy 0 rule 0
    testpmd> flow create 0 ingress pattern eth / ipv6 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 4 / end

   send packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=80,flags="S")/Raw('x' * 20)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=80,flags="PA")/Raw('x' * 20)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/TCP(dport=80,flags="S")/Raw('x' * 20)
    pkt4 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/TCP(dport=80,flags="PA")/Raw('x' * 20)

   ipv4 verify pkt1 to queue 3, pkt2 to queue 0, pkt3 to queue 3, pkt4 to queue 0
   ipv6 verify pkt1 to queue 4, pkt2 to queue 0, pkt3 to queue 4, pkt4 to queue 0
   notes: the out packet default is Flags [S], so if the flags is omitted in sent
   pkt, the pkt will be into queue 3 or queue 4.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0


Test case: IXGBE n-tuple(supported by x540 and 82599)
=====================================================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules

   ipv4-other::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 1 / end

   ipv4-udp::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 17 / udp src is 22 dst is 23 / end actions queue index 2 / end

   ipv4-tcp::

    testpmd> flow create 0 ingress pattern ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 6 / tcp src is 32 dst is 33 / end actions queue index 3 / end

   ipv4-sctp::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 132 / sctp src is 44 dst is 45 / end actions queue index 4 / end

3. send packets::

    pkt11 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x' * 20)
    pkt12 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw('x' * 20)
    pkt21 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=22,dport=23)/Raw('x' * 20)
    pkt22 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=22,dport=24)/Raw('x' * 20)
    pkt31 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=32,dport=33)/Raw('x' * 20)
    pkt32 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=34,dport=33)/Raw('x' * 20)
    pkt41 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=44,dport=45)/Raw('x' * 20)
    pkt42 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=44,dport=46)/Raw('x' * 20)
    pkt5 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=44,dport=45)/Raw('x' * 20)
    pkt6 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/TCP(sport=32,dport=33)/Raw('x' * 20)

   verify pkt11 to queue 1, pkt12 to queue 0,
   pkt21 to queue 2, pkt22 to queue 0,
   pkt31 to queue 3, pkt32 to queue 0,
   pkt41 to queue 4, pkt42 to queue 0,
   pkt5 to queue 1, pkt6 to queue 0,

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0


Test case: IXGBE ethertype
==========================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=16 --txq=16
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules::

    testpmd> flow validate 0 ingress pattern eth type is 0x0806 / end actions queue index 3 / end
    testpmd> flow validate 0 ingress pattern eth type is 0x86DD / end actions queue index 5 / end
    testpmd> flow create 0 ingress pattern eth type is 0x0806 / end actions queue index 3 / end
    testpmd> flow create 0 ingress pattern eth type is 0x88cc / end actions queue index 4 / end

   the ixgbe don't support the 0x88DD eth type packet. so the second command
   failed.

3. send packets::

    pkt1 = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.1.1")
    pkt2 = Ether(dst="00:11:22:33:44:55", type=0x88CC)/Raw('x' * 20)
    pkt3 = Ether(dst="00:11:22:33:44:55", type=0x86DD)/Raw('x' * 20)

   verify pkt1 to queue 3, and pkt2 to queue 4, pkt3 to queue 0.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0

   verify pkt1 to queue 0, and pkt2 to queue 4.
   Then::

    testpmd> flow list 0
    testpmd> flow flush 0

   verify pkt1 to queue 0, and pkt2 to queue 0.
   Then::

    testpmd> flow list 0

Test case: IXGBE fdir for ipv4
==============================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules

   ipv4-other
   (only support by 82599 and x540, this rule matches the n-tuple)::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 1 / end

   ipv4-udp::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.4 / udp src is 22 dst is 23 / end actions queue index 2 / end

   ipv4-tcp::

    testpmd> flow create 0 ingress pattern ipv4 src is 192.168.0.3 dst is 192.168.0.4 / tcp src is 32 dst is 33 / end actions queue index 3 / end

   ipv4-sctp
   (x550/x552, 82599 can support this format, because it matches n-tuple)::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.4 / sctp src is 44 dst is 45 / end actions queue index 4 / end

   ipv4-sctp(82599/x540)::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.4 / sctp / end actions queue index 4 / end

   ipv4-sctp-drop(x550/x552)::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.4 / sctp src is 46 dst is 47 / end actions drop / end

   ipv4-sctp-drop(82599/x540)::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.5 dst is 192.168.0.6 / sctp / end actions drop / end

notes: 82599 don't support the sctp port match drop, x550 and x552 support it.

   ipv4-udp-flexbytes::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / udp src is 24 dst is 25 / raw relative is 0 search is 0 offset is 44 limit is 0 pattern is 86 / end actions queue index 5 / end

   ipv4-tcp-flexbytes::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.4 / tcp src is 22 dst is 23 / raw relative spec 0 relative mask 1 search spec 0 search mask 1 offset spec 54 offset mask 0xffffffff limit spec 0 limit mask 0xffff pattern is ab pattern is cd / end actions queue index 6 / end

notes: the second pattern will overlap the first pattern.
the rule 6 and 7 should be created after the testpmd reset,
because the flexbytes rule is global bit masks.

   invalid queue id::
 
    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / udp src is 32 dst is 33 / end actions queue index 16 / end

notes: the rule can't be created successfully because the queue id
exceeds the max queue id.

3. send packets::

    pkt1 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x' * 20)
    pkt2 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.3", dst="192.168.0.4")/UDP(sport=22,dport=23)/Raw('x' * 20)
    pkt3 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.3", dst="192.168.0.4")/TCP(sport=32,dport=33)/Raw('x' * 20)

   for x552/x550::

    pkt41 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.3", dst="192.168.0.4")/SCTP(sport=44,dport=45)/Raw('x' * 20)
    pkt42 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.3", dst="192.168.0.4")/SCTP(sport=42,dport=43)/Raw('x' * 20)

   for 82599/x540::

    pkt41 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.3", dst="192.168.0.4")/SCTP()/Raw('x' * 20)
    pkt42 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.3", dst="192.168.0.5")/SCTP()/Raw('x' * 20)

   for x552/x550::

    pkt5 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.3", dst="192.168.0.4")/SCTP(sport=46,dport=47)/Raw('x' * 20)

   for 82599/x540::

    pkt5 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.5", dst="192.168.0.6")/SCTP()/Raw('x' * 20)
    pkt6 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=24,dport=25)/Raw(load="xx86ddef")
    pkt7 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.3", dst="192.168.0.4")/TCP(sport=22,dport=23)/Raw(load="abcdxxx")
    pkt8 = Ether(dst="A0:36:9F:7B:C5:A9")/IP(src="192.168.0.3", dst="192.168.0.4")/TCP(sport=22,dport=23)/Raw(load="cdcdxxx")

   verify pkt1 to pkt3 can be received by queue 1 to queue 3 correctly.
   pkt41 to queue 4, pkt42 to queue 0, pkt5 couldn't be received.
   pkt6 to queue 5, pkt7 to queue 0, pkt8 to queue 6.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0

Test case: IXGBE fdir for signature(ipv4/ipv6)
==============================================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules

   ipv6-other
   (82599 support this rule,x552 and x550 don't support this rule)::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 1 / ipv6 src is 2001::1 dst is 2001::2 / end actions queue index 1 / end

   ipv6-udp::

    testpmd> flow create 0 ingress pattern fuzzy thresh spec 2 thresh last 5 thresh mask 0xffffffff / ipv6 src is 2001::1 dst is 2001::2 / udp src is 22 dst is 23 / end actions queue index 2 / end

   ipv6-tcp::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 3 / ipv6 src is 2001::1 dst is 2001::2 / tcp src is 32 dst is 33 / end actions queue index 3 / end

   ipv6-sctp
   (x552 and x550)::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 4 / ipv6 src is 2001::1 dst is 2001::2 / sctp src is 44 dst is 45 / end actions queue index 4 / end

   (82599 and x540)::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 4 / ipv6 src is 2001::1 dst is 2001::2 / sctp / end actions queue index 4 / end

   ipv6-other-flexbytes
   (just for 82599/x540)::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 6 / ipv6 src is 2001::1 dst is 2001::2 / raw relative is 0 search is 0 offset is 56 limit is 0 pattern is 86 / end actions queue index 5 / end

notes: this rule can be created successfully on 82599/x540, but can't be
created successfully on x552/x550, because it's an ipv4-other rule.
but the offset<=62, the mac header is 14bytes, the ipv6 header is 40 bytes,
the shortest L4 header (udp header) is 8bytes, the total header is 62 bytes,
there is no payload can be set offset. so we don't test the ipv6 flexbytes
on x550/x552.
according to hardware limitation, signature mode does not support drop action,
while IPv6 rely on signature mode, so it is expected result that a IPv6 flow
with drop action can't be created

   ipv4-other
   (82599 support this rule,x552 and x550 don't support this rule)::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 1 / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 6 / end

   ipv4-udp::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 2 / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / udp src is 22 dst is 23 / end actions queue index 7 / end

   ipv4-tcp::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 3 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / tcp src is 32 dst is 33 / end actions queue index 8 / end

   ipv4-sctp(x550/x552)::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 4 / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / sctp src is 44 dst is 45 / end actions queue index 9 / end

   ipv4-sctp(82599/x540)::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 5 / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / sctp / end actions queue index 9 / end

notes: if set the ipv4-sctp rule with sctp ports on 82599, it will fail
to create the rule.

   ipv4-sctp-flexbytes(x550/x552)::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 6 / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / sctp src is 24 dst is 25 / raw relative is 0 search is 0 offset is 48 limit is 0 pattern is ab / end actions queue index 10 / end

   ipv4-sctp-flexbytes(82599/x540)::

    testpmd> flow create 0 ingress pattern fuzzy thresh is 6 / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / sctp / raw relative is 0 search is 0 offset is 48 limit is 0 pattern is ab / end actions queue index 10 / end

notes: you need to reset testpmd before create this rule,
because it's conflict with the rule 9.

3. send packets

   ipv6 packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/Raw('x' * 20)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/UDP(sport=22,dport=23)/Raw('x' * 20)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/TCP(sport=32,dport=33)/Raw(load="xxxxabcd")

   for x552/x550::

    pkt4 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2",nh=132)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="cdxxxx")
    pkt5 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2",nh=132)/SCTP(sport=46,dport=47,tag=1)/SCTPChunkData(data="cdxxxx")

   for 82599/x540::

    pkt41 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2",nh=132)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="cdxxxx")
    pkt42 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2",nh=132)/SCTP()/SCTPChunkData(data="cdxxxx")
    pkt51 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2",nh=132)/SCTP(sport=46,dport=47,tag=1)/SCTPChunkData(data="cdxxxx")
    pkt52 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="2001::4",nh=132)/SCTP(sport=46,dport=47,tag=1)/SCTPChunkData(data="cdxxxx") 
    pkt6 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/Raw(load="xx86abcd")
    pkt7 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/Raw(load="xxx86abcd")

   ipv4 packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x' * 20)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/Raw('x' * 20)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=32,dport=33)/Raw('x' * 20)

   for x552/x550::

    pkt41 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=44,dport=45)/Raw('x' * 20)
    pkt42 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=42,dport=43)/Raw('x' * 20)

   for 82599/x540::

    pkt41 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP()/Raw('x' * 20)
    pkt42 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.3")/SCTP()/Raw('x' * 20)
    pkt51 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=24,dport=25)/Raw(load="xxabcdef")
    pkt52 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=24,dport=25)/Raw(load="xxaccdef")

   verify ipv6 packets:
   for x552/x550:
   pkt1 to queue 0, pkt2 to queue 2, pkt3 to queue 3.
   pkt4 to queue 4, pkt5 to queue 0.

   for 82599/x540:
   packet pkt1 to pkt3 can be received by queue 1 to queue 3 correctly.
   pkt41 and pkt42 to queue 4, pkt51 to queue 4, pkt52 to queue 0. 
   pkt6 to queue 5, pkt7 to queue 0.

   verify ipv4 packets:
   for x552/x550:
   pk1 to queue 0, pkt2 to queue 7, pkt3 to queue 8.
   pkt41 to queue 9, pkt42 to queue 0,
   pkt51 to queue 10, pkt52 to queue 0.

   for 82599/x540:
   pkt1 to pkt3 can be received by queue 6 to queue 8 correctly.
   pkt41 to queue 9, pkt42 to queue 0,
   pkt51 to queue 10, pkt52 to queue 0.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0

Test case: IXGBE fdir for mac/vlan(support by x540, x552, x550)
===============================================================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start
    testpmd> vlan set strip off 0
    testpmd> vlan set filter off 0

2. create filter rules::

    testpmd> flow create 0 ingress pattern eth dst is A0:36:9F:7B:C5:A9 / vlan tpid is 0x8100 tci is 1 / end actions queue index 9 / end
    testpmd> flow create 0 ingress pattern eth dst is A0:36:9F:7B:C5:A9 / vlan tpid is 0x8100 tci is 4095 / end actions queue index 10 / end

3. send packets::

    pkt1 = Ether(dst="A0:36:9F:7B:C5:A9")/Dot1Q(vlan=1)/IP()/TCP()/Raw('x' * 20)
    pkt2 = Ether(dst="A0:36:9F:7B:C5:A9")/Dot1Q(vlan=4095)/IP()/UDP()/Raw('x' * 20)

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0


Test case: IXGBE fdir for tunnel (vxlan and nvgre)(support by x540, x552, x550)
===============================================================================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules

   vxlan::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / vxlan vni is 8 / eth dst is A0:36:9F:7B:C5:A9 / vlan tci is 2 tpid is 0x8100 / end actions queue index 1 / end
    testpmd> flow create 0 ingress pattern eth / ipv6 / udp / vxlan vni is 9 / eth dst is A0:36:9F:7B:C5:A9 / vlan tci is 4095 tpid is 0x8100 / end actions queue index 2 / end

   nvgre::

    testpmd> flow create 0 ingress pattern eth / ipv4 / nvgre tni is 0x112244 / eth dst is A0:36:9F:7B:C5:A9 / vlan tci is 20 / end actions queue index 3 / end
    testpmd> flow create 0 ingress pattern eth / ipv6 / nvgre tni is 0x112233 / eth dst is A0:36:9F:7B:C5:A9 / vlan tci is 21 / end actions queue index 4 / end

3. send packets

   vxlan::

    pkt1=Ether(dst="A0:36:9F:7B:C5:A9")/IP()/UDP()/Vxlan(vni=8)/Ether(dst="A0:36:9F:7B:C5:A9")/Dot1Q(vlan=2)/IP()/TCP()/Raw('x' * 20)
    pkt2=Ether(dst="A0:36:9F:7B:C5:A9")/IPv6()/UDP()/Vxlan(vni=9)/Ether(dst="A0:36:9F:7B:C5:A9")/Dot1Q(vlan=4095)/IP()/TCP()/Raw('x' * 20)

   nvgre::

    pkt3 = Ether(dst="A0:36:9F:7B:C5:A9")/IP()/NVGRE(TNI=0x112244)/Ether(dst="A0:36:9F:7B:C5:A9")/Dot1Q(vlan=20)/IP()/TCP()/Raw('x' * 20)
    pkt4 = Ether(dst="A0:36:9F:7B:C5:A9")/IPv6()/NVGRE(TNI=0x112233)/Ether(dst="A0:36:9F:7B:C5:A9")/Dot1Q(vlan=21)/IP()/TCP()/Raw('x' * 20)

   verify pkt1 to pkt4 are into queue 1 to queue 4.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0

Test case: igb SYN
==================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=8 --txq=8 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules

   ipv4::

    testpmd> flow create 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 3 / end

   ipv6::

    testpmd> flow destroy 0 rule 0
    testpmd> flow create 0 ingress pattern eth / ipv6 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 4 / end

3. send packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=80,flags="S")/Raw('x' * 20)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/TCP(dport=80,flags="S")/Raw('x' * 20)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=80,flags="PA")/Raw('x' * 20)
    pkt4 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/TCP(dport=80,flags="PA")/Raw('x' * 20)

   ipv4 verify pkt1 to queue 3, pkt2 to queue 0, pkt3 to queue 0
   ipv6 verify pkt2 to queue 4, pkt1 to queue 0, pkt4 to queue 0

notes: the out packet default is Flags [S], so if the flags is omitted in
sent pkt, the pkt will be into queue 3 or queue 4.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0

Test case: igb n-tuple(82576)
=============================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=8 --txq=8 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 proto is 17 / udp src is 22 dst is 23 / end actions queue index 1 / end
    testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 proto is 6 / tcp src is 22 dst is 23 / end actions queue index 2 / end

3. send packets::

    pkt1 = Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/Raw('x' * 20)
    pkt2 = Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=32,dport=33)/Raw('x' * 20)

   verify pkt1 to queue 1, pkt2 to queue 2, pkt3 to queue 3.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0

Test case: igb n-tuple(i350 or 82580)
=====================================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=8 --txq=8 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 proto is 17 / udp dst is 23 / end actions queue index 1 / end
    testpmd> flow create 0 ingress pattern eth / ipv4 proto is 6 / tcp dst is 33 / end actions queue index 2 / end

3. send packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/Raw('x' * 20)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=24)/Raw('x' * 20)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=32,dport=33)/Raw('x' * 20)
    pkt4 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=32,dport=34)/Raw('x' * 20)

   verify pkt1 to queue 1, pkt2 to queue 0.
   pkt3 to queue 2, pkt4 to queue 0.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0

Test case: igb ethertype
========================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=8 --txq=8
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules::

    testpmd> flow validate 0 ingress pattern eth type is 0x0806 / end actions queue index 3 / end
    testpmd> flow validate 0 ingress pattern eth type is 0x86DD / end actions queue index 5 / end
    testpmd> flow create 0 ingress pattern eth type is 0x0806 / end actions queue index 3 / end
    testpmd> flow create 0 ingress pattern eth type is 0x88cc / end actions queue index 4 / end
    testpmd> flow create 0 ingress pattern eth type is 0x88cc / end actions queue index 8 / end

   the ixgbe don't support the 0x88DD eth type packet. so the second command
   failed. the queue id exceeds the max queue id, so the last command failed.

3. send packets::

    pkt1 = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.1.1")
    pkt2 = Ether(dst="00:11:22:33:44:55", type=0x88CC)/Raw('x' * 20)

   verify pkt1 to queue 3, and pkt2 to queue 4.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    verify pkt1 to queue 0, and pkt2 to queue 4.
    testpmd> flow list 0
    testpmd> flow flush 0

   verify pkt1 to queue 0, and pkt2 to queue 0
   Then::

    testpmd> flow list 0

Test case: igb flexbytes
========================

1. Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 1ffff -n 4 -- -i --rxq=8 --txq=8 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. create filter rules

   l2 packet::

    testpmd> flow create 0 ingress pattern raw relative is 0 offset is 14 pattern is fhds / end actions queue index 1 / end

   l2 packet relative is 1
   (the first relative must be 0, so this rule won't work)::

    testpmd> flow create 0 ingress pattern raw relative is 1 offset is 2 pattern is fhds / end actions queue index 2 / end

   ipv4 packet::
 
    testpmd> flow create 0 ingress pattern raw relative is 0 offset is 34 pattern is ab / end actions queue index 3 / end

   ipv6 packet::

    testpmd> flow create 0 ingress pattern raw relative is 0 offset is 58 pattern is efgh / end actions queue index 4 / end

   3 fields relative is 0::

    testpmd> flow create 0 ingress pattern raw relative is 0 offset is 38 pattern is ab / raw relative is 0 offset is 34 pattern is cd / raw relative is 0 offset is 42 pattern is efgh / end actions queue index 5 / end

   4 fields relative is 0 and 1::

    testpmd> flow create 0 ingress pattern raw relative is 0 offset is 48 pattern is ab / raw relative is 1 offset is 0 pattern is cd / raw relative is 0 offset is 44 pattern is efgh / raw relative is 1 offset is 10 pattern is hijklmnopq / end actions queue index 6 / end

   3 fields offset conflict::

    testpmd> flow create 0 ingress pattern raw relative is 0 offset is 64 pattern is ab / raw relative is 1 offset is 4 pattern is cdefgh / raw relative is 0 offset is 68 pattern is klmn / end actions queue index 7 / end

   1 field 128bytes
   
   flush the rules::

    testpmd> flow flush 0

   then create the rule::

    testpmd> flow create 0 ingress pattern raw relative is 0 offset is 128 pattern is ab / end actions queue index 1 / end
    testpmd> flow create 0 ingress pattern raw relative is 0 offset is 126 pattern is abcd / end actions queue index 1 / end
    testpmd> flow create 0 ingress pattern raw relative is 0 offset is 126 pattern is ab / end actions queue index 1 / end

   the first two rules failed to create, only the last flow rule is created successfully.

   2 field 128bytes::

    testpmd> flow create 0 ingress pattern raw relative is 0 offset is 68 pattern is ab / raw relative is 1 offset is 58 pattern is cd / end actions queue index 2 / end
    testpmd> flow create 0 ingress pattern raw relative is 0 offset is 68 pattern is ab / raw relative is 1 offset is 56 pattern is cd / end actions queue index 2 / end

   the first rule failed to create, only the last flow rule is created successfully.

3. send packets::

    pkt11 = Ether(dst="00:11:22:33:44:55")/Raw(load="fhdsab")
    pkt12 = Ether(dst="00:11:22:33:44:55")/Raw(load="afhdsb")
    pkt2 = Ether(dst="00:11:22:33:44:55")/Raw(load="abfhds")
    pkt3 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="abcdef")
    pkt41 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/Raw(load="xxxxefgh")
    pkt42 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2")/TCP(sport=32,dport=33)/Raw(load="abcdefgh")
    pkt5 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="cdxxabxxefghxxxx")
    pkt6 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2", tos=4, ttl=3)/UDP(sport=32,dport=33)/Raw(load="xxefghabcdxxxxxxhijklmnopqxxxx")
    pkt71 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxabxxklmnefgh")
    pkt72 = Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1", dst="2001::2", tc=3, hlim=30)/Raw(load="xxxxxxxxxxabxxklmnefgh")
    pkt73 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxabxxklcdefgh")
    pkt81 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxab")
    pkt82 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxcb")
    pkt91 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxxxxxabxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxcd")
    pkt92 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxxxxxabxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxce")

   verify pkt11 to queue 1, pkt12 to queue 0.
   pkt2 to queue 0.
   pkt3 to queue 3.
   pkt41 to queue 4, pkt42 to queue 0, // tcp header has 20 bytes.
   pkt5 to queue 5.
   pkt6 to queue 6.
   pkt71 to queue 7, pkt72 to queue 7, pkt73 to queue 0.
   pkt81 to queue 1, pkt82 to queue 0.
   pkt91 to queue 2, pkt92 to queue 0.

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0
    testpmd> flow flush 0
    testpmd> flow list 0

Test case: Intel® Ethernet 700 Series fdir for l2 mac
=====================================================
    Prerequisites:

    bind the PF to dpdk driver::
        ./usertools/dpdk-devbind.py -b igb_uio 0000:81:00.0

    launch testpmd::
        ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 0-3 -n 4 -a 0000:81:00.0 -- -i --rxq=4 --txq=4

1. basic test for ipv4-other

    1) validate a rule::
        testpmd> flow validate 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end

        Verify the commend can validete::
            Flow rule validated

    2) create a rule::
        testpmd> flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        send packets not match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    3) list the rule::
        testpmd> flow list 0

        Verify there are one rule.

    4) flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    5) list the rule::
        testpmd> flow list 0

        Verify there are no rule.

    6) validate a rule::
        testpmd> flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / end actions mark id 1 / rss / end

        Verify the commend can validete::
            Flow rule validated

    7) create a rule::
        testpmd> flow create 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / end actions mark id 1 / rss / end

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        send packets not match rule 0::
            sendp(Ether(src='88:88:88:88:88:88',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    8) list the rule::
        testpmd> flow list 0

        Verify there are one rule.

    9) flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    10) list the rule::
        testpmd> flow list 0

        Verify there are no rule.

    11) validate a rule::
        testpmd> flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end

        Verify the commend can validete::
            Flow rule validated

    12) create a rule::
        testpmd> flow create 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        send packets not match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")
            sendp(Ether(src='88:88:88:88:88:88',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")
            sendp(Ether(src='88:88:88:88:88:88',dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    13) list the rule::
        testpmd> flow list 0

        Verify there are one rule.

    14) destory the rule::
        testpmd> flow destroy 0 rule 0

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    15) list the rule::
        testpmd> flow list 0

        Verify there are no rule.

2. basic test for ipv4-udp

    1) validate a rule::
        testpmd> flow validate 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / udp / end actions mark id 1 / rss / end

        Verify the commend can validete::
            Flow rule validated

    2) create a rule::
        testpmd> flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / udp / end actions mark id 1 / rss / end

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/UDP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        send packets not match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/UDP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    3) list the rule::
        testpmd> flow list 0

        Verify there are one rule.

    4) flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/UDP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    5) list the rule::
        testpmd> flow list 0

        Verify there are no rule.

    6) validate a rule::
        testpmd> flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / udp / end actions mark id 1 / rss / end

        Verify the commend can validete::
            Flow rule validated

    7) create a rule::
        testpmd> flow create 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / udp / end actions mark id 1 / rss / end

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/UDP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        send packets not match rule 0::
            sendp(Ether(src='88:88:88:88:88:88',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/UDP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    8) list the rule::
        testpmd> flow list 0

        Verify there are one rule.

    9) flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/UDP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    10) list the rule::
        testpmd> flow list 0

        Verify there are no rule.

    11) validate a rule::
        testpmd> flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / udp / end actions mark id 1 / rss / end

        Verify the commend can validete::
            Flow rule validated

    12) create a rule::
        testpmd> flow create 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / udp / end actions mark id 1 / rss / end

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/UDP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        send packets not match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/UDP()/"Hello!0",iface="enp129s0f1")
            sendp(Ether(src='88:88:88:88:88:88',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/UDP()/"Hello!0",iface="enp129s0f1")
            sendp(Ether(src='88:88:88:88:88:88',dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/UDP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    13) list the rule::
        testpmd> flow list 0

        Verify there are one rule.

    14) destory the rule::
        testpmd> flow destroy 0 rule 0

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/UDP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    15) list the rule::
        testpmd> flow list 0

        Verify there are no rule.

3. basic test for ipv4-tcp

    1) validate a rule::
        testpmd> flow validate 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / tcp / end actions mark id 1 / rss / end

        Verify the commend can validete::
            Flow rule validated

    2) create a rule::
        testpmd> flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / tcp / end actions mark id 1 / rss / end

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/TCP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        send packets not match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/TCP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    3) list the rule::
        testpmd> flow list 0

        Verify there are one rule.

    4) flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/TCP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    5) list the rule::
        testpmd> flow list 0

        Verify there are no rule.

    6) validate a rule::
        testpmd> flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / tcp / end actions mark id 1 / rss / end

        Verify the commend can validete::
            Flow rule validated

    7) create a rule::
        testpmd> flow create 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / tcp / end actions mark id 1 / rss / end

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/TCP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        send packets not match rule 0::
            sendp(Ether(src='88:88:88:88:88:88',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/TCP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    8) list the rule::
        testpmd> flow list 0

        Verify there are one rule.

    9) flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/TCP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    10) list the rule::
        testpmd> flow list 0

        Verify there are no rule.

    11) validate a rule::
        testpmd> flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / tcp / end actions mark id 1 / rss / end

        Verify the commend can validete::
            Flow rule validated

    12) create a rule::
        testpmd> flow create 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / tcp / end actions mark id 1 / rss / end

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/TCP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        send packets not match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/TCP()/"Hello!0",iface="enp129s0f1")
            sendp(Ether(src='88:88:88:88:88:88',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/TCP()/"Hello!0",iface="enp129s0f1")
            sendp(Ether(src='88:88:88:88:88:88',dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/TCP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    13) list the rule::
        testpmd> flow list 0

        Verify there are one rule.

    14) destory the rule::
        testpmd> flow destroy 0 rule 0

        send packets match rule 0::
            sendp(Ether(src='99:99:99:99:99:99',dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/TCP()/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    15) list the rule::
        testpmd> flow list 0

        Verify there are no rule.

4. complex test

    1) create rules and destory the first::
        create three rules::
            testpmd> flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end
            testpmd> flow create 0 ingress pattern eth dst is 22:22:22:22:22:22 / ipv4 / end actions mark id 2 / rss / end
            testpmd> flow create 0 ingress pattern eth dst is 33:33:33:33:33:33 / ipv4 / end actions mark id 3 / rss / end

        list the rules::
            testpmd> flow list 0

        Verify there are three rules.

        send packets::
            sendp(Ether(dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")
            sendp(Ether(dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")
            sendp(Ether(dst='33:33:33:33:33:33')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        destory the first rule::
            testpmd> flow destroy 0 rule 0

        list the rules::
            testpmd> flow list 0

        Verify there are rule 1 and rule 2.

        send packets match rule 0::
            sendp(Ether(dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

        send packets match rule 1 and rule 2::
            sendp(Ether(dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")
            sendp(Ether(dst='33:33:33:33:33:33')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        flush rules::
            testpmd> flow flush 0

        send packets match rule 0, rule 1 and rule 2::
            sendp(Ether(dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")
            sendp(Ether(dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")
            sendp(Ether(dst='33:33:33:33:33:33')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

    2) create rules and destory the second::
        create three rules::
            testpmd> flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end
            testpmd> flow create 0 ingress pattern eth dst is 22:22:22:22:22:22 / ipv4 / end actions mark id 2 / rss / end
            testpmd> flow create 0 ingress pattern eth dst is 33:33:33:33:33:33 / ipv4 / end actions mark id 3 / rss / end

        list the rules::
            testpmd> flow list 0

        Verify there are three rules.

        destory the second rule::
            testpmd> flow destroy 0 rule 1

        list the rules::
            testpmd> flow list 0

        Verify there are rule 0 and rule 2.

        send packets match rule 1::
            sendp(Ether(dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

        send packets match rule 0 and rule 2::
            sendp(Ether(dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")
            sendp(Ether(dst='33:33:33:33:33:33')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

        flush rules::
            testpmd> flow flush 0

   3) create rules and destory the third::
        create three rules::
            testpmd> flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end
            testpmd> flow create 0 ingress pattern eth dst is 22:22:22:22:22:22 / ipv4 / end actions mark id 2 / rss / end
            testpmd> flow create 0 ingress pattern eth dst is 33:33:33:33:33:33 / ipv4 / end actions mark id 3 / rss / end

        list the rules::
            testpmd> flow list 0

        Verify there are three rules.

        destory the second rule::
            testpmd> flow destroy 0 rule 2

        list the rules::
            testpmd> flow list 0

        Verify there are rule 0 and rule 1.

        send packets match rule 2::
            sendp(Ether(dst='33:33:33:33:33:33')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can not mark.

        send packets match rule 0 and rule 1::
            sendp(Ether(dst='11:11:11:11:11:11')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")
            sendp(Ether(dst='22:22:22:22:22:22')/IP(src=RandIP(),dst='2.2.2.5')/"Hello!0",iface="enp129s0f1")

        Verify all packets can rss and mark.

5. negative test

    1) ip in command::
        creat rule::
            testpmd> flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 dst is 1.1.1.1 / end actions mark id 2 / rss / end
            Verify rule can not be created.

    2) udp in command::
        creat rule::
            testpmd> flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / udp dst is 111 / end actions mark id 2 / rss / end
            Verify rule can not be created.

    3) tcp in command::
        creat rule::
            testpmd> flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / tcp dst is 111 / end actions mark id 2 / rss / end
            Verify rule can not be created.

    4) kinds rule conflict::
        creat rule::
            testpmd> flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 3 / rss / end
            testpmd> flow create 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / end actions mark id 1 / rss / end
            Verify second rule can not be created.

        flush rules::
            testpmd> flow flush 0

        creat rule::
            testpmd> flow create 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / end actions mark id 1 / rss / end
            testpmd> flow create 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end

        Verify second rule can not be created.

        flush rules::
            testpmd> flow flush 0

        creat rule::
            testpmd> flow create 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end
            testpmd> flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 3 / rss / end

        Verify second rule can not be created.

Test case: Dual vlan(QinQ)
==========================

1. config testpmd on DUT

   1. set up testpmd with Intel® Ethernet 700 Series NICs::

         ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x1ffff -n 4 -- -i --coremask=0x1fffe --portmask=0x1 --rxq=16 --txq=16

   2. verbose configuration::

         testpmd> set verbose 8

   3. PMD fwd only receive the packets::

         testpmd> set fwd rxonly

   4. set extend on::

         testpmd> vlan set extend on <port_id>

   5. create rule::

         testpmd> flow create 0 ingress pattern eth / end actions rss types l2-payload end queues end func toeplitz / end

   6. start packet receive::

         testpmd> start


2. using scapy to send packets with dual vlan (QinQ) on tester::


         sendp([Ether(dst="68:05:ca:30:6a:f8")/Dot1Q(id=0x8100,vlan=1)/Dot1Q(id=0x8100,vlan=2,type=0xaaaa)/Raw(load="x"*60)], iface=ttester_itf)

   then got hash value and queue value that output from the testpmd on DUT.

3. create flow rss type s-vlan c-vlan by testpmd on dut::


      testpmd> flow create 0 ingress pattern eth / end actions rss types s-vlan c-vlan end key_len 0 queues end / end

   1). send packet as step 2, got hash value and queue value that output from the testpmd on DUT, the value should be
   different with the values in step 2.


   2). send packet as step 2 with changed ovlan id, got hash value and queue value that output from the testpmd on DUT, the value should be
   different with the values in step 2 & step 1).

   3). send packet as step 2 with changed ivlan id, got hash value and queue value that output from the testpmd on DUT, the value should be
   different with the values in step 2 & step 1) & step 2).

Test case: create same rule after destroy
=========================================
support NIC: Intel® Ethernet 700 Series, Intel® Ethernet 800 Series and 82599.

1. Launch the app ``testpmd`` with the following arguments::

        ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1,2,3,4,5,6,7,8 -n 4 -- -i --disable-rss --rxq=16 --txq=16
        testpmd> set fwd rxonly
        testpmd> set verbose 1
        testpmd> start

2. create same rule after destroy::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp src is 32 / end actions queue index 2 / end
        testpmd>flow destroy 0 rule 0
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp src is 32 / end actions queue index 2 / end

3. send match and mismatch packets to check if rule work::

    pkt1 = Ether()/IP()/UDP(sport=32)/Raw('x' * 20)
    pkt2 = Ether()/IP()/UDP(dport=32)/Raw('x' * 20)

    verify match pkt1 to queue 2, verify mismatch pkt2 to queue 0.

Test case: create different rule after destroy
==============================================
support NIC: Intel® Ethernet 700 Series, Intel® Ethernet 800 Series and 82599.

1. Launch the app ``testpmd`` with the following arguments::

        ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1,2,3,4,5,6,7,8 -n 4 -- -i --disable-rss --rxq=16 --txq=16
        testpmd> set fwd rxonly
        testpmd> set verbose 1
        testpmd> start

2. create different rule after destroy::

        testpmd>flow create 0 ingress pattern eth / ipv4 / udp src is 32 / end actions queue index 2 / end
        testpmd>flow destroy 0 rule 0
        testpmd>flow create 0 ingress pattern eth / ipv4 / udp dst is 32 / end actions queue index 2 / end

3. send match and mismatch packets to check if rule work::

    pkt1 = Ether()/IP()/UDP(sport=32)/Raw('x' * 20)
    pkt2 = Ether()/IP()/UDP(dport=32)/Raw('x' * 20)

    verify match pkt2 to queue 2, verify mismatch pkt1 to queue 0.

Test Case: 10GB Multiple filters
================================
only supported by ixgbe and igb

1. config testpmd on DUT

   1. set up testpmd with 82599 NICs::

         ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1,2,3,4,5,6,7,8 -n 4 -- -i --disable-rss --rxq=16 --txq=16

   2. verbose configuration::

         testpmd> set verbose 1

   3. PMD fwd only receive the packets::

         testpmd> set fwd rxonly

   4. start packet receive::

         testpmd> start

   5. create rule,Enable ethertype filter, SYN filter and 5-tuple Filter on the port 0 at same
   time. Assigning different filters to different queues on port 0::

         testpmd> flow validate 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 1 / end
         testpmd> flow validate 0 ingress pattern eth type is 0x0806  / end actions queue index 2 /  end
         testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 2.2.2.5 src is 2.2.2.4 proto is 17 / udp dst is 1 src is 1  / end actions queue index 3 /  end
         testpmd> flow create 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 1 / end
         testpmd> flow create 0 ingress pattern eth type is 0x0806  / end actions queue index 2 /  end
         testpmd> flow create 0 ingress pattern eth / ipv4 dst is 2.2.2.5 src is 2.2.2.4 proto is 17 / udp dst is 1 src is 1  / end actions queue index 3 /  end

2. Configure the traffic generator to send different packets. Such as,SYN packets, ARP packets, IP packets and
packets with(`dst_ip` = 2.2.2.5 `src_ip` = 2.2.2.4 `dst_port` = 1 `src_port` = 1 `protocol` = udp)::

    sendp([Ether(dst="90:e2:ba:36:99:34")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=80,flags="S")/Raw("x" * 20)],iface="ens224f0",count=1,inter=0,verbose=False)
    sendp([Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.1.1")/Raw("x" * 20)],iface="ens224f0",count=1,inter=0,verbose=False)
    sendp([Ether(dst="90:e2:ba:36:99:34")/Dot1Q(prio=3)/IP(src="2.2.2.4",dst="2.2.2.5")/UDP(sport=1,dport=1)],iface="ens224f0",count=1,inter=0,verbose=False)

3. Verify that all packets are received (RX-packets incremented)on the assigned
queue, remove 5-tuple filter::

    testpmd> stop
    testpmd> start
    testpmd> flow destroy 0 rule 2

4. Send different packets such as,SYN packets, ARP packets, packets with
(`dst_ip` = 2.2.2.5 `src_ip` = 2.2.2.4 `dst_port` = 1 `src_port` = 1
`protocol` = udp)::

    testpmd> stop

5. Verify that different packets are received (RX-packets incremented)on the
assigned queue export 5-tuple filter, remove ethertype filter::

    testpmd> start
    testpmd> flow destroy 0 rule 1

Send different packets such as,SYN packets, ARP packets, packets with
(`dst_ip` = 2.2.2.5 `src_ip` = 2.2.2.4 `dst_port` = 1 `src_port` = 1
`protocol` = udp)::

    testpmd>stop

Verify that only SYN packets are received (RX-packets incremented)on the
assigned queue set off SYN filter,remove syn filter::

    testpmd>start
    testpmd>flow destroy 0 rule 0

Configure the traffic generator to send SYN packets::

    testpmd>stop

Verify that the packets are not received (RX-packets do not increased)on the
queue 1.

Test Case: jumbo framesize filter
=================================

This case is designed for NIC (82599, I350, 82576 and 82580). Since
``Testpmd`` could transmits packets with jumbo frame size , it also could
transmit above packets on assigned queue.  Launch the app ``testpmd`` with the
following arguments::

    dpdk-testpmd -l 1,2,3,4,5,6,7,8 -n 4 -- -i --disable-rss --rxq=4 --txq=4 --portmask=0x3 --nb-cores=4 --nb-ports=1 --mbcache=200 --mbuf-size=2048 --max-pkt-len=9600
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

Enable the syn filters with large size::

    testpmd> flow validate 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 2 / end
    testpmd> flow create 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 2 / end

Configure the traffic generator to send syn packets::

    sendp([Ether(dst="90:e2:ba:36:99:34")/IP(src="2.2.2.5",dst="2.2.2.4")/TCP(dport=80,flags="S")/Raw(load="P"*8962)],iface="ens224f0",count=1,inter=0,verbose=False)
    testpmd> stop

Then Verify that the packet are received on the queue 2. Configure the traffic generator to send arp packets::

    testpmd> start
    sendp([Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.1.1")],iface="ens224f0",count=1,inter=0,verbose=False)

Then Verify that the packet are not received on the queue 2.  Remove the filter::

    testpmd> flow destroy 0 rule 0

Configure the traffic generator to send syn packets. Then Verify that
the packet are not received on the queue 2::

    testpmd> stop

Test Case: 64 queues
====================

This case is designed for NIC(82599). Default use 64 queues for test

Launch the app ``testpmd`` with the following arguments::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1,2,3,4,5 -n 4 -- -i --disable-rss --rxq=64 --txq=64 --portmask=0x3 --nb-cores=4 --total-num-mbufs=263168

    testpmd>set stat_qmap rx 0 0 0
    testpmd>set stat_qmap rx 1 0 0
    testpmd>vlan set strip off 0
    testpmd>vlan set strip off 1
    testpmd>vlan set filter off 0
    testpmd>vlan set filter off 1

Create the 5-tuple Filters with different queues (32,63) on port 0 for
82599::

    testpmd> set stat_qmap rx 0 32 1
    testpmd> flow create 0 ingress pattern eth / ipv4 dst is 2.2.2.5 src is 2.2.2.4 / tcp dst is 1 src is 1 / end actions queue index 32 / end
    testpmd> set stat_qmap rx 0 63 2
    testpmd> flow create 0 ingress pattern eth / ipv4 dst is 2.2.2.5 src is 2.2.2.4 / tcp dst is 2 src is 1 / end actions queue index 63 / end

Send packets(`dst_ip` = 2.2.2.5 `src_ip` = 2.2.2.4 `dst_port` = 1 `src_port` =
1 `protocol` = tcp) and (`dst_ip` = 2.2.2.5 `src_ip` = 2.2.2.4 `dst_port` = 2
`src_port` = 1 `protocol` = tcp ). Then reading the stats for port 0 after
sending packets. packets are received on the queue 32 and queue 63 When
setting 5-tuple Filter with queue(64), it will display failure because the
number of queues no more than 64.
