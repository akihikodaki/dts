
Common steps for launching DCF
==============================

Generate 1 trust VF on 1 PF, and request 1 DCF on the trust VF.
PF should grant DCF mode to it.

Generate 4 VFs on PF ::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

Set a VF as trust ::

    ip link set enp24s0f0 vf 0 trust on
    ip link set enp27s0f0 vf 0 mac D2:6B:4C:EB:1C:26

Launch dpdk on the VF, request DCF mode ::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-10 -n 4 -w 18:01.0,cap=dcf --file-prefix=vf -- -i


Test Case: Launch DCF and do macfwd
===================================

Execute **common steps** to prepare DCF test environment

Set macfwd ::

    set fwd mac
    start

Launch tcpdump to sniffer the packets from DCF ::

    tcpdump -i enp24s0f1 -vvv -Q in

Send packets from tester(scapy) to the VF by MAC address(D2:6B:4C:EB:1C:26) ::

    p = Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="192.168.1.1",dst="192.168.1.3")/Raw('x'*64)
    sendp(p, iface=intf, count=100)

Expect tester can get packets which loopbacked by DCF.


Test Case: Check default rss for L3
===================================

DCF data path support RSS packets by default. For L3 packets, input set is IP src/dst.
For tunneling packets, input set is inner IP src/dst.

Execute **common steps** to prepare DCF test environment

Set rxonly forward mode ::

    set fwd rxonly
    set verbose 1
    start
    
Send a series packets to check if DCF RSS is correct for IPv4 ::

    intf="enp175s0f0" 
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.2")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.2")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.2")/Raw('x'*64), iface=intf)

Expected: p1 hash value is not equal to p2 or p3, and should be same to p4.

Send a series packets to check if DCF RSS is correct for IPv6 ::

    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IPv6(src="::22", dst="::11")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IPv6(src="::22", dst="::12")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IPv6(src="::21", dst="::11")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IPv6(src="::22", dst="::11")/Raw('x'*64), iface=intf)

Expected: p1 hash value is not equal to p2 or p3, and should be same to p4.

Send a series packets to check if DCF RSS is correct for tunnelling packet (inner IPv4) ::

    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IP(src="192.168.1.1", dst="192.168.1.2")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IP(src="192.168.1.1", dst="192.168.1.3")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IP(src="192.168.1.3", dst="192.168.1.2")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="11:22:33:44:55:77")/IP(src="1.1.1.2", dst="2.2.2.1")/GRE()/IP(src="192.168.1.1", dst="192.168.1.2")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="11:22:33:44:55:77")/IPv6(src="::11", dst="::22")/GRE()/IP(src="192.168.1.1", dst="192.168.1.2")/Raw('x'*64), iface=intf)


Expected: p1 hash value is not equal to p2 or p3. p1 hash value is equal to p4 and p5.


Send a series packets to check if DCF RSS is correct for tunnelling packet (inner IPv6) ::

    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IPv6(src="::22", dst="::11")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IPv6(src="::22", dst="::12")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IPv6(src="::21", dst="::11")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="11:22:33:44:55:77")/IP(src="1.1.1.2", dst="2.2.2.1")/GRE()/IPv6(src="::22", dst="::11")/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="11:22:33:44:55:77")/IPv6(src="::33", dst="::44")/GRE()/IPv6(src="::22", dst="::11")/Raw('x'*64), iface=intf)

Expected: p1 hash value is not equal to p2 or p3. p1 hash value is equal to p4 and p5.


Test Case: Check default rss for L4
===================================

DCF data path support RSS packets by default. For L3 packets, input set is IP src/dst.
For tunneling packets, input set is inner IP src/dst.

Execute **common steps** to prepare DCF test environment

Set rxonly forward mode ::

    set fwd rxonly
    set verbose 1
    start

Send a series packets to check if DCF RSS is correct for IPv4 ::

    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=1235, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=1234, dport=5679)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:22:33:44:55:77")/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)

Expected: p1 hash value is not equal to p2 or p3 or p4 or p5, and should be equal to p6.

Send a series packets to check if DCF RSS is correct for IPv6 ::

    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IPv6(src="::22", dst="::11")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IPv6(src="::22", dst="::12")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IPv6(src="::21", dst="::11")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IPv6(src="::22", dst="::11")/UDP(sport=1235, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IPv6(src="::22", dst="::11")/UDP(sport=1234, dport=5679)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="11:22:33:44:55:77")/IPv6(src="::22", dst="::11")/TCP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)

Expected: p1 hash value is not equal to p2 or p3 or p4 or p5, and should be equal to p6.

Send a series packets to check if DCF RSS is correct for tunnelling packet (inner IPv4) ::

    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=1235, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=1234, dport=5679)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:22:33:44:55:77")/IP(src="1.1.1.2", dst="2.2.2.1")/GRE()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:22:33:44:55:77")/IPv6(src="::11", dst="::22")/GRE()/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)

Expected: p1 hash value is not equal to p2 or p3 or p4 or p5, and should be equal to p6 and p7.


Send a series packets to check if DCF RSS is correct for tunnelling packet (inner IPv6) ::

    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IPv6(src="::22", dst="::11")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IPv6(src="::22", dst="::12")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IPv6(src="::21", dst="::11")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IPv6(src="::22", dst="::11")/UDP(sport=1235, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:11:22:33:44:55")/IP(src="1.1.1.1", dst="2.2.2.2")/GRE()/IPv6(src="::22", dst="::11")/UDP(sport=1234, dport=5679)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:22:33:44:55:77")/IP(src="1.1.1.2", dst="2.2.2.1")/GRE()/IPv6(src="::22", dst="::11")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)
    sendp(Ether(dst="D2:6B:4C:EB:1C:26", src="00:22:33:44:55:77")/IPv6(src="::33", dst="::44")/GRE()/IPv6(src="::22", dst="::11")/UDP(sport=1234, dport=5678)/Raw('x'*64), iface=intf)

Expected: p1 hash value is not equal to p2 or p3 or p4 or p5, and should be equal to p6 and p7.


Test Case: Create rule with to original VF action
=================================================

DCF data path support RSS packets by default. For L3 packets, input set is IP src/dst.
For tunneling packets, input set is inner IP src/dst.

Execute **common steps** to prepare DCF test environment

Set rxonly forward mode ::

    set fwd rxonly
    set verbose 1
    start

Send a packet, check the DCF can't recieve the packet (Dest mac address is not DCF's mac) ::
    
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/("X"*480)], iface=intf, count=1)

Create a rule to DCF ::

    flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions vf original 1 / end

Send the packet again, check DCF can recieve the packet ::

    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/("X"*480)], iface=intf, count=1)

Destory the rule on DCF ::

    flow destroy 0 rule 0

Send the packet agiain, check DCF can't recieve the packet ::

    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/("X"*480)], iface=intf, count=1)


Test Case: Measure performance of DCF interface
===============================================

The steps are same to iAVF performance test, a slight difference on 
launching testpmd devarg. DCF need cap=dcf option.
Expect the performance is same to iAVF