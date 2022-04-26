.. SPDX-License-Identifier: BSD-3-Clause
   Copyright 2022 Intel Corporation

==========================
L3fwd Functional test plan
==========================

Description
===========

The L3fwd application is a simple example of packet processing using
DPDK to demonstrate usage of poll and event mode packet I/O mechanism.
The application performs L3 forwarding. For more, please consult
`Data Plane Development Kit L3 Forwarding Sample Application
<https://doc.dpdk.org/guides/sample_app_ug/l3_forward.html>`_.

Prerequisites
=============
Topology
--------
It requires at least 1 port connected traffic generator::

	Port0 --- TG0

2 ports is better::

	Port0 --- TG0
	Port1 --- TG1


Hardware
--------
This suite focus on l3fwd application, so any standard Ethernet Network Adapter is qualified.

Software
--------
* dpdk l3fwd application
* scapy to send packets from traffic generator, which is usually another Ethernet Network Adapter.

General Set Up
--------------
Here assume that 0000:18:00.0 and 0000:18:00.1 are DUT ports, and ens785f0 and ens785f1 are tester interfaces.

#. Build DPDK and l3fwd application::

   <dpdk dir># meson -Dexamples=l3fwd <dpdk build dir>
   <dpdk dir># ninja -C <dpdk build dir>

#. Get the DUT ports and tester interfaces::

    <dpdk dir># ./usertools/dpdk-devbind.py -s
    0000:18:00.0 'Ethernet Controller E810-C for QSFP 1592' if=ens785f0 drv=ice unused=vfio-pci
    0000:18:00.1 'Ethernet Controller E810-C for QSFP 1592' if=ens785f1 drv=ice unused=vfio-pci

#. Bind the DUT ports to vfio-pci::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:00.0 0000:18:00.1
    0000:18:00.0 'Ethernet Controller E810-C for QSFP 1592' drv=vfio-pci unused=ice
    0000:18:00.1 'Ethernet Controller E810-C for QSFP 1592' drv=vfio-pci unused=ice


Test Case
=========

The l3fwd application has a number of command line options, here list the key options will be tested::

    ./dpdk-l3fwd [EAL options] -- -p PORTMASK
                             --rule_ipv4=FILE
                             --rule_ipv6=FILE
                             [-P]
                             [--lookup LOOKUP_METHOD]
                             --config(port,queue,lcore)[,(port,queue,lcore)]
                             [--rx-queue-size NPKTS]
                             [--tx-queue-size NPKTS]
                             ...

Go through every options is not efficiency, therefore 3 combinations are created to make sure every key options are tested.

.. table::

   +-------------+--------------------+-------------+--------------+-------------+---------------+
   | Port number | Rx queues per port | Rule source | Lookup       | Promise     | Queue size    |
   +=============+====================+=============+==============+=============+===============+
   |     1       |   1                | default     | default(lpm) | default(on) | default(1024) |
   +-------------+--------------------+-------------+--------------+-------------+---------------+
   |     1       |   4                | file        | em           |     enable  | 2048          |
   +-------------+--------------------+-------------+--------------+-------------+---------------+
   |     2       |   4                | file        | em           |     enable  | 2048          |
   +-------------+--------------------+-------------+--------------+-------------+---------------+

The table shows:

* No. 1 covers most default options with least port, it only requires 1 port.
* No. 2 covers the other situations against to default, it also requires 1 port.
* No. 3 is almost same as No.2 except it requires 2 ports.

.. note::

    * If there is only 1 port, choose test case 1 and 2 to test.
    * If there are 2 ports, choose test case 1 and 3 to test.

Packet pattern:

* IPv4::

	[Ether(dst="<dtsmac>", src="<srcmac>")/IP(src="1.2.3.4",dst="<match>")/Raw("x"*80)]

* IPv6::

	[Ether(dst="<dtsmac>", src="<srcmac>")/IPv6(src="fe80::b696:91ff:fe9f:64b9",dst="<match>")/Raw("x"*80)]

.. note::

	20 packets with increased src_ip are used in every examination.


Test Case 1: 1 port 1 queue with default setting
------------------------------------------------

#. Launch l3fwd::

   ./<build_dir>/examples/dpdk-l3fwd -l <lcore> -n 4 -- -p 0x1 --config="(0,0,<lcore>)"
   ./build/examples/dpdk-l3fwd -l 1 -n 4 -- -p 0x1 --config="(0,0,1)" --eth-dest=0,b4:96:91:9f:64:b9

   Here list some output logs which helps you understand l3fwd.

   *  The DUT port is 0000:18:00.0::

         EAL: Probe PCI driver: net_ice (8086:1592) device: 0000:18:00.0 (socket 0)

   *  The lookup method is lpm and use default table. DUT mac address is 40:A6:B7:7B:3F:00, the egress packets dst mac is 02:00:00:00:00:00::

         Neither LPM, EM, or FIB selected, defaulting to LPM
         L3FWD: Missing 1 or more rule files, using default instead

   *  Every port creates 1 rx queue and 1 tx queue::

         Creating queues: nb_rxq=1 nb_txq=1
         Address:40:A6:B7:7B:3F:00, Destination:02:00:00:00:00:00

   *  Route rules::

         LPM: Adding route 198.18.0.0 / 24 (0) [0000:18:00.0]
         LPM: Adding route 2001:200:: / 64 (0) [0000:18:00.0]

   *  RX PATH "AVX2 OFFLOAD Vector Rx" is used::

         ice_set_rx_function(): Using AVX2 OFFLOAD Vector Rx (port 0)

   *  lcore 1 is used to polling port 0 rx queue 0::

         L3FWD:  -- lcoreid=1 portid=0 rxqueueid=0

   *  Link status, Packets sending to DUT have to wait port `link up`::

         Port 0 Link up at 100 Gbps FDX Autoneg

#. run tcpdump to capture packets on tester interface::

    tcpdump -i <TG interface> -vvv -Q in -e
    tcpdump -i ens2f0 -vvv -Q in -e

#. TG send both 20 ipv4 and ipv6 packets which match the route table::

   >>> sendp([Ether(dst="<matched mac>", src="<src mac>")/IP(src="<src ip>",dst="<198.168.0.x>")/Raw("x"*80)], iface="<tester tx port interface>")
   >>> sendp([Ether(dst="<matched mac>", src="<src mac>")/IPv6(src="<src ip>",dst="<2001:200::x>")/Raw("x"*80)], iface="<tester tx port interface>")

   >>> sendp([Ether(dst="40:A6:B7:7B:3F:00", src="b4:96:91:9f:64:b9")/IP(src="1.2.3.4",dst="198.168.0.1")/Raw("x"*80)], iface="ens2f0")
   >>> sendp([Ether(dst="40:A6:B7:7B:3F:00", src="b4:96:91:9f:64:b9")/IPv6(src="fe80::b696:91ff:fe9f:64b9",dst="2001:200::")/Raw("x"*80)], iface="ens2f0")

#. Check if the packets forwarded to TG, get the packets informartion from tcpdump output::

    07:44:32.770005 40:a6:b7:7b:3f:00 (oui Unknown) > 02:00:00:00:00:00 (oui Unknown), ethertype IPv4 (0x0800), length 114: (tos 0x0, ttl 63, id 1, offset 0, flags [none], proto Options (0), length 100)
        1.2.3.4 > 198.168.0.1:  hopopt 80
    07:53:08.206002 40:a6:b7:7b:3f:00 (oui Unknown) > 02:00:00:00:00:00 (oui Unknown), ethertype IPv6 (0x86dd), length 134: (hlim 64, next-header unknown (59) payload length: 80) test > 2001:200::: no next header

   `Pass Criteria`: Both the IPv4 and IPv6 packets are matched with the the transmitted packets.

Test Case 2: 1 port 4 queue with non-default setting
----------------------------------------------------

#. Launch l3fwd::

   ./<build_dir>/examples/dpdk-l3fwd -l <lcore0,lcore1> -n 4 -- -p 0x1 --config="(0,0,<lcore0>),(0,1,<lcore0>),(0,2,<lcore1>),(0,3,<lcore1>)" -P --rule_ipv4="./examples/l3fwd/em_default_v4.cfg" --rule_ipv6="./examples/l3fwd/em_default_v6.cfg" --lookup=em --rx-queue-size=2048 --tx-queue-size=2048
   ./build/examples/dpdk-l3fwd -l 1,2 -n 4 -- -p 0x1 --config="(0,0,1),(0,1,1),(0,2,2),(0,3,2)" -P --rule_ipv4="./examples/l3fwd/em_default_v4.cfg" --rule_ipv6="./examples/l3fwd/em_default_v6.cfg" --lookup=em --rx-queue-size=2048 --tx-queue-size=2048 --parse-ptype

   "--parse-ptype" is optional, add it if DUT do not support to parse RTE_PTYPE_L3_IPV4_EXT and RTE_PTYPE_L3_IPV6_EXT.

   *  Route rules::

         EM: Adding route 198.18.0.0, 198.18.0.1, 9, 9, 17 (0) [0000:18:00.0]

#. run tcpdump to capture packets on tester interface::

    tcpdump -i <TG interface> -vvv -Q in -e
    tcpdump -i ens2f0 -vvv -Q in -e

#. TG send both ipv4 and ipv6 packets which match the route table and distributed to all queues::

   >>> sendp([Ether(dst="<unmatched mac>", src="<src mac>")/IP(src="<src ip>",dst="<198.168.0.x>")/Raw("x"*80)], iface="<tester tx port interface>")
   >>> sendp([Ether(dst="<unmatched mac>", src="<src mac>")/IPv6(src="<src ip>",dst="<match table>")/Raw("x"*80)], iface="<tester tx port interface>")

#. Check if the packets forwarded to TG, get the packets informartion from tcpdump output::

    07:44:32.770005 40:a6:b7:7b:3f:00 (oui Unknown) > 02:00:00:00:00:00 (oui Unknown), ethertype IPv4 (0x0800), length 114: (tos 0x0, ttl 63, id 1, offset 0, flags [none], proto Options (0), length 100)
        1.2.3.4 > 198.168.0.1:  hopopt 80
    07:53:08.206002 40:a6:b7:7b:3f:00 (oui Unknown) > 02:00:00:00:00:00 (oui Unknown), ethertype IPv6 (0x86dd), length 134: (hlim 64, next-header unknown (59) payload length: 80) test > 2001:200::: no next header

   `Pass Criteria`: Both the IPv4 and IPv6 packets are matched with the the transmitted packets.


Test Case 3: 2 ports 4 queues with non-default setting
------------------------------------------------------

#. Launch l3fwd::

    ./<build_dir>/examples/dpdk-l3fwd -l <lcore0,lcore1> -n 4 -- -p 0x3 --config="(0,0,<lcore0>),(0,1,<lcore0>),(0,2,<lcore1>, ,(0,3,<lcore1>),(1,0,<lcore0>),(1,1,<lcore0>),(1,2,<lcore1>, ,(1,3,<lcore1>)" -P --rule_ipv4="rule_ipv4.cfg" --rule_ipv6="rule_ipv6.cfg" --lookup=em --rx-queue-size=2048 --tx-queue-size=2048

#. run tcpdump to capture packets on tester interfaces::

    tcpdump -i <tester tx Port0 interface> -vvv -Q in -e
    tcpdump -i <tester tx Port1 interface> -vvv -Q in -e

#. All TG 2 ports send both ipv4 and ipv6 packets which match the route table and distributed to all queues::

   >>> sendp([Ether(dst="<unmatched mac>", src="<src mac>")/IP(src="<src ip>",dst="<198.168.0.x>")/Raw("x"*80)], iface="<tester tx Port0 interface>")
   >>> sendp([Ether(dst="<unmatched mac>", src="<src mac>")/IPv6(src="<src ip>",dst="<match table>")/Raw("x"*80)], iface="<tester tx port0 interface>")
   >>> sendp([Ether(dst="<unmatched mac>", src="<src mac>")/IP(src="<src ip>",dst="<198.168.0.x>")/Raw("x"*80)], iface="<tester tx Port1 interface>")
   >>> sendp([Ether(dst="<unmatched mac>", src="<src mac>")/IPv6(src="<src ip>",dst="<match table>")/Raw("x"*80)], iface="<tester tx port1 interface>")

#. Check if the packets forwarded to TG, run tcpdump to capture packets on tester interface::

    07:44:32.770005 40:a6:b7:7b:3f:00 (oui Unknown) > 02:00:00:00:00:00 (oui Unknown), ethertype IPv4 (0x0800), length 114: (tos 0x0, ttl 63, id 1, offset 0, flags [none], proto Options (0), length 100)
        1.2.3.4 > 198.168.0.1:  hopopt 80
    07:53:08.206002 40:a6:b7:7b:3f:00 (oui Unknown) > 02:00:00:00:00:00 (oui Unknown), ethertype IPv6 (0x86dd), length 134: (hlim 64, next-header unknown (59) payload length: 80) test > 2001:200::: no next header

   `Pass Criteria`: Both the IPv4 and IPv6 packets are matched with the the transmitted packets.
