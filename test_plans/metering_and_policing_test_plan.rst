.. Copyright (c) <2015-2018>, Intel Corporation
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

=====================
metering and policing
=====================

Description
-----------
The SoftNIC allows building custom NIC pipelines in SW. The Soft NIC pipeline
is configurable through firmware (DPDK Packet Framework script).

In RFC2698, the behavior of the Meter is specified as below:
When a packet of size B bytes arrives at time t, the following
happens if the trTCM is configured to operate:

* in the Color-Blind mode:

  * If Tp(t)-B < 0, the packet is red, else
  * If Tc(t)-B < 0, the packet is yellow and Tp is decremented by B, else
  * The packet is green and both Tp and Tc are decremented by B.

* in the Color-Aware mode:

  * If the packet has been precolored as red or if Tp(t)-B < 0, the packet is red, else
  * If the packet has been precolored as yellow or if Tc(t)-B < 0, the packet is yellow and Tp is decremented by B, else
  * The packet is green and both Tp and Tc are decremented by B.

DPDK meter library (librte_meter) implements these two mode separately
and made through different APIs. In table meter action implementation,
always color aware mode API is invoked regardless of dscp table.

Prerequisites
-------------
The DUT must have four 10G Ethernet ports connected to four ports on
Tester that are controlled by the Scapy packet generator,

  ::

    dut_port_0 <---> tester_port_0
    dut_port_1 <---> tester_port_1
    dut_port_2 <---> tester_port_2
    dut_port_3 <---> tester_port_3

Assume four DUT 10G Ethernet ports' pci device id is as the following,

  ::

    dut_port_0 : "0000:05:00.0"
    dut_port_1 : "0000:05:00.1"
    dut_port_2 : "0000:05:00.2"
    dut_port_3 : "0000:05:00.3"

Bind them to dpdk igb_uio driver,

  ::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0 05:00.1

1. change ./drivers/net/softnic/firmware.cli to meet the specific test environment.

  ::

    link LINK0 dev 0000:05:00.0
    link LINK1 dev 0000:05:00.1
    link LINK2 dev 0000:05:00.2
    link LINK3 dev 0000:05:00.3

    pipeline RX period 10 offset_port_id 0
    pipeline RX port in bsz 32 link LINK0 rxq 0
    pipeline RX port in bsz 32 link LINK1 rxq 0
    pipeline RX port in bsz 32 link LINK2 rxq 0
    pipeline RX port in bsz 32 link LINK3 rxq 0
    pipeline RX port out bsz 32 swq RXQ0
    pipeline RX port out bsz 32 swq RXQ1
    pipeline RX port out bsz 32 swq RXQ2
    pipeline RX port out bsz 32 swq RXQ3

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    ;pipeline RX table 0 dscp /root/dpdk/drivers/net/softnic/dscp_yellow.sh
    pipeline RX port in 0 table 0
    pipeline RX port in 1 table 0
    pipeline RX port in 2 table 0
    pipeline RX port in 3 table 0
    flowapi map group 0 ingress pipeline RX table 0

    pipeline TX period 10 offset_port_id 0
    pipeline TX port in bsz 32 swq TXQ0
    pipeline TX port in bsz 32 swq TXQ1
    pipeline TX port in bsz 32 swq TXQ2
    pipeline TX port in bsz 32 swq TXQ3
    pipeline TX port out bsz 32 link LINK0 txq 0
    pipeline TX port out bsz 32 link LINK1 txq 0
    pipeline TX port out bsz 32 link LINK2 txq 0
    pipeline TX port out bsz 32 link LINK3 txq 0
    pipeline TX table match stub
    pipeline TX table match stub
    pipeline TX table match stub
    pipeline TX table match stub

    pipeline TX port in 0 table 0
    pipeline TX port in 1 table 1
    pipeline TX port in 2 table 2
    pipeline TX port in 3 table 3
    pipeline TX table 0 rule add match default action fwd port 0
    pipeline TX table 1 rule add match default action fwd port 1
    pipeline TX table 2 rule add match default action fwd port 2
    pipeline TX table 3 rule add match default action fwd port 3

    thread 4 pipeline RX enable
    thread 4 pipeline TX enable

2. start softnic with following command line,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x1f -s 0x10 -n 4 \
    --vdev 'net_softnic0,firmware=./drivers/net/softnic/firmware.cli' \
    -- -i --portmask=0x10 --disable-rss
    testpmd> start

3. start softnic with default hierarchy Qos with following command line,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x1f -s 0x10 -n 4 \
    --vdev 'net_softnic0,firmware=./drivers/net/softnic/firmware.cli' \
    -- -i --portmask=0x10 --disable-rss
    testpmd> set port tm hierarchy default 1
    testpmd> start

Test Case 1: ipv4 ACL table RFC2698 GYR
---------------------------------------
1. Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,

  ::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=2 --txq=2 --portmask=0x4 --disable-rss

  Add rules to table, set CBS to 400 bytes, PBS to 500 bytes

  ::

    testpmd> add port meter profile trtcm_rfc2698 2 0 3125000000 3125000000 400 500 0
    testpmd> add port meter policy 2 0 g_actions color type green / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 0 / queue index 0 / end
    testpmd> start

3. Configure the packets with specified src/dst IP address and TCP dport/sport.

  a. send a packet larger than PBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")

  The packet was forwarded to port 0.

  b. send a packet not larger than PBS but larger than CBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")

  The packet was forwarded to port 0.

  c. send a packet not larger than CBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  The packet was forwarded to port 0.

**Notes**: the CBS/PBS includes IP header(20 bytes) and TCP header(20 bytes).
So when the payload is 460 bytes, the IP packet is 500 bytes.


Test Case 2: ipv4 ACL table RFC2698 GYD
---------------------------------------
1. Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,

  ::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=2 --txq=2 --portmask=0x4 --disable-rss

  Add rules to table, set CBS to 400 bytes, PBS to 500 bytes
  ::

    testpmd> add port meter profile trtcm_rfc2698 2 0 3125000000 3125000000 400 500 0
    testpmd> add port meter policy 2 0 g_actions color type green / end y_actions color type yellow / end r_actions drop / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 0 / queue index 0 / end
    testpmd> start

3. Configure the packets with specified src/dst IP address and TCP dport/sport.

  a. send a packet larger than PBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")

  The packet was dropped.

  b. send a packet not larger than PBS but larger than CBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")

  The packet was forwarded to port 0.


  c. send a packet not larger than CBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  The packet was forwarded to port 0.

Test Case 3: ipv4 ACL table RFC2698 GDR
---------------------------------------
1. Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,

 ::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=2 --txq=2 --portmask=0x4 --disable-rss

  Add rules to table, set CBS to 400 bytes, PBS to 500 bytes
  ::

    testpmd> add port meter profile trtcm_rfc2698 2 0 3125000000 3125000000 400 500 0
    testpmd> add port meter policy 2 0 g_actions color type green / end y_actions drop / end r_actions color type red / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 132 / sctp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 0 / queue index 1 / end
    testpmd> start

3. Configure the packets with specified src/dst IP address and SCTP dport/sport.

  a. send a packet larger than PBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=132)/SCTP(sport=2,dport=2)/Raw(load="P"*469)], iface="enp131s0f3")

  The packet was forwarded to port 1.

  b. send a packet not larger than PBS but larger than CBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=132)/SCTP(sport=2,dport=2)/Raw(load="P"*468)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=132)/SCTP(sport=2,dport=2)/Raw(load="P"*369)], iface="enp131s0f3")

  The packets was dropped.

  c. send a packet not larger than CBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=132)/SCTP(sport=2,dport=2)/Raw(load="P"*368)], iface="enp131s0f3")

  The packet was forwarded to port 1.

**Notes**: the CBS/PBS includes IP header(20 bytes) and SCTP header(12 bytes).
So when the payload is 468 bytes, the IP packet is 500 bytes.

Test Case 4: ipv4 ACL table RFC2698 DYR
---------------------------------------
1. Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,

  ::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=2 --txq=2 --portmask=0x4 --disable-rss

  Add rules to table, set CBS to 400 bytes, PBS to 500 bytes
  ::

    testpmd> add port meter profile trtcm_rfc2698 2 0 3125000000 3125000000 400 500 0
    testpmd> add port meter policy 2 0 g_actions drop / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 17 / udp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 0 / queue index 0 / end
    testpmd> start

3. Configure the packets with specified src/dst IP address and TCP dport/sport.

  a. send a packet larger than PBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=17)/UDP(sport=2,dport=2)/Raw(load="P"*473)], iface="enp131s0f3")

  The packet was forwarded to port 0.

  b. send a packet not larger than PBS but larger than CBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=17)/UDP(sport=2,dport=2)/Raw(load="P"*373)], iface="enp131s0f3")

  The packet was forwarded to port 0.

  c. send a packet not larger than CBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=17)/UDP(sport=2,dport=2)/Raw(load="P"*372)], iface="enp131s0f3")

  The packet was dropped.

**Notes**: the CBS/PBS includes IP header(20 bytes) and UDP header(8 bytes).
So when the payload is 472 bytes, the IP packet is 500 bytes.

Test Case 5: ipv4 ACL table RFC2698 DDD
---------------------------------------
1. Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,

  ::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=2 --txq=2 --portmask=0x4 --disable-rss

  Add rules to table, set CBS to 400 bytes, PBS to 500 bytes
  ::

    testpmd> add port meter profile trtcm_rfc2698 2 0 3125000000 3125000000 400 500 0
    testpmd> add port meter policy 2 0 g_actions drop / end y_actions drop / end r_actions drop / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 0 / queue index 0 / end
    testpmd> start

3. Configure the packets with specified src/dst IP address and TCP dport/sport.

  a. send a packet larger than PBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")

  The packet was dropped.

  b. send a packet not larger than PBS but larger than CBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")

  The packet was dropped.

  c. send a packet not larger than CBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  The packet was dropped.

Test Case 6: ipv4 with same CBS and PBS GDR
-------------------------------------------
1. Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,

  ::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=2 --txq=2 --portmask=0x4 --disable-rss

  Add rules to table, set CBS to 400 bytes, PBS to 500 bytes
  ::

    testpmd> add port meter profile trtcm_rfc2698 2 0 3125000000 3125000000 500 500 0
    testpmd> add port meter policy 2 0 g_actions color type green / end y_actions drop / end r_actions color type red / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 0 / queue index 0 / end
    testpmd> start

3. Configure the packets with specified src/dst IP address and TCP dport/sport.

  a. send a packet larger than PBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")

  The packet was forwarded to port 0.

  b. send a packet not larger than PBS
  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")

  The packet was forwarded to port 0.

Test Case 7: ipv4 HASH table RFC2698
------------------------------------
1. Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,

  ::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match hash ext key 16 mask 00FF0000FFFFFFFFFFFFFFFFFFFFFFFF offset 278 buckets 16K size 65K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=2 --txq=2 --portmask=0x4 --disable-rss

  Add rules to table,
  ::

    testpmd> add port meter profile trtcm_rfc2698 2 0 3125000000 3125000000 400 500 0
    a)GYR
    testpmd> add port meter policy 2 0 g_actions color type green / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    b)GYD
    testpmd> add port meter policy 2 0 g_actions color type green / end y_actions color type yellow / end r_actions drop / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    c)GDR
    testpmd> add port meter policy 2 0 g_actions color type green / end y_actions drop / end r_actions color type red / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    d)DYR
    testpmd> add port meter policy 2 0 g_actions drop / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    e)DDD
    testpmd> add port meter policy 2 0 g_actions drop / end y_actions drop / end r_actions drop / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 0 / queue index 0 / end
    testpmd> start

3. Configure the packets with specified src/dst IP address and TCP dport/sport. Send packets same as ACL table, there will be the same result with ACL table.

Test Case 8: ipv6 ACL table RFC2698
-----------------------------------
1. Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,

  ::

    table action profile AP0 ipv6 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv6 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=2 --txq=2 --portmask=0x4 --disable-rss

  Add rules to table,
  ::

    testpmd> add port meter profile trtcm_rfc2698 2 0 3125000000 3125000000 400 500 0
    testpmd> add port meter policy 2 0 g_actions color type green / end y_actions color type yellow / end r_actions drop / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    testpmd> add port meter policy 2 1 g_actions drop / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 2 1 0 1 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv6 proto mask 255 src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:5789 dst spec 0:0:0:0:0:0:0:0 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 0 / queue index 0 / end
    testpmd> flow create 2 group 0 ingress pattern eth / ipv6 proto mask 255 src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:5789 dst spec 0:0:0:0:0:0:0:0 proto spec 17 / udp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 1 / queue index 1 / end
    testpmd> start
    testpmd> flow list 2
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV6 TCP => METER QUEUE
    1       0       0       i--     ETH IPV6 UDP => METER QUEUE

3. Configure the packets with specified src/dst IPv6 address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789",dst="2001::1",nh=6)/TCP(sport=2,dport=2)/Raw(load="P"*441)], iface="enp131s0f3")
    The packet was dropped.
    sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789",dst="2001::1",nh=6)/TCP(sport=2,dport=2)/Raw(load="P"*440)], iface="enp131s0f3")
    The packet was forwarded to port 0.
    sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789",dst="2001::1",nh=6)/TCP(sport=2,dport=2)/Raw(load="P"*340)], iface="enp131s0f3")
    The packet was forwarded to port 0.
    sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789",dst="2001::1",nh=17)/UDP(sport=2,dport=2)/Raw(load="P"*453)], iface="enp131s0f3")
    The packet was forwarded to port 1.
    sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789",dst="2001::1",nh=17)/UDP(sport=2,dport=2)/Raw(load="P"*353)], iface="enp131s0f3")
    The packet was forwarded to port 1.
    sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789",dst="2001::1",nh=17)/UDP(sport=2,dport=2)/Raw(load="P"*352)], iface="enp131s0f3")
    The packet was dropped.

**Notes**: TCP header covers 20 bytes, UDP header covers 8 bytes.
The CBS/PBS includes IPv6 header(40 bytes) and TCP/UDP header(20/8 bytes).
So when the payload of IPv6-TCP packet is 440 bytes, the IPv6 packet is 500 bytes.
When the payload of IPv6-UDP packet is 452 bytes, the IPv6 packet is 500 bytes.

Test Case 9: multiple meter and profile
---------------------------------------
1. Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,

  ::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic, configure 4 ports,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x1f -s 0x10 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=4 --txq=4 --portmask=0x10 --disable-rss

  Add rules to table, set CBS to 400 bytes, PBS to 500 bytes
  ::

    testpmd> add port meter profile trtcm_rfc2698 4 0 3125000000 3125000000 400 500 0
    testpmd> add port meter profile trtcm_rfc2698 4 1 3125000000 3125000000 300 400 0
    testpmd> add port meter policy 4 0 g_actions color type green / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 4 0 0 0 yes 0 0 0
    testpmd> add port meter policy 4 1 g_actions color type green / end y_actions color type yellow / end r_actions drop / end
    testpmd> create port meter 4 1 0 1 yes 0 0 0
    testpmd> add port meter policy 4 2 g_actions color type green / end y_actions drop / end r_actions color type red / end
    testpmd> create port meter 4 2 0 2 yes 0 0 0
    testpmd> add port meter policy 4 3 g_actions drop / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 4 3 0 3 yes 0 0 0
    testpmd> add port meter policy 4 4 g_actions color type green / end y_actions color type yellow / end r_actions drop / end
    testpmd> create port meter 4 4 1 4 yes 0 0 0
    testpmd> add port meter policy 4 5 g_actions color type green / end y_actions drop / end r_actions color type red / end
    testpmd> create port meter 4 5 1 5 yes 0 0 0
    testpmd> add port meter policy 4 6 g_actions drop / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 4 6 1 6 yes 0 0 0
    testpmd> add port meter policy 4 7 g_actions drop / end y_actions drop / end r_actions drop / end
    testpmd> create port meter 4 7 1 7 yes 0 0 0
    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 0 dst spec 0 / end actions meter mtr_id 0 / queue index 0 / end
    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 1 dst spec 1 / end actions meter mtr_id 1 / queue index 1 / end
    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 2 / queue index 2 / end
    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 3 dst spec 3 / end actions meter mtr_id 3 / queue index 3 / end
    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 4 dst spec 4 / end actions meter mtr_id 4 / queue index 0 / end
    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 5 dst spec 5 / end actions meter mtr_id 5 / queue index 1 / end
    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 6 dst spec 6 / end actions meter mtr_id 6 / queue index 2 / end
    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 7 dst spec 7 / end actions meter mtr_id 128 / queue index 3 / end
    testpmd> flow create 4 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 8 dst spec 8 / end actions meter mtr_id 128 / queue index 0 / end
    the last flow can't be created successfully with "METER: Meter already attached to a flow: Invalid argument"
    testpmd> start
    testpmd> flow list 4
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 TCP => METER QUEUE
    1       0       0       i--     ETH IPV4 TCP => METER QUEUE
    2       0       0       i--     ETH IPV4 TCP => METER QUEUE
    3       0       0       i--     ETH IPV4 TCP => METER QUEUE
    4       0       0       i--     ETH IPV4 TCP => METER QUEUE
    5       0       0       i--     ETH IPV4 TCP => METER QUEUE
    6       0       0       i--     ETH IPV4 TCP => METER QUEUE
    7       0       0       i--     ETH IPV4 TCP => METER QUEUE

3. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    pkt1: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=0,dport=0)/Raw(load="P"*461)], iface="enp131s0f3")
    pkt2: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=0,dport=0)/Raw(load="P"*460)], iface="enp131s0f3")
    pkt3: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=0,dport=0)/Raw(load="P"*360)], iface="enp131s0f3")
    pkt1/2/3 were forwarded to port 0
    pkt4: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=1,dport=1)/Raw(load="P"*461)], iface="enp131s0f3")
    pkt5: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=1,dport=1)/Raw(load="P"*460)], iface="enp131s0f3")
    pkt6: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=1,dport=1)/Raw(load="P"*360)], iface="enp131s0f3")
    pkt4 was dropped, pkt5/6 were forwarded to port1
    pkt7: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    pkt8: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    pkt9: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*361)], iface="enp131s0f3")
    pkt10: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")
    pkt8/9 were dropped, pkt7/10 were forwarded to port2
    pkt11: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=3,dport=3)/Raw(load="P"*461)], iface="enp131s0f3")
    pkt12: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=3,dport=3)/Raw(load="P"*361)], iface="enp131s0f3")
    pkt13: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=3,dport=3)/Raw(load="P"*360)], iface="enp131s0f3")
    pkt13 was dropped, pkt11/12 were forwarded to port3
    pkt14: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=4,dport=4)/Raw(load="P"*361)], iface="enp131s0f3")
    pkt15: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=4,dport=4)/Raw(load="P"*360)], iface="enp131s0f3")
    pkt16: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=4,dport=4)/Raw(load="P"*260)], iface="enp131s0f3")
    pkt14 was dropped, pkt15/16 were forwarded to port0
    pkt17: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=5,dport=5)/Raw(load="P"*361)], iface="enp131s0f3")
    pkt18: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=5,dport=5)/Raw(load="P"*360)], iface="enp131s0f3")
    pkt19: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=5,dport=5)/Raw(load="P"*261)], iface="enp131s0f3")
    pkt20: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=5,dport=5)/Raw(load="P"*260)], iface="enp131s0f3")
    pkt18/19 were dropped, pkt17/20 were forwarded to port1
    pkt21: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=6,dport=6)/Raw(load="P"*361)], iface="enp131s0f3")
    pkt22: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=6,dport=6)/Raw(load="P"*261)], iface="enp131s0f3")
    pkt23: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=6,dport=6)/Raw(load="P"*260)], iface="enp131s0f3")
    pkt23 was dropped, pkt21/22 were forwarded to port2
    pkt24: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=7,dport=7)/Raw(load="P"*361)], iface="enp131s0f3")
    pkt25: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=7,dport=7)/Raw(load="P"*261)], iface="enp131s0f3")
    pkt26: sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=7,dport=7)/Raw(load="P"*260)], iface="enp131s0f3")
    pkt24/25/26 were dropped

**Notes**: if create one flow with a mtr_id, then create the flow again with another mtr_id,
the last flow rule will overlap the previous one.
so the first flow rule will not take effect, just the last one can take effect.

Test Case 10: ipv4 RFC2698 pre-colored red by DSCP table
--------------------------------------------------------
1. Set the DSCP table in dscp.sh, set all the packets from every tc and every queue to red color. Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,

  ::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    pipeline RX table 0 dscp /root/dpdk/drivers/net/softnic/dscp_red.sh
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=2 --txq=2 --portmask=0x4 --disable-rss

  Add rules to table, set CBS to 400 bytes, PBS to 500 bytes
  ::

    testpmd> add port meter profile trtcm_rfc2698 2 0 3125000000 3125000000 400 500 0
    testpmd> add port meter policy 2 0 g_actions color type green / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 0 / queue index 0 / end
    testpmd> start

3. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  All the packets were forwarded to port 0.

4. Create another meter to drop all the packets with red color,

  ::

    testpmd> add port meter policy 2 1 g_actions color type green / end y_actions color type yellow / end r_actions drop / end
    testpmd> create port meter 2 1 0 1 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 1 / queue index 0 / end

5. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  All the packets were dropped.

6. Create another meter to drop all the packets with yellow color,

  ::

    testpmd> add port meter policy 2 2 g_actions color type green / end y_actions drop / end r_actions color type red / end
    testpmd> create port meter 2 2 0 2 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 2 / queue index 0 / end

7. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  All the packets were forwarded to port 0

8. Create another meter to drop all the packets with green color,

  ::

    testpmd> add port meter policy 2 3 g_actions drop / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 2 3 0 3 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 3 / queue index 0 / end

9. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  All the packets were forwarded to port 0

Test Case 11: ipv4 RFC2698 pre-colored yellow by DSCP table
-----------------------------------------------------------
1. Set the DSCP table in dscp.sh, set all the packets from every tc and every queue to yellow color.

  Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,
  ::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    pipeline RX table 0 dscp /root/dpdk/drivers/net/softnic/dscp_yellow.sh
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=2 --txq=2 --portmask=0x4 --disable-rss

  Add rules to table, set CBS to 400 bytes, PBS to 500 bytes
  ::

    testpmd> add port meter profile trtcm_rfc2698 2 0 3125000000 3125000000 400 500 0
    testpmd> add port meter policy 2 0 g_actions color type green / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 0 / queue index 0 / end
    testpmd> start

3. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  All the packets were forwarded to port 0.

4. Create another meter to drop all the packets with red color,

  ::

    testpmd> add port meter policy 2 1 g_actions color type green / end y_actions color type yellow / end r_actions drop / end
    testpmd> create port meter 2 1 0 1 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 1 / queue index 0 / end

5. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  pkt1 was dropped.
  pkt2 and pkt3 were forwarded to port 0.

6. Create another meter to drop all the packets with yellow color,

  ::

    testpmd> add port meter policy 2 2 g_actions color type green / end y_actions drop / end r_actions color type red / end
    testpmd> create port meter 2 2 0 2 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 2 / queue index 0 / end

7. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  pkt1 was forwarded to port 0.
  pkt2 and pkt3 were dropped.

8. Create another meter to drop all the packets with green color,

  ::

    testpmd> add port meter policy 2 3 g_actions drop / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 2 3 0 3 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 3 / queue index 0 / end

9. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  All the packets were forwarded to port 0

Test Case 12: ipv4 RFC2698 pre-colored green by DSCP table
----------------------------------------------------------
1. Set the DSCP table in dscp.sh, set all the packets from every tc and every queue to green color.

  Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,
  ::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    pipeline RX table 0 dscp /root/dpdk/drivers/net/softnic/dscp_green.sh
    flowapi map group 0 ingress pipeline RX table 0

2. Start softnic,

  ::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 --vdev 'net_softnic0,firmware=/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli' -- -i --rxq=2 --txq=2 --portmask=0x4 --disable-rss

  Add rules to table, set CBS to 400 bytes, PBS to 500 bytes
  ::

    testpmd> add port meter profile trtcm_rfc2698 2 0 3125000000 3125000000 400 500 0
    testpmd> add port meter policy 2 0 g_actions color type green / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 2 0 0 0 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 0 / queue index 0 / end
    testpmd> start

3. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  All the packets were forwarded to port 0.

4. Create another meter to drop all the packets with red color,

  ::

    testpmd> add port meter policy 2 1 g_actions color type green / end y_actions color type yellow / end r_actions drop / end
    testpmd> create port meter 2 1 0 1 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 1 / queue index 0 / end

5. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  pkt1 was dropped.
  pkt2 and pkt3 were forwarded to port 0.

6. Create another meter to drop all the packets with yellow color,

  ::

    testpmd> add port meter policy 2 2 g_actions color type green / end y_actions drop / end r_actions color type red / end
    testpmd> create port meter 2 2 0 2 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 2 / queue index 0 / end

7. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  pkt1 and pkt3 were forwarded to port 0.
  pkt2 was dropped.

8. Create another meter to drop all the packets with green color,

  ::

    testpmd> add port meter policy 2 3 g_actions drop / end y_actions color type yellow / end r_actions color type red / end
    testpmd> create port meter 2 3 0 3 yes 0 0 0
    testpmd> flow create 2 group 0 ingress pattern eth / ipv4 proto mask 255 src mask 255.255.255.255 dst mask 255.255.255.255 src spec 1.10.11.12 dst spec 2.20.21.22 proto spec 6 / tcp src mask 65535 dst mask 65535 src spec 2 dst spec 2 / end actions meter mtr_id 3 / queue index 0 / end

9. Configure the packets with specified src/dst IP address and TCP dport/sport.

  ::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*461)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*460)], iface="enp131s0f3")
    sendp([Ether(dst="00:00:00:00:01:00")/IP(src='1.10.11.12',dst='2.20.21.22',proto=6)/TCP(sport=2,dport=2)/Raw(load="P"*360)], iface="enp131s0f3")

  pkt1 and pkt2 were forwarded to port 0.
  pkt3 was dropped.

Test Case 13: ipv4 RFC2698 pre-colored by default DSCP table
------------------------------------------------------------
1. Set the DSCP table in dscp.sh,

  The default DSCP table translate all input packets dscp values (0...64) to 0 0 0
  which means traffic class 0, queue id 0 , color 0 (i.e green).

  Edit meter_and_policing_firmware.cli to change "table action" and "pipeline table" as below,::

    table action profile AP0 ipv4 offset 270 fwd meter trtcm tc 1 stats pkts
    pipeline RX table match acl ipv4 offset 270 size 4K action AP0
    pipeline RX table 0 dscp /root/dpdk/drivers/net/softnic/dscp_default.sh
    flowapi map group 0 ingress pipeline RX table 0

2. Execute the steps2-9 of the case pre-colored green by DSCP table, got the same result.
