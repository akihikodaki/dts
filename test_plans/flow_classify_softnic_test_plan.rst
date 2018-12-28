.. Copyright (c) < 2017 >, Intel Corporation
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

===================================
Flow classification for softnic PMD
===================================

Description
===========
The SoftNIC allows building custom NIC pipelines in SW. The Soft NIC pipeline is configurable through firmware (DPDK Packet Framework script).

Prerequisites
=============
The DUT must have four 10G Ethernet ports connected to four ports on tester that are controlled by the Scapy packet generator::

    dut_port_0 <---> tester_port_0
    dut_port_1 <---> tester_port_1
    dut_port_2 <---> tester_port_2
    dut_port_3 <---> tester_port_3

Assume four DUT 10G Ethernet ports' pci device id is as the following::

    dut_port_0 : "0000:05:00.0"
    dut_port_1 : "0000:05:00.1"
    dut_port_2 : "0000:05:00.2"
    dut_port_3 : "0000:05:00.3"

Bind them to dpdk igb_uio driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0 05:00.1 05:00.2 05:00.3

Change ./drivers/net/softnic/firmware.cli to meet the specific test environment.

Start softnic with following command line::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25 -n 4 \
    --vdev 'net_softnic0,firmware=./drivers/net/softnic/firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --portmask=0x10
    testpmd> start

Start softnic with default hierarchy Qos with following command line::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25 -n 4 \
    --vdev 'net_softnic0,firmware=./drivers/net/softnic/firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --portmask=0x10
    testpmd> set port tm hierarchy default 1
    testpmd> start

Test Case: ipv4 ACL table
=========================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below::

    table action profile AP0 ipv4 offset 270 fwd
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25  -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv4_acl_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=4 --txq=4 --disable-rss --portmask=0x10

3. Validate a rule::

    flow validate 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 0.0.0.0 \
    dst mask 255.192.0.0 src spec 0.0.0.0 dst spec 2.0.0.0 proto spec 17 / udp src mask \
    65535 dst mask 65535 src spec 100 dst spec 200 / end actions queue index 3 / end

4. Add rules to table::

    flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 0.0.0.0 \
    dst mask 255.192.0.0 src spec 0.0.0.0 dst spec 2.0.0.0 proto spec 17 / udp src mask \
    65535 dst mask 65535 src spec 100 dst spec 200 / end actions queue index 3 / end

    flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 0.0.0.0 \
    dst mask 255.192.0.0 src spec 0.0.0.0 dst spec 2.64.0.0 proto spec 6 / tcp src mask
    65535 dst mask 65535 src spec 100 dst spec 200 / end actions queue index 2 / end

    flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.192.0.0 \
    dst mask 0.0.0.0 src spec 2.128.0.0 dst spec 0.0.0.0 proto spec 132 / sctp src mask \
    65535 dst mask 65535 src spec 100 dst spec 200 / end actions queue index 1 / end

    flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 0.0.0.0 \
    dst mask 255.192.0.0 src spec 0.0.0.0 dst spec 4.0.0.0 proto spec 17 / udp src mask \
    65535 dst mask 65535 src spec 100 dst spec 200 / end actions queue index 0 / end
    testpmd> start

5. Sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='0.0.0.0', dst='2.0.0.0',proto=17)/UDP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='0.0.0.0', dst='2.64.0.0',proto=6)/TCP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='2.128.0.0', dst='0.0.0.0',proto=132)/SCTP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='0.0.0.0', dst='4.0.0.0',proto=17)/UDP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='0.0.0.0', dst='3.0.0.0',proto=17)/UDP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='0.0.0.0', dst='2.64.0.0',proto=17)/UDP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='2.128.0.0', dst='0.0.0.0',proto=132)/SCTP(sport=101, dport=200)/('X'*48), iface="enp131s0f3")

   The first 4 packets were forwarded to port3/2/1/0.
   The last 3 packets weren't forwarded.

6. Query the rule::

    testpmd> flow query 4 3 queue
    Cannot query action type 6 (QUEUE)

7. destroy and flush the rule::

    testpmd> flow list 4
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => QUEUE
    1       0       0       i--     ETH IPV4 TCP => QUEUE
    2       0       0       i--     ETH IPV4 SCTP => QUEUE
    3       0       0       i--     ETH IPV4 UDP => QUEUE

    testpmd> flow destroy 4 rule 1
    Flow rule #1 destroyed
    testpmd> flow list 4
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => QUEUE
    2       0       0       i--     ETH IPV4 SCTP => QUEUE
    3       0       0       i--     ETH IPV4 UDP => QUEUE

8. Send packets, pkt1 to port3, pkt2 can't be forwarded, pkt3 to port1, pkt4 to port0::

    testpmd> flow flush 4
    testpmd> flow list 4

   No rule listed.
   Send the first 4 packets, none of them was forwarded.

9. Shutdown the port, the rules will be flushed.
   Re-add the four rules, then start forward.
   The first 4 packets can be forwarded to port3/2/1/0.
   Then::

    testpmd> stop
    testpmd> port stop 4
    testpmd> port start 4
    testpmd> start

   Send the first 4 packets, none of them was forwarded.

Notes: The IPv4 header source address mask must be set from high bits to low bits.
255.255.192.0 is legal.
255.192.255.0 is illegal.

Test Case: ipv4-5tuple hash table
=================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below::

    table action profile AP0 ipv4 offset 270 fwd
    pipeline RX table match hash ext key 16 mask 00FF0000FFFFFFFFFFFFFFFFFFFFFFFF \
    offset 278 buckets 16K size 64K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25  -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv4_5tuple_hash_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=4 --txq=4 --disable-rss --portmask=0x10

3. Add rules to table::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 100.0.0.1 dst spec 200.0.0.1 proto spec 6 / udp src mask \
    65535 dst mask 65535 src spec 101 dst spec 201 / end actions queue index 3 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 100.0.0.2 dst spec 200.0.0.2 proto spec 17 / udp src mask \
    65535 dst mask 65535 src spec 102 dst spec 202 / end actions queue index 2 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 100.0.0.3 dst spec 200.0.0.3 proto spec 132 / udp src mask \
    65535 dst mask 65535 src spec 103 dst spec 203 / end actions queue index 1 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 100.0.0.4 dst spec 200.0.0.4 proto spec 17 / udp src mask \
    65535 dst mask 65535 src spec 104 dst spec 204 / end actions queue index 0 / end

    testpmd> start

4. Sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.1', dst='200.0.0.1',proto=6)/TCP(sport=101, dport=201)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.2', dst='200.0.0.2',proto=17)/UDP(sport=102, dport=202)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.3', dst='200.0.0.3',proto=132)/SCTP(sport=103, dport=203)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.4', dst='200.0.0.4',proto=17)/UDP(sport=104, dport=204)/('X'*48), iface="enp131s0f3")

   The first 4 packets were forwarded to port3/2/1/0.
   Change any parameter of the 5 tuple, the packet can't forwarded to any port.

Test Case: ipv4-addr hash table
===============================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below::

    table action profile AP0 ipv4 offset 270 fwd

a) Match ipv4 src_addr::

    pipeline RX table match hash ext key 8 mask FFFFFFFF00000000 offset 282 buckets 16K size 64K action AP0

b) Match ipv4 dst_addr::

    pipeline RX table match hash ext key 8 mask FFFFFF0000000000 offset 286 buckets 16K size 64K action AP0

c) Match UDP SPORT::

    pipeline RX table match hash ext key 8 mask FFFF000000000000 offset 290 buckets 16K size 64K action AP0

    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25  -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv4_addr_hash_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=4 --txq=4 --disable-rss --portmask=0x10

3. Add rules to table.

a) Match the table a::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask \
    255.255.255.255 dst mask 0.0.0.0 src spec 100.0.0.1 dst spec 200.0.0.1 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions queue index 3 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask \
    255.255.255.255 dst mask 0.0.0.0 src spec 100.0.0.2 dst spec 200.0.0.1 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions queue index 2 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask \
    255.255.255.255 dst mask 0.0.0.0 src spec 100.0.0.3 dst spec 200.0.0.1 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions queue index 1 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask \
    255.255.255.255 dst mask 0.0.0.0 src spec 100.0.0.4 dst spec 200.0.0.1 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions queue index 0 / end

b) Match the table b::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 \
    dst mask 255.255.255.0 src spec 100.0.0.1 dst spec 200.0.0.1 proto spec 17 / udp src mask 0 \
    dst mask 0 src spec 100 dst spec 200 / end actions queue index 3 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 \
    dst mask 255.255.255.0 src spec 100.0.0.1 dst spec 200.0.1.1 proto spec 6 / tcp src mask 0 \
    dst mask 0 src spec 100 dst spec 200 / end actions queue index 2 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 \
    dst mask 255.255.255.0 src spec 100.0.0.1 dst spec 200.0.2.1 proto spec 132 / sctp src mask 0 \
    dst mask 0 src spec 100 dst spec 200 / end actions queue index 1 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 \
    dst mask 255.255.255.0 src spec 100.0.0.1 dst spec 200.0.3.1 / end actions queue index 0 / end

c) Match the table c::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 \
    dst mask 0.0.0.0 src spec 100.0.0.1 dst spec 200.0.0.1 proto spec 17 / udp src mask 65535 \
    dst mask 0 src spec 100 dst spec 200 / end actions queue index 3 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 \
    dst mask 0.0.0.0 src spec 100.0.0.1 dst spec 200.0.0.1 proto spec 6 / tcp src mask 65535 \
    dst mask 0 src spec 101 dst spec 200 / end actions queue index 2 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 \
    dst mask 0.0.0.0 src spec 100.0.0.1 dst spec 200.0.0.1 proto spec 132 / sctp src mask 65535 \
    dst mask 0 src spec 102 dst spec 200 / end actions queue index 1 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 \
    dst mask 0.0.0.0 src spec 100.0.0.1 dst spec 200.0.0.1 proto spec 17 / udp src mask 65535 \
    dst mask 0 src spec 103 dst spec 200 / end actions queue index 0 / end

    testpmd> start

   Notes: The added rule must be consistent with the match table format defined in firmware.cli

4. Sent packet, verify the packets were forwarded to the expected ports.

a) Match ipv4 src_addr::

    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.1', dst='200.0.0.1',proto=6)/TCP(sport=101, dport=201)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.2', dst='200.0.0.2',proto=17)/UDP(sport=102, dport=202)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.3', dst='200.0.0.3',proto=132)/SCTP(sport=103, dport=203)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.4', dst='200.0.0.4')/('X'*48), iface="enp131s0f3")

   The 4 packets were forwarded to port3/2/1/0.
   Change the ipv4 src address, the packet can't forwarded to any port.

b) Match ipv4 dst_addr::

    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.1', dst='200.0.0.1',proto=6)/TCP(sport=101, dport=201)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.2', dst='200.0.1.2',proto=17)/UDP(sport=102, dport=202)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.3', dst='200.0.2.3',proto=132)/SCTP(sport=103, dport=203)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.4', dst='200.0.3.4')/('X'*48), iface="enp131s0f3")

   The 4 packets were forwarded to port3/2/1/0.
   Change the ipv4 first 6 bytes of dst address, the packet can't forwarded to any port.

c) Match sport::

    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.1', dst='200.0.0.1',proto=6)/TCP(sport=100, dport=201)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.2', dst='200.0.1.2',proto=17)/UDP(sport=101, dport=202)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.3', dst='200.0.2.3',proto=132)/SCTP(sport=102, dport=203)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.2', dst='200.0.1.2',proto=17)/UDP(sport=103, dport=202)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='100.0.0.4', dst='200.0.3.4')/('X'*48), iface="enp131s0f3")

   The first 4 packets were forwarded to port3/2/1/0.
   The last packet can't forwarded to any port.
   Change the udp/tcp/sctp sport, the packet can't forwarded to any port.

Test Case: ipv6 ACL table
=========================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below::

    table action profile AP0 ipv6 offset 270 fwd
    pipeline RX table match acl ipv6 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25  -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv6_acl_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=4 --txq=4 --disable-rss --portmask=0x10

3. Add rules to table::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 src \
    mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 \
    src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:5789 dst spec 0:0:0:0:0:0:0:0 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 3 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 src \
    mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 \
    src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:6789 dst spec 0:0:0:0:0:0:0:0 proto spec 6 \
    / tcp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 2 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 src \
    mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 \
    src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:7789 dst spec 0:0:0:0:0:0:0:0 proto spec 132 \
    / sctp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 1 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 src \
    mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 \
    src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:8789 dst spec 0:0:0:0:0:0:0:0 proto spec 17 \
    / udp src mask 65535 dst mask 0 src spec 101 dst spec 0 / end actions queue index 0 / end

    testpmd> start

4. Sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789", dst="2001::2",nh=17)/UDP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:6789", dst="2001::2",nh=6)/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:7789", dst="2001::2",nh=132)/SCTP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:8789", dst="2001::2",nh=17)/UDP(sport=101, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:9789", dst="2001::2",nh=17)/UDP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:8789", dst="2001::2",nh=17)/UDP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:6789", dst="2001::2",nh=17)/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")

   The first 4 packets were forwarded to port3/2/1/0.
   The last 3 packets weren't forwarded.

Test Case: ipv6-addr hash table
===============================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below::

    table action profile AP0 ipv6 offset 270 fwd

a) Match ipv6 src_addr::

    pipeline RX table match hash ext key 16 mask FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF offset 278 buckets 16K size 64K action AP0

b) Match ipv6 dst_addr::

    pipeline RX table match hash ext key 16 mask FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF offset 294 buckets 16K size 64K action AP0

    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25  -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv6_addr_hash_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=4 --txq=4 --disable-rss --portmask=0x10

3. Add rules to table.

a) Match ipv6 src_addr::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 \
    src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:5789 dst spec 0:0:0:0:0:0:0:0 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 3 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 \
    src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:6789 dst spec 0:0:0:0:0:0:0:0 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 2 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 \
    src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:7789 dst spec 0:0:0:0:0:0:0:0 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 1 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 \
    src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:8789 dst spec 0:0:0:0:0:0:0:0 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 0 / end

b) Match ipv6 dst_addr::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 \
    dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff src mask 0:0:0:0:0:0:0:0 \
    dst spec ABCD:EF01:2345:6789:ABCD:EF01:2345:5789 src spec 0:0:0:0:0:0:0:0 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 3 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 \
    dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff src mask 0:0:0:0:0:0:0:0 \
    dst spec ABCD:EF01:2345:6789:ABCD:EF01:2345:6789 src spec 0:0:0:0:0:0:0:0 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 2 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 \
    dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff src mask 0:0:0:0:0:0:0:0 \
    dst spec ABCD:EF01:2345:6789:ABCD:EF01:2345:7789 src spec 0:0:0:0:0:0:0:0 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 1 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 \
    dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff src mask 0:0:0:0:0:0:0:0 \
    dst spec ABCD:EF01:2345:6789:ABCD:EF01:2345:8789 src spec 0:0:0:0:0:0:0:0 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 0 / end

    testpmd> start

4. Sent packet, verify the packets were forwarded to the expected ports.

a) Match ipv6 src_addr::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789", dst="2001::2")/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:6789", dst="2001::2")/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:7789", dst="2001::2")/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:8789", dst="2001::2")/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:9789", dst="2001::2")/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")

b) Match ipv6 dst_addr::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::1", dst="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789")/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::1", dst="ABCD:EF01:2345:6789:ABCD:EF01:2345:6789")/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::1", dst="ABCD:EF01:2345:6789:ABCD:EF01:2345:7789")/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::1", dst="ABCD:EF01:2345:6789:ABCD:EF01:2345:8789")/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::1", dst="ABCD:EF01:2345:6789:ABCD:EF01:2345:9789")/TCP(sport=32, dport=33)/Raw('x'*48), iface="enp131s0f3")

   The first 4 packets were forwarded to port3/2/1/0.
   The last packet weren't be forwarded to any port.

Test Case: ipv6-5tuple hash table
=================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below::

    table action profile AP0 ipv6 offset 270 fwd
    pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25  -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv6_5tuple_hash_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=4 --txq=4 --disable-rss --portmask=0x10

3. Add rules to table::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 2001::1 dst spec 0::1 proto spec 17 / udp src mask 65535 dst mask 65535 src spec 31 dst spec 41 \
    / end actions queue index 3 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 2001::2 dst spec 0::2 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 32 dst spec 42
    / end actions queue index 2 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 2001::3 dst spec 0::3 proto spec 132 / sctp src mask 65535 dst mask 65535 src spec 33 dst spec 43 \
    / end actions queue index 1 / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 2001::4 dst spec 0::4 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 34 dst spec 44 \
    / end actions queue index 0 / end

    testpmd> start

4. Sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::1", dst="0::1")/UDP(sport=31, dport=41)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::2", dst="0::2")/TCP(sport=32, dport=42)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::3", dst="0::3",nh=132)/SCTP(sport=33, dport=43)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::4", dst="0::4")/TCP(sport=34, dport=44)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::1", dst="0::1")/TCP(sport=31, dport=41)/Raw('x'*48), iface="enp131s0f3")

   The first 4 packets were forwarded to port3/2/1/0.
   The last packet weren't be forwarded to any port.

Test Case: ipv4 rule item inconsistent with table match format
==============================================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below::

    table action profile AP0 ipv4 offset 270 fwd

a) Match ipv4 src_addr::

    pipeline RX table match hash ext key 8 mask FFFFFFFF00000000 offset 282 buckets 16K size 64K action AP0

b) Match ipv4 dst_addr::

    pipeline RX table match hash ext key 8 mask FFFFFF0000000000 offset 286 buckets 16K size 64K action AP0

   Map the flowapi to softnic table::

    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25  -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv4_addr_hash_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=4 --txq=4 --disable-rss --portmask=0x10

3. Add rules to table.

a) Map the table a::

    flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 \
    dst mask 255.255.255.255 src spec 100.0.0.1 dst spec 200.0.0.1 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions queue index 3 / end

   Error reported, rule item is inconsistent with the table match.
   Table with hask key mask for src addr, but the rule added is for dst addr.

b) Map the table b::

    flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 \
    dst mask 255.255.255.255 src spec 100.0.0.1 dst spec 200.0.0.1 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions queue index 3 / end

   Error reported, rule item is inconsistent with the table match.
   Table with hask key mask for dst addr 255.255.255.0, but the rule added is 255.255.255.255.

Test Case: ipv6 rule item inconsistent with table match format
==============================================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below::

    table action profile AP0 ipv6 offset 270 fwd

a) Match ipv6 5tuple::

    pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0
    flowapi map group 0 ingress pipeline RX table 0

b) Match ipv6 dst_addr::

    pipeline RX table match hash ext key 16 mask FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF offset 294 buckets 16K size 64K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25  -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv6_5tuple_hash_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=4 --txq=4 --disable-rss --portmask=0x10

3. Add rules to table.

a) Map the table a::

    flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 src mask \
    ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 2001::1 dst spec 0::1 proto spec 17 / udp src mask 0 dst mask 65535 \
    src spec 31 dst spec 41 / end actions queue index 3 / end

   Error reported, rule item is inconsistent with the table match.
   Table with hask key mask for 5 tuple, but the rule added mask udp src with 0.

b) Map the table b::

    flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 src mask \
    ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 src spec \
    ABCD:EF01:2345:6789:ABCD:EF01:2345:5789 dst spec 0:0:0:0:0:0:0:0 proto spec 17 \
    / udp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 3 / end

   Error reported, rule item is inconsistent with the table match.
   Table with hask key mask for dst addr, but the rule added is for src addr.

Test Case: ipv4 hash table rss action
=====================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below::

    table action profile AP0 ipv4 offset 270 fwd balance offset 278 mask 00FF0000FFFFFFFFFFFFFFFFFFFFFFFF outoffset 256

a) Table a::

    pipeline RX table match hash ext key 16 mask 00FF0000FFFFFFFFFFFFFFFFFFFFFFFF offset 278 buckets 16K size 64K action AP0

b) Table b::

    pipeline RX table match hash ext key 16 mask 00FF0000FFFFFF00FFFFFFFFFFFFFFFF offset 278 buckets 16K size 64K action AP0

c) Table c::

    pipeline RX table match hash ext key 8 mask FFFF0000FFFFFFFF offset 282 buckets 16K size 64K action AP0

   Map the flowapi to softnic table::

    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25 -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv4_rss_firmware.cli,cpu_id=1,conn_port=8086'
    -- -i --forward-mode=softnic --rxq=4 --txq=4 --disable-rss --portmask=0x10

3. Add rules to table.

a) Map the table a::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 1.10.11.0 dst spec 2.20.21.0 proto spec 6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions rss queues 3 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 1.10.11.1 dst spec 2.20.21.1 proto spec 17 / udp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions rss queues 2 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 1.10.11.2 dst spec 2.20.21.2 proto spec 132 / sctp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions rss queues 1 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 1.10.11.3 dst spec 2.20.21.3 proto spec 6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions rss queues 0 end / end

b) Map the table b::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.0 \
    dst mask 255.255.255.255 src spec 1.10.11.0 dst spec 2.20.21.0 proto spec 6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions rss queues 0 1 2 3 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.0 \
    dst mask 255.255.255.255 src spec 1.10.12.0 dst spec 2.20.21.0 proto spec 6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions rss queues 0 1 2 3 end / end

c) Map the table c::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 255.255.0.0 \
    dst mask  255.255.255.255 src spec 1.10.11.0 dst spec 2.20.21.0 proto spec 6 / tcp src mask 0 \
    dst mask 0 src spec 100 dst spec 200 / end actions rss queues 0 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 255.255.0.0 \
    dst mask  255.255.255.255 src spec 1.10.11.0 dst spec 2.20.21.1 proto spec 6 / tcp src mask 0 \
    dst mask 0 src spec 100 dst spec 200 / end actions rss queues 2 3 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 255.255.0.0 \
    dst mask  255.255.255.255 src spec 2.10.11.0 dst spec 2.20.21.1 proto spec 6 / tcp src mask 0 \
    dst mask 0 src spec 100 dst spec 200 / end actions rss queues 1 2 end / end

    testpmd> start

4. Sent packet, verify the packets were forwarded to the expected ports.

a) Match the table a::

    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="1.10.11.0", dst="2.20.21.0")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="1.10.11.1", dst="2.20.21.1")/UDP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="1.10.11.2", dst="2.20.21.2")/SCTP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="1.10.11.3", dst="2.20.21.3")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="1.10.11.3", dst="2.20.21.3")/TCP(sport=101, dport=200)/Raw('x'*48), iface="enp131s0f3")

   The first 4 packets were forwarded to port3/2/1/0.
   The last packet weren't be forwarded to any port.

b) Match the table b::

    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="1.10.11.0", dst="2.20.21.0")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")

   Set the src address from 1.10.11.0 to 1.10.11.255, and other parameters keep constant,
   The packets were distributed from port0 to port3 according to RSS table.::

    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="1.10.12.0", dst="2.20.21.0")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")

   Set the src address from 1.10.12.0 to 1.10.12.255, and other parameters keep constant,
   The packets were distributed from port0 to port3 according to RSS table.::

    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="1.10.13.0", dst="2.20.21.0")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")

   The packet was not be forwarded to any port.

c) Match the table c::

    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="1.10.11.0", dst="2.20.21.0")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")

   Set the IP src address from 1.10.0.0 to 1.10.255.255, the packet was forwarded to port0.::

    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="1.10.11.0", dst="2.20.21.1")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")

   Set the IP src address from 1.10.0.0 to 1.10.255.255, or set sport or dport to 0-65535, the packet was forwarded to port2 or port3.::

    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="2.10.11.0", dst="2.20.21.1")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")

   Set the IP src address from 1.10.0.0 to 1.10.255.255, or set sport or dport to 0-65535, the packet was forwarded to port1 or port2.::

    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="1.10.11.0", dst="2.20.21.2")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")

   The packet weren't be forwarded to any port.

Test Case: ipv6 hash table rss action
=====================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below::

    table action profile AP0 ipv6 offset 270 fwd balance offset 274 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 outoffset 256

a) Table a::

    pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0

b) Table b::

    pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFF0000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0

c) Table c::

    pipeline RX table match hash ext key 64 mask 00000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000FFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0

   Map the flowapi to softnic table::

    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 21-25 -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv6_rss_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=4 --txq=4 --disable-rss --portmask=0x10

3. Add rules to table,

a) Map the table a::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 2001::1 dst spec 0::1 proto spec 17 / udp src mask 65535 dst mask 65535 \
    src spec 31 dst spec 41 / end actions rss queues 3 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 2001::2 dst spec 0::2 proto spec 6 / tcp src mask 65535 dst mask 65535 \
    src spec 32 dst spec 42 / end actions rss queues 2 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 2001::3 dst spec 0::3 proto spec 132 / sctp src mask 65535 dst mask 65535 \
    src spec 33 dst spec 43 / end actions rss queues 1 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 2001::4 dst spec 0::4 proto spec 6 / tcp src mask 65535 dst mask 65535 \
    src spec 34 dst spec 44 / end actions rss queues 0 end / end

b) Map the table b::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:0 dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:0 dst spec 0::1 proto spec 17 / udp src mask 65535 \
    dst mask 65535 src spec 31 dst spec 41 / end actions rss queues 0 1 2 3 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:0 dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec ABCD:EF01:2345:6789:ABCD:EF01:2346:0 dst spec 0::1 proto spec 17 / udp src mask 65535 \
    dst mask 65535 src spec 31 dst spec 41 / end actions rss queues 0 1 2 3 end / end

c) Map the table c::

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:0 \
    src spec 2001::1 dst spec 1001::1 proto spec 17 / udp src mask 65535 dst mask 65535 \
    src spec 31 dst spec 41 / end actions rss queues 0 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:0 \
    src spec 2001::2 dst spec 1001::1 proto spec 6 / tcp src mask 65535 dst mask 65535 \
    src spec 32 dst spec 42 / end actions rss queues 2 3 end / end

    testpmd> flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:0 \
    src spec 2001::1 dst spec 2001::3 proto spec 132 / sctp src mask 65535 dst mask 65535 \
    src spec 33 dst spec 43 / end actions rss queues 1 2 end / end

    testpmd> start

4. Sent packet, verify the packets were forwarded to the expected ports.

a) Match the table a::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::1", dst="0::1")/UDP(sport=31, dport=41)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::2", dst="0::2")/TCP(sport=32, dport=42)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::3", dst="0::3",nh=132)/SCTP(sport=33, dport=43)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::4", dst="0::4")/TCP(sport=34, dport=44)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::1", dst="0::1")/TCP(sport=31, dport=41)/Raw('x'*48), iface="enp131s0f3")

   The first 4 packets were forwarded to port3/2/1/0.
   The last packet weren't be forwarded to any port.

b) Match the table b::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:0", dst="0::1")/UDP(sport=31, dport=41)/Raw('x'*48), iface="enp131s0f3")

   Set the src address from ABCD:EF01:2345:6789:ABCD:EF01:2345:0 to ABCD:EF01:2345:6789:ABCD:EF01:2345:FFFF, and other parameters keep constant,
   The packets were distributed from port0 to port3 according to RSS table.::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2346:0", dst="0::1")/UDP(sport=31, dport=41)/Raw('x'*48), iface="enp131s0f3")

   Set the src address from ABCD:EF01:2345:6789:ABCD:EF01:2346:0 to ABCD:EF01:2345:6789:ABCD:EF01:2346:FFFF, and other parameters keep constant,
   The packets were distributed from port0 to port3 according to RSS table.::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2347:0", dst="0::1")/UDP(sport=31, dport=41)/Raw('x'*48), iface="enp131s0f3")

   The packet was not be forwarded to any port.

c) Match the table c::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::1", dst="1001::1")/TCP(sport=31, dport=41)/Raw('x'*48), iface="enp131s0f3")

   Set the IPv6 dst address from 1001::0 to 1001::FFFF, the packet was forwarded to port0.::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::2", dst="1001::2")/TCP(sport=32, dport=42)/Raw('x'*48), iface="enp131s0f3")

   Set the IPv6 dst address from 1001::0 to 1001::FFFF, the packet was forwarded to port2 or port3.::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::1", dst="2001::3")/TCP(sport=33, dport=43)/Raw('x'*48), iface="enp131s0f3")

   Set the IPv6 dst address from 2001::0 to 2001::FFFF, the packet was forwarded to port1 or port2.::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::1", dst="0::1")/TCP(sport=31, dport=41)/Raw('x'*48), iface="enp131s0f3")

   The packet weren't be forwarded to any port.

Test Case: ipv4 ACL table jump action
=====================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below,
   Just two links::

    link LINK0 dev 0000:05:00.0
    link LINK1 dev 0000:05:00.1

    table action profile AP0 ipv4 offset 270 fwd
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0
    flowapi map group 1 ingress pipeline RX table 1

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-25 -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv4_acl_jump_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=2 --txq=2 --disable-rss --portmask=0x4

3. Add rules to table::

    testpmd> create 2 group 1 ingress pattern eth / ipv4 proto mask 255 src mask 0.0.0.0 \
    dst mask 255.192.0.0 src spec 0.0.0.0 dst spec 2.0.0.0 proto spec 6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions queue index 0 / end

    testpmd> create 2 group 1 ingress pattern eth / ipv4 proto mask 255 src mask 0.0.0.0 \
    dst mask 255.192.0.0 src spec 0.0.0.0 dst spec 2.64.0.0 proto spec 6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions queue index  1 / end

    testpmd> create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 0.0.0.0 \
    dst mask 255.192.0.0 src spec 0.0.0.0 dst spec 2.0.0.0 proto spec 6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions jump group 1 / end

    testpmd> create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 0.0.0.0 \
    dst mask 255.192.0.0 src spec 0.0.0.0 dst spec 2.64.0.0 proto spec 6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions jump group 1 / end

4. Sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="0.0.0.0", dst="2.0.0.0")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IP(src="0.0.0.0", dst="2.64.0.0")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")

   The first packet was forwarded to port 0, the second was forwarded to port 1.
   If change the TCP sport or dport, the packet can't be forwarded to any port.

Notes: When only set the group 1 rules, the input packets match table 0, which map group 0, while there is no group 0 rule created.
So the packets can't be forwarded.

Test Case: ipv4 HASH table jump action
======================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below,
   Just two links::

    link LINK0 dev 0000:05:00.0
    link LINK1 dev 0000:05:00.1

    table action profile AP0 ipv4 offset 270 fwd
    pipeline RX table match hash ext key 16 mask 00FF0000FFFFFFFFFFFFFFFF00000000 offset 278 buckets 16K size 64K action AP0
    pipeline RX table match hash ext key 16 mask 00FF0000FFFFFFFFFFFFFFFF00000000 offset 278 buckets 16K size 64K action AP0
    pipeline RX port in 0 table 0
    pipeline RX port in 1 table 0
    flowapi map group 0 ingress pipeline RX table 0
    flowapi map group 1 ingress pipeline RX table 1

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-25 -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv4_hash_jump_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=2 --txq=2 --disable-rss --portmask=0x4

3. Add rules to table::

    testpmd> flow create 2 group 1 ingress pattern eth / ipv4 proto mask 255 \
    src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.0 dst spec 2.20.21.0 proto spec 6 \
    / tcp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions queue index 0 / end

    testpmd> flow create 2 group 1 ingress pattern eth / ipv4 proto mask 255 \
    src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.1 dst spec 2.20.21.1 proto spec 6 \
    / tcp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions queue index 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 \
    src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.0 dst spec 2.20.21.0 proto spec 6 \
    / tcp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions jump group 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 \
    src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.1 dst spec 2.20.21.1 proto spec 6 \
    / tcp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions jump group 1 / end

4. Sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='1.10.11.0', dst='2.20.21.0',proto=6)/TCP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='1.10.11.1', dst='2.20.21.1',proto=6)/TCP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")

   The first packet was forwarded to port 0, the second was forwarded to port 1.
   If change the IPv4 dst address or src address, the packet can't be forwarded to any port.

Notes: when only set the group 1 rules, the input packets match table 0, which map group 0, while there is no group 0 rule created.
So the packets can't be forwarded.

Test Case: ipv4 ACL jump to HASH table
======================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below,
   Just two links::

    link LINK0 dev 0000:05:00.0
    link LINK1 dev 0000:05:00.1

   Group 0 with ACL table jump to group 1 with HASH table::

    table action profile AP0 ipv4 offset 270 fwd
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    pipeline RX table match hash ext key 16 mask 00FF0000FFFFFFFFFFFFFFFFFFFFFFFF offset 278 buckets 16K size 64K action AP0
    pipeline RX port in 0 table 0
    pipeline RX port in 1 table 0
    flowapi map group 0 ingress pipeline RX table 0
    flowapi map group 1 ingress pipeline RX table 1

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-25 -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv4_acl_hash_jump_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=2 --txq=2 --disable-rss --portmask=0x4

3. Add rules to table::

    testpmd> flow create 2 group 1 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 1.10.11.0 dst spec 2.20.21.0 proto spec 6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions queue index 0 / end

    testpmd> flow create 2 group 1 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 1.10.11.1 dst spec 2.20.21.1 proto spec 6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions queue index 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 1.10.11.0 dst spec 2.20.21.0 proto spec  6 / tcp src mask 0 \
    dst mask 0 src spec 100 dst spec 200 / end actions jump group 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 1.10.11.1 dst spec 2.20.21.1 proto spec  6 / tcp src mask 0 \
    dst mask 0 src spec 100 dst spec 200 / end actions jump group 1 / end

4. Sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='1.10.11.0', dst='2.20.21.0',proto=6)/TCP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='1.10.11.1', dst='2.20.21.1',proto=6)/TCP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")

   The first packet was forwarded to port 0, the second was forwarded to port 1.
   If change the IPv4 dst address or src address, the packet can't be forwarded to any port::

    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='1.10.11.0', dst='2.20.21.0',proto=6)/TCP(sport=101, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='1.10.11.1', dst='2.20.21.1',proto=6)/TCP(sport=100, dport=201)/('X'*48), iface="enp131s0f3")

   The two packets can't be forwarded to any port.

Test Case: ipv4 HASH jump to ACL table
======================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below,
   Just two links::

    link LINK0 dev 0000:05:00.0
    link LINK1 dev 0000:05:00.1

   Group 0 with ACL table jump to group 1 with HASH table::

    table action profile AP0 ipv4 offset 270 fwd
    pipeline RX table match hash ext key 16 mask 00FF0000FFFFFFFFFFFFFF00FFFFFFFF offset 278 buckets 16K size 64K action AP0
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    pipeline RX port in 0 table 0
    pipeline RX port in 1 table 0
    flowapi map group 0 ingress pipeline RX table 0
    flowapi map group 1 ingress pipeline RX table 1

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-25 -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv4_hash_acl_jump_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=2 --txq=2 --disable-rss --portmask=0x4

3. Add rules to table::

    testpmd> flow create 2 group 1 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 1.10.11.0 dst spec 2.20.21.0 proto spec 6 / tcp src mask 0 \
    dst mask 0 src spec 100 dst spec 200 / end actions queue index 0 / end

    testpmd> flow create 2 group 1 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.255 src spec 1.10.11.1 dst spec 2.20.21.1 proto spec 6 / tcp src mask 0 \
    dst mask 0 src spec 100 dst spec 200 / end actions queue index 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.0 src spec 1.10.11.0 dst spec 2.20.21.0 proto spec  6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions jump group 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 \
    dst mask 255.255.255.0 src spec 1.10.11.1 dst spec 2.20.21.1 proto spec  6 / tcp src mask 65535 \
    dst mask 65535 src spec 100 dst spec 200 / end actions jump group 1 / end

4. Sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='1.10.11.0', dst='2.20.21.0',proto=6)/TCP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='1.10.11.1', dst='2.20.21.1',proto=6)/TCP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='1.10.11.0', dst='2.20.21.2',proto=6)/TCP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")
    sendp(Ether(dst='00:00:00:00:01:00')/IP(src='1.10.11.1', dst='2.20.21.3',proto=6)/TCP(sport=100, dport=200)/('X'*48), iface="enp131s0f3")

   The first packet was forwarded to port 0, the second was forwarded to port 1.
   The last two packets can't be forwarded to any ports.

Test Case: ipv6 ACL table jump action
=====================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below,
   Just two links::

    link LINK0 dev 0000:05:00.0
    link LINK1 dev 0000:05:00.1

    table action profile AP0 ipv6 offset 270 fwd
    pipeline RX table match acl ipv6 offset 270 size 4K action AP0
    pipeline RX table match acl ipv6 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0
    flowapi map group 1 ingress pipeline RX table 1

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-25 -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv6_acl_jump_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=2 --txq=2 --disable-rss --portmask=0x4

3. Add rules to table::

    testpmd> flow create 2 group 1 ingress pattern eth / ipv6 proto mask 255 src mask 0:0:0:0:0:0:0:0 \
    dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff src spec 0::1 dst spec 2001::1 proto spec 6 \
    / tcp src mask 65535 dst mask 65535 src spec 100 dst spec 200 / end actions queue index 0 / end

    testpmd> flow create 2 group 1 ingress pattern eth / ipv6 proto mask 255 src mask \
    ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 0::1 dst spec 2001::2 proto spec 6 / tcp src mask 65535 dst mask 65535 \
    src spec 100 dst spec 200 / end actions queue index 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv6 proto mask 255 src mask 0:0:0:0:0:0:0:0 \
    dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff src spec 0::1 dst spec 2001::1 proto spec 6 \
    / tcp src mask 65535 dst mask 65535 src spec 100 dst spec 200 / end actions jump group 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv6 proto mask 255 src mask 0:0:0:0:0:0:0:0 \
    dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff src spec 0::1 dst spec 2001::2 proto spec 6 \
    / tcp src mask 65535 dst mask 65535 src spec 100 dst spec 200 / end actions jump group 1 / end

4. Sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::1", dst="2001::1")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::1", dst="2001::2")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::2", dst="2001::1")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::2", dst="2001::2")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")

   The first packet was forwarded to port 0, the second was forwarded to port 1.
   The third packet was forwarded to port 0, the fourth packet can't be forwarded to any port.

Notes: When only set the group 1 rules, the input packets match table 0, which map group 0, while there is no group 0 rule created.
So the packets can't be forwarded.

Test Case: ipv6 HASH table jump action
======================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below,
   Just two links::

    link LINK0 dev 0000:05:00.0
    link LINK1 dev 0000:05:00.1

    table action profile AP0 ipv6 offset 270 fwd
    pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0
    pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0
    pipeline RX port in 0 table 0
    pipeline RX port in 1 table 0
    flowapi map group 0 ingress pipeline RX table 0
    flowapi map group 1 ingress pipeline RX table 1

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-25 -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv6_hash_jump_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=2 --txq=2 --disable-rss --portmask=0x4

3. Add rules to table::

    testpmd> flow create 2 group 1 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 0::1 dst spec 2001::1 proto spec 6 / tcp src mask 65535 dst mask 65535 \
    src spec 100 dst spec 200 / end actions queue index 0 / end

    testpmd> flow create 2 group 1 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 0::2 dst spec 2001::2 proto spec 17 / udp src mask 65535 dst mask 65535 \
    src spec 100 dst spec 200 / end actions queue index 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 0::1 dst spec 2001::1 proto spec 6 / tcp src mask 65535 dst mask 65535 \
    src spec 100 dst spec 200 / end actions jump group 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 0::2 dst spec 2001::2 proto spec 17 / udp src mask 65535 dst mask 65535 \
    src spec 100 dst spec 200 / end actions jump group 1 / end

4. Sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::1", dst="2001::1")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::2", dst="2001::2")/UDP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")

   The first packet was forwarded to port 0, the second was forwarded to port 1.
   If change the IPv6 dst address or src address, the packet can't be forwarded to any port.

Notes: When only set the group 1 rules, the input packets match table 0, which map group 0, while there is no group 0 rule created.
So the packets can't be forwarded.

Test Case: ipv6 ACL jump to HASH table
======================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below,
   Just two links::

    link LINK0 dev 0000:05:00.0
    link LINK1 dev 0000:05:00.1

   Group 0 with ACL table jump to group 1 with HASH table::

    table action profile AP0 ipv6 offset 270 fwd
    pipeline RX table match acl ipv6 offset 270 size 4K action AP0
    pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0
    pipeline RX port in 0 table 0
    pipeline RX port in 1 table 0
    flowapi map group 0 ingress pipeline RX table 0
    flowapi map group 1 ingress pipeline RX table 1

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-25 -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv6_acl_hash_jump_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=2 --txq=2 --disable-rss --portmask=0x4

3. Add rules to table::

    testpmd> flow create 2 group 1 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 0::1 dst spec 2001::1 proto spec 6 / tcp src mask 65535 dst mask 65535 \
    src spec 100 dst spec 200 / end actions queue index 0 / end

    testpmd> flow create 2 group 1 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 0::2 dst spec 2001::2 proto spec 6 / tcp src mask 65535 dst mask 65535 \
    src spec 100 dst spec 200 / end actions queue index 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask 0:0:0:0:0:0:0:0 dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff src spec 0::1 \
    dst spec 2001::1 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 100 dst spec 200 / end actions jump group 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask 0:0:0:0:0:0:0:0 dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff src spec 0::2 dst spec 2001::2 proto spec 6 \
    / tcp src mask 65535 dst mask 65535 src spec 100 dst spec 200 / end actions jump group 1 / end

4. sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::1", dst="2001::1")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::2", dst="2001::2")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::3", dst="2001::1")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::4", dst="2001::2")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")

   The first packet was forwarded to port 0, the second was forwarded to port 1.
   The last two packets can't be forwarded to any ports.

Test Case: ipv6 HASH jump to ACL table
======================================
1. Edit flow_classification_firmware.cli to change "table action" and "pipeline table" as below,
   Just two links::

    link LINK0 dev 0000:05:00.0
    link LINK1 dev 0000:05:00.1

   Group 0 with ACL table jump to group 1 with HASH table::

    table action profile AP0 ipv6 offset 270 fwd
    pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0
    pipeline RX table match acl ipv6 offset 270 size 4K action AP0
    pipeline RX port in 0 table 0
    pipeline RX port in 1 table 0
    flowapi map group 0 ingress pipeline RX table 0
    flowapi map group 1 ingress pipeline RX table 1

2. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-25 -n 4 --vdev 'net_softnic0, \
    firmware=./drivers/net/softnic/flow_ipv6_hash_acl_jump_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --rxq=2 --txq=2 --disable-rss --portmask=0x4

3. Add rules to table::

    testpmd> flow create 2 group 1 ingress pattern eth / ipv6 proto mask 255 src mask 0:0:0:0:0:0:0:0 \
    dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff src spec 0::1 dst spec 2001::1 proto spec 6 \
    / tcp src mask 65535 dst mask 65535 src spec 100 dst spec 200 / end actions queue index 0 / end

    testpmd> flow create 2 group 1 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 0::2 dst spec 2001::2 proto spec 6 / tcp src mask 0 dst mask 65535 src spec 100 dst spec 200 / end actions queue index 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 0::1 dst spec 2001::1 proto spec 6 / tcp src mask 65535 dst mask 0 src spec 100 dst spec 200 / end actions jump group 1 / end

    testpmd> flow create 2 group 0 ingress pattern eth / ipv6 proto mask 255 \
    src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff \
    src spec 0::2 dst spec 2001::2 proto spec 6 / tcp src mask 65535 dst mask 0 src spec 100 dst spec 200 / end actions jump group 1 / end

4. Sent packet, verify the packets were forwarded to the expected ports::

    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::1", dst="2001::1")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::2", dst="2001::2")/TCP(sport=100, dport=200)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::1", dst="2001::1")/TCP(sport=100, dport=201)/Raw('x'*48), iface="enp131s0f3")
    sendp(Ether(dst="00:00:00:00:01:00")/IPv6(src="0::2", dst="2001::2")/TCP(sport=100, dport=202)/Raw('x'*48), iface="enp131s0f3")

   The first packet was forwarded to port 0, the second was forwarded to port 1.
   The last two packets can't be forwarded to any ports.
