.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

==========================
ICE PF Enable Buffer Split
==========================

Description
===========
Protocol based buffer split consists of splitting a received packet into two separate regions based on the packet content. 
It is useful in some scenarios, such as GPU acceleration. The splitting will help to enable true zero copy and hence 
improve the performance significantly.

It supports protocol split based on current buffer split. When Rx queue is 
configured with RTE_ETH_RX_OFFLOAD_BUFFER_SPLIT offload and corresponding protocol, 
packets received will be directly split into two different mempools with expected hdr and payload length/content.

For validation, we will focus on:
1. Configuration of protocol based buffer split is applied.
Setup buffer split:
Per port: testpmd>port config 0 rx_offload buffer_split on
Per queue: testpmd>port 0 rxq 0 rx_offload buffer_split on

Set the protocol type of buffer split:
testpmd>set rxhdrs (eth|ipv4|ipv6|ipv4-tcp|ipv6-tcp|ipv4-udp|ipv6-udp|
ipv4-sctp|ipv6-sctp|grenat|inner-eth|inner-ipv4|inner-ipv6|
inner-ipv4-tcp|inner-ipv6-tcp|inner-ipv4-udp|inner-ipv6-udp|
inner-ipv4-sctp|inner-ipv6-sctp)

2. Packets received in ice scalar path(--force-max-simd-bitwidth=64) can be devided into 
two mempools with expected hdr and payload length/content specified by protocol type.

.. note::

    Currently, it supports 6 kinds segmentation of buffer split:
    * Outer mac: set rxhdrs eth
    * Inner mac: set rxhdrs inner-eth
    * Inner l3: set rxhdrs ipv4|ipv6|inner-ipv4|inner-ipv6
    * Inner l4: set rxhdrs ipv4-udp|ipv4-tcp|ipv6-udp|ipv6-tcp|inner-ipv4-udp|inner-ipv4-tcp|inner-ipv6-udp|inner-ipv6-tcp
    * Inner sctp: set rxhdrs ipv4-sctp|ipv6-sctp|inner-ipv4-sctp|inner-ipv6-sctp
    * Tunnel: set rxhdrs grenat

Prerequisites
=============

Topology
--------
DUT port 0 <----> Tester port 0

Hardware
--------
Supported NICs: Intel® Ethernet 800 Series E810-XXVDA4/E810-CQ

Software
--------
dpdk: http://dpdk.org/git/dpdk
runtime command: https://doc.dpdk.org/guides/testpmd_app_ug/testpmd_funcs.html

General Set Up
--------------
1. Compile DPDK with '-Dc_args='-DRTE_ETHDEV_DEBUG_RX=1' to dump segment data::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dc_args='-DRTE_ETHDEV_DEBUG_RX=1' --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110

2. Get the pci device id and interface of DUT and tester.
   For example, 0000:3b:00.0 and 0000:3b:00.1 is pci device id,
   ens785f0 and ens785f1 is interface::

    <dpdk dir># ./usertools/dpdk-devbind.py -s

    0000:3b:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci
    0000:3b:00.1 'Device 159b' if=ens785f1 drv=ice unused=vfio-pci

3. Bind the DUT port to dpdk::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id> 

Test Case
=========
The test case verifies the buffer split of 6 packets:
* MAC_IPV4_UDP_PAY
* MAC_IPV4_IPV4_UDP_PAY
* MAC_IPV4_UDP_VXLAN_MAC_IPV4_UDP_PAY
* MAC_IPV4_UDP_VXLAN_IPV4_UDP_PAY
* MAC_IPV4_GRE_MAC_IPV4_UDP_PAY 
* MAC_IPV4_GRE_IPV4_UDP_PAY

Common Steps
------------
1.port stop all
2.port config 0 rx_offload buffer_split on 
3.show port 0 rx_offload configuration
4.port config 0 udp_tunnel_port add vxlan 4789
5.set rxhdrs eth
6.show config rxhdrs
7.port start all
8.start

Test Case 1: PORT_BUFFER_SPLIT_OUTER_MAC
----------------------------------------
Launch two ports testpmd, configure port 0 buffer split on outer mac, send matched packets to port 0 and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the outer mac.

Test Steps
~~~~~~~~~~
1. Launch two ports testpmd::
 
    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 -a 3b:00.1 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 

2. Execute common steps to configure port 0 buffer split on outer mac.

3. Send matched packets to port 0.
    
    Send MAC_IPV4_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=14 and pay_len=50.
    
    Send MAC_IPV4_IPV6_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/IPv6()/("Y"*30)], iface="ens260f0")
    
    Check the received packets can be devided into two mempools with hdr_len=14 and pay_len=90.

    Send MAC_IPV4_UDP_VXLAN_MAC_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with har_len=14 and pay_len=80.
   
    Send MAC_IPV6_UDP_VXLAN_IPV6_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/("Y"*30)], iface="ens260f0") 
      
    Check the received packets can be devided into two mempools with hdr_len=14 and pay_len=126.
   
    Send MAC_IPV4_GRE_MAC_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/("Y"*30)], iface="ens260f0")
 
    Check the received packets can be devided into two mempools with hdr_len=14 and pay_len=68.

    Send MAC_IPV4_GRE_IPV6_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/("Y"*30)], iface="ens260f0")
   
    Check the received packets can be devided into two mempools with hdr_len=14 and pay_len=94.

4. Send matched packets to port 1::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/IPv6()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/("Y"*30)], iface="ens260f1") 
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/("Y"*30)], iface="ens260f1")

   Check the received packets can't be devided into two mempools and the segment length should be empty.

Test Case 2: PORT_BUFFER_SPLIT_INNER_MAC
----------------------------------------
Launch two ports testpmd, configure port 0 buffer split on inner mac, send matched packets to port 0 and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the inner mac.

Test Steps
~~~~~~~~~~
1. Launch two ports testpmd::
 
    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 -a 3b:00.1 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 

2. Modify common step 5 to::
 
    set rxhdrs inner-eth

   Execute common steps to configure port 0 buffer split on inner mac.

3. Send matched packets to port 0.

    Send MAC_IPV4_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=14 and pay_len=50.
    
    Send MAC_IPV4_IPV6_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/IPv6()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=14 and pay_len=90.

    Send MAC_IPV4_UDP_VXLAN_MAC_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=64 and pay_len=30.
    
    Send MAC_IPV6_UDP_VXLAN_IPV6_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/("Y"*30)], iface="ens260f0")
   
    Check the received packets can be devided into two mempools with hdr_len=14 and pay_len=126.

    Send MAC_IPV4_GRE_MAC_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=52 and pay_len=30.

    Send MAC_IPV6_GRE_IPV6_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IPv6()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=14 and pay_len=114.

4. Send matched packets to port 1::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/IPv6()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/("Y"*30)], iface="ens260f1") 
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/("Y"*30)], iface="ens260f1")

   Check the received packets can't be devided into two mempools and the segment length should be empty.

Test Case 3: PORT_BUFFER_SPLIT_INNER_L3
---------------------------------------
Launch two ports testpmd, configure port 0 buffer split on inner l3, send matched packets to port 0 and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the inner l3.
Whether configure buffer split on ipv4 or ipv6, packets are split at inner ipv4 or inner ipv6.

Subcase 1: buffer split ipv4
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Steps
~~~~~~~~~~
1. Launch two ports testpmd::
 
    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 -a 3b:00.1 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 

2. Modify common step 5 to::
 
    set rxhdrs ipv4

   Execute common steps to configure port 0 buffer split on inner l3.

3. Send matched packets to port 0.
    
    Send MAC_IPV4_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)], iface="ens260f0")
    
    Check the received packets can be devided into two mempools with hdr_len=34 and pay_len=30.

    Send MAC_IPV6_IPV4_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/IP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=74 and pay_len=30.

    Send MAC_IPV4_UDP_VXLAN_MAC_IPV6_PAY packet::
      
      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IPv6()/("Y"*30)], iface="ens260f0")
    
    Check the received packets can be devided into two mempools with hdr_len=104 and pay_len=30.

    Send MAC_IPV6_UDP_VXLAN_IPV4_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IP()/("Y"*30)], iface="ens260f0")
    
    Check the received packets can be devided into two mempools with hdr_len=90 and pay_len=30.

    Send MAC_IPV4_GRE_MAC_IPV6_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IPv6()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=92 and pay_len=30.

    Send MAC_IPV6_GRE_IPV4_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=78 and pay_len=30.

4. Send matched packets to port 1::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/IP()/("Y"*30)], iface="ens260f1") 
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IPv6()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether()/IPv6()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/("Y"*30)], iface="ens260f1")    
 
   Check the received packets can't be devided into two mempools and the segment length should be empty.

Subcase 2: buffer split ipv6
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs ipv6

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner l3.

Subcase 3: buffer split inner-ipv4
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv4

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner l3.

Subcase 4: buffer split inner-ipv6
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv6

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner l3.

Test Case 4: PORT_BUFFER_SPLIT_INNER_L4
---------------------------------------
Launch two ports testpmd, configure port 0 buffer split on inner udp/tcp, send matched packets to port 0 and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the inner udp/tcp. 
Whether configure buffer split on udp or tcp, packets are split at inner udp or inner tcp.

Subcase 1: buffer split ipv4-udp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Steps
~~~~~~~~~~
1. Launch two ports testpmd::
 
    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 -a 3b:00.1 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 

2. Modify common step 5 to::
 
    set rxhdrs ipv4-udp

   Execute common steps to configure port 0 buffer split on inner udp/tcp.

3. Send matched packets to port 0.
   
    #UDP packets
    Send MAC_IPV4_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=42 and pay_len=30.
    
    Send MAC_IPV4_IPV6_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/IPv6()/UDP()/("Y"*30)], iface="ens260f0")
 
    Check the received packets can be devided into two mempools with hdr_len=82 and pay_len=30.

    Send MAC_IPV4_UDP_VXLAN_MAC_IPV4_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP()/UDP()/("Y"*30)], iface="ens260f0")
       
    Check the received packets can be devided into two mempools with hdr_len=92 and pay_len=30.

    Send MAC_IPV6_UDP_VXLAN_IPV6_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/UDP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=118 and pay_len=30.    

    Send MAC_IPV6_GRE_MAC_IPV4_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/UDP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=100 and pay_len=30.

    Send MAC_IPV4_GRE_IPV6_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP()/("Y"*30)], iface="ens260f0")    

    Check the received packets can be devided into two mempools with hdr_len=86 and pay_len=30.

    #TCP packets
    Send MAC_IPV6_TCP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/TCP()/("Y"*30)], iface="ens260f0")
 
    Check the received packets can be devided into two mempools with hdr_len=74 and pay_len=30.    

    Send MAC_IPV6_IPV4_TCP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/IP()/TCP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=94 and pay_len=30.
 
    Send MAC_IPV6_UDP_VXLAN_MAC_IPV6_TCP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IPv6()/TCP()/("Y"*30)], iface="ens260f0")
 
    Check the received packets can be devided into two mempools with hdr_len=144 and pay_len=30.

    Send MAC_IPV4_UDP_VXLAN_IPV4_TCP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN()/IP()/TCP()/("Y"*30)], iface="ens260f0")
 
    Check the received packets can be devided into two mempools with hdr_len=90 and pay_len=30.    

    Send MAC_IPV4_GRE_MAC_IPV6_TCP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IPv6()/TCP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=112 and pay_len=30.

    Send MAC_IPV6_GRE_IPV4_TCP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/TCP()/("Y"*30)], iface="ens260f0")
    
    Check the received packets can be devided into two mempools with hdr_len=98 and pay_len=30.

4. Send mismatched packet to port 0::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)], iface="ens260f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/SCTP()/("Y"*30)], iface="ens260f0")

   Check the received packets can't be devided into two mempools and hdr_len=0.

5. Send matched packets to port 1::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/IPv6()/UDP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP()/UDP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/UDP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/UDP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP()/("Y"*30)], iface="ens260f1")
    
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/TCP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/IP()/TCP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IPv6()/TCP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN()/IP()/TCP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/Ether(dst="00:11:22:33:44:66")/IPv6()/TCP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/TCP()/("Y"*30)], iface="ens260f1")

   Check the received packets can't be devided into two mempools and the segment length should be empty.

Subcase 2: buffer split ipv6-udp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs ipv6-udp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner udp/tcp.

Subcase 3: buffer split ipv4-tcp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs ipv4-tcp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner udp/tcp.

Subcase 4: buffer split ipv6-tcp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs ipv6-tcp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner udp/tcp.

Subcase 5: buffer split inner-ipv4-udp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv4-udp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner udp/tcp.

Subcase 6: buffer split inner-ipv6-udp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv6-udp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner udp/tcp.

Subcase 7: buffer split inner-ipv4-tcp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv4-tcp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner udp/tcp.

Subcase 8: buffer split inner-ipv6-tcp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv6-tcp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner udp/tcp.

Test Case 5: PORT_BUFFER_SPLIT_INNER_SCTP
-----------------------------------------
Launch two ports testpmd, configure port 0 buffer split on inner sctp, send matched packets to port 0 and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the inner sctp.

Subcase 1: buffer split ipv4-sctp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Steps
~~~~~~~~~~
1. Launch two ports testpmd::
 
    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 -a 3b:00.1 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 

2. Modify common step 5 to::
 
    set rxhdrs ipv4-sctp

   Execute common steps to configure port 0 buffer split on inner sctp.

3. Send matched packets to port 0.

    Send MAC_IPV4_SCTP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/SCTP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=46 and pay_len=30.
    
    Send MAC_IPV4_IPV6_SCTP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/IPv6()/SCTP()/("Y"*30)], iface="ens260f0")
 
    Check the received packets can be devided into two mempools with hdr_len=86 and pay_len=30.
 
    Send MAC_IPV4_UDP_VXLAN_MAC_IPV4_SCTP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP()/SCTP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=96 and pay_len=30.

    Send MAC_IPV6_UDP_VXLAN_IPV6_SCTP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/SCTP()/("Y"*30)], iface="ens260f0")
    
    Check the received packets can be devided into two mempools with hdr_len=122 and pay_len=30.

    Send MAC_IPV6_GRE_MAC_IPV4_SCTP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/SCTP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=104 and pay_len=30.

    Send MAC_IPV4_GRE_IPV6_SCTP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/SCTP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=90 and pay_len=30.
    
4. Send mismatched packet to port 0.
    
    Send MAC_IPV4_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)], iface="ens260f0")

    Check the received packets can't be devided into two mempools with hdr_len=0 and pay_len=64.
    
    Send MAC_IPV4_GRE_MAC_IPV4_UDP_PAY packet::
    
      sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/UDP()/("Y"*30)], iface="ens260f0")

    Check the received packets can't be devided into two mempools with hdr_len=0 and pay_len=110.

    Send MAC_IPV4_GRE_MAC_IPV4_TCP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/TCP()/("Y"*30)], iface="ens260f0")
    
    Check the received packets can't be devided into two mempools with hdr_len=0 and pay_len=122.

5. Send matched packets to port 1::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/SCTP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/IPv6()/SCTP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP()/SCTP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/SCTP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/SCTP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/SCTP()/("Y"*30)], iface="ens260f1")

   Check the received packets can't be devided into two mempools and the segment length should be empty.

Subcase 2: buffer split ipv6-sctp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs ipv6-sctp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner sctp.

Subcase 3: buffer split inner-ipv4-sctp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv4-sctp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner sctp.

Subcase 4: buffer split inner-ipv6-sctp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv6-sctp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner sctp.

Test Case 6: PORT_BUFFER_SPLIT_TUNNEL
-------------------------------------
Launch two ports testpmd, configure port 0 buffer split on tunnel, send matched packets to port 0 and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the tunnel.

Test Steps
~~~~~~~~~~
1. Launch two ports testpmd::
 
    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 -a 3b:00.1 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 

2. Modify common step 5 to::
 
    set rxhdrs grenat

   Execute common steps to configure port 0 buffer split on tunnel.

3. Send matched packets to port 0.
    
    Send MAC_IPV4_IPV4_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/IP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=34 and pay_len=50.
 
    Send MAC_IPV6_IPV6_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/IPv6()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=54 and pay_len=70.
 
    Send MAC_IPV4_UDP_VXLAN_MAC_IPV4_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP()/UDP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=50 and pay_len=72.

    Send MAC_IPV6_UDP_VXLAN_IPV6_TCP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/TCP()/("Y"*30)], iface="ens260f0")
 
    Check the received packets can be devided into two mempools with hdr_len=70 and pay_len=90.

    Send MAC_IPV4_GRE_MAC_IPV6_SCTP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IPv6()/SCTP()/("Y"*30)], iface="ens260f0")
 
    Check the received packets can be devided into two mempools with hdr_len=38 and pay_len=96.

    Send MAC_IPV6_GRE_IPV4_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=58 and pay_len=58.

4. Send mismatched packet to port 0::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/("Y"*30)], iface="ens260f0")
    
   Check the received packets can't be devided into two mempools with hdr_len=0 and pay_len=72.

5. Send matched packets to port 1::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/IP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/IPv6()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP()/UDP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/TCP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IPv6()/SCTP()/("Y"*30)], iface="ens260f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/("Y"*30)], iface="ens260f1")

   Check the received packets can't be devided into two mempools and the segment length should be empty.

.. note::

    Test Case 7~14 are queue buffer split cases. Verify the configuration of buffer split on single queue or queue group is effective. 
    It will not affect creating, matching and destroying of fdir rule. 

Test Case 7: QUEUE_BUFFER_SPLIT_OUTER_MAC
-----------------------------------------
Launch one port with multi queues testpmd, configure queue buffer split on outer mac, send matched packets and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the outer mac.

Test Steps
~~~~~~~~~~
1. Launch one port with multi queues testpmd::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 --txq=8 --rxq=8

2. Modify common step 2 to::
 
    port 0 rxq 1 rx_offload buffer_split on

   Execute common steps to configure queue buffer split on outer mac.

3. Create a fdir rule::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 1 / mark / end

4. Send matched packets.

    Send MAC_IPV4_UDP_VXLAN_MAC_IPV4_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1",dst="192.168.0.2")/("Y"*30)], iface="ens260f0")
    
    Check the received packets can be devided into two mempools with hdr_len=14 and pay_len=100.

5. Send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.1.1",dst="192.168.0.2")/("Y"*30)], iface="ens260f0") 
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1",dst="192.168.1.2")/("Y"*30)], iface="ens260f0") 

   If the received packets are distributed to queue 1 by RSS, check the received packets can be devided into two mempools with hdr_len=14 and pay_len=100. 
   Else check the received packets can't be devided into two mempools and the segment length should be empty.

6. Destroy the rule::

    flow destroy 0 rule 0  

Test Case 8: QUEUE_BUFFER_SPLIT_INNER_MAC
-----------------------------------------
Launch one port with multi queues testpmd, configure queue buffer split on inner mac, send matched packets and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the inner mac.

Test Steps
~~~~~~~~~~
1. Launch one port with multi queues testpmd::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 --txq=8 --rxq=8

2. Modify common step 2 to::
 
    port 0 rxq 2 rx_offload buffer_split on
    port 0 rxq 3 rx_offload buffer_split on 

   Modify common step 5 to::
   
    set rxhdrs inner-eth

   Execute common steps to configure queue buffer split on inner mac.

3. Create a fdir rule::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions rss queues 2 3 end / mark / end

4. Send matched packets.

    Send MAC_IPV4_UDP_VXLAN_MAC_IPV4_UDP_PAY packet::
  
      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1",dst="192.168.0.2")/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=64 and pay_len=50.

5. Send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.1.1",dst="192.168.0.2")/("Y"*30)], iface="ens260f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1",dst="192.168.1.2")/("Y"*30)], iface="ens260f0")  

   If the received packets are distributed to queue 2 or queue 3 by RSS, check the received packets can be devided into two mempools with hdr_len=64 and pay_len=50. 
   Else check the received packets can't be devided into two mempools and the segment length should be empty.

6. Destroy the rule::

    flow destroy 0 rule 0  

Test Case 9: QUEUE_BUFFER_SPLIT_INNER_IPV4
------------------------------------------
Launch one port with multi queues testpmd, configure queue buffer split on inner ipv4, send matched packets and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the inner ipv4.

Subcase 1: buffer split ipv4
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Steps
~~~~~~~~~~
1. Launch one port with multi queues testpmd::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 --txq=8 --rxq=8

2. Modify common step 2 to::
 
    port 0 rxq 2 rx_offload buffer_split on

   Modify common step 5 to::
   
    set rxhdrs ipv4

   Execute common steps to configure queue buffer split on inner ipv4.

3. Create a fdir rule::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 2 / mark / end

4. Send matched packets.

    Send MAC_IPV4_UDP_VXLAN_MAC_IPV4_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1",dst="192.168.0.2")/("Y"*30)], iface="ens260f0") 

    Check the received packets can be devided into two mempools with hdr_len=84 and pay_len=30.

5. Send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.1.1",dst="192.168.0.2")/("Y"*30)], iface="ens260f0") 
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1",dst="192.168.1.2")/("Y"*30)], iface="ens260f0") 

   If the received packets are distributed to queue 2 by RSS, check the received packets can be devided into two mempools with hdr_len=84 and pay_len=30. 
   Else check the received packets can't be devided into two mempools and the segment length should be empty.

6. Destroy the rule::

    flow destroy 0 rule 0  

Subcase 2: buffer split inner-ipv4
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv4

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner ipv4.

Test Case 10: QUEUE_BUFFER_SPLIT_INNER_IPV6
-------------------------------------------
Launch one port with multi queues testpmd, configure queue buffer split on inner ipv6, send matched packets and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the inner ipv6.

Subcase 1: buffer split ipv6
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Steps
~~~~~~~~~~
1. Launch one port with multi queues testpmd::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 --txq=8 --rxq=8

2. Modify common step 2 to::
 
    port 0 rxq 4 rx_offload buffer_split on
    port 0 rxq 5 rx_offload buffer_split on 

   Modify common step 5 to::
   
    set rxhdrs ipv6

   Execute common steps to configure queue buffer split on inner ipv6.

3. Create a fdir rule::

    flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / end actions rss queues 4 5 end / mark / end

4. Send matched packets.

    Send MAC_IPV6_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/("Y"*30)], iface="ens260f0")
 
    Check the received packets can be devided into two mempools with hdr_len=54 and pay_len=30. 

5. Send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::8",dst="2001::2")/("Y"*30)], iface="ens260f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::9")/("Y"*30)], iface="ens260f0")

   If the received packets are distributed to queue 4 or queue 5 by RSS, check the received packets can be devided into two mempools with hdr_len=54 and pay_len=30. 
   Else check the received packets can't be devided into two mempools and the segment length should be empty.

6. Destroy the rule::

    flow destroy 0 rule 0  

Subcase 2: buffer split inner-ipv6
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv6

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner ipv6.

Test Case 11: QUEUE_BUFFER_SPLIT_INNER_UDP
------------------------------------------
Launch one port with multi queues testpmd, configure queue buffer split on inner udp, send matched packets and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the inner udp.

Subcase 1: buffer split ipv4-udp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Steps
~~~~~~~~~~
1. Launch one port with multi queues testpmd::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 --txq=8 --rxq=8

2. Modify common step 2 to::
 
    port 0 rxq 3 rx_offload buffer_split on

   Modify common step 5 to::
   
    set rxhdrs ipv4-udp

   Execute common steps to configure queue buffer split on inner udp.

3. Create a fdir rule::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / udp dst is 23 / end actions queue index 3 / mark / end

4. Send matched packets.

    Send MAC_IPV4_UDP_VXLAN_MAC_IPV4_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(dport=23)/("Y"*30)], iface="ens260f0")  

    Check the received packets can be devided into two mempools with hdr_len=92 and pay_len=30. 

5. Send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.1.1", dst="192.168.0.2")/UDP(dport=23)/("Y"*30)], iface="ens260f0")

   If the received packets are distributed to queue 3 by RSS, check the received packets can be devided into two mempools with hdr_len=92 and pay_len=30. 
   Else check the received packets can't be devided into two mempools and the segment length should be empty.

6. Destroy the rule::

    flow destroy 0 rule 0  

Subcase 2: buffer split ipv6-udp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Steps
~~~~~~~~~~
1. Launch one port multi queues testpmd::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 --txq=8 --rxq=8

2. Modify common step 2 to::
 
     port 0 rxq 3 rx_offload buffer_split on

   Modify common step 5 to::
   
    set rxhdrs ipv6-udp

   Execute common steps to configure queue buffer split on inner udp.

3. Create a fdir rule::

    flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp dst is 23 / end actions queue index 3 / mark / end

4. Send matched packets.

    Send MAC_IPV6_UDP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/UDP(dport=23)/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=62 and pay_len=30.      

5. Send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::8",dst="2001::2")/UDP(dport=23)/("Y"*30)], iface="ens260f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/UDP(dport=24)/("Y"*30)], iface="ens260f0")

   If the received packets are distributed to queue 3 by RSS, check the received packets can be devided into two mempools with hdr_len=62 and pay_len=30. 
   Else check the received packets can't be devided into two mempools and the segment length should be empty.

6. Destroy the rule::

    flow destroy 0 rule 0  

Subcase 3: buffer split inner-ipv4-udp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv4-udp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner udp.

Subcase 4: buffer split inner-ipv6-udp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 2 test step 2 to::

    set rxhdrs inner-ipv6-udp

2. Execute subcase 2 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner udp.

Test Case 12: QUEUE_BUFFER_SPLIT_INNER_TCP
------------------------------------------
Launch one port with multi queues testpmd, configure queue buffer split on inner tcp, send matched packets and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the inner tcp.

Subcase 1: buffer split ipv4-tcp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Steps
~~~~~~~~~~
1. Launch one port with multi queues testpmd::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 --txq=8 --rxq=8

2. Modify common step 2 to::
 
    port 0 rxq 2 rx_offload buffer_split on
    port 0 rxq 3 rx_offload buffer_split on 

   Modify common step 5 to::
   
    set rxhdrs ipv4-tcp

   Execute common steps to configure queue buffer split on inner tcp.

3. Create a fdir rule::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / tcp dst is 23 / end actions rss queues 2 3 end / mark / end

4. Send matched packets.

    Send MAC_IPV4_UDP_VXLAN_MAC_IPV4_TCP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=23)/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=104 and pay_len=30. 

5. Send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.1.1", dst="192.168.0.2")/TCP(dport=23)/("Y"*30)], iface="ens260f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=24)/("Y"*30)], iface="ens260f0")

   If the received packets are distributed to queue 2 or queue 3 by RSS, check the received packets can be devided into two mempools with hdr_len=104 and pay_len=30. 
   Else check the received packets can't be devided into two mempools and the segment length should be empty.

6. Destroy the rule::

    flow destroy 0 rule 0  

Subcase 2: buffer split ipv6-tcp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Steps
~~~~~~~~~~
1. Launch one port multi queues testpmd::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 --txq=8 --rxq=8

2. Modify common step 2 to::
 
     port 0 rxq 2 rx_offload buffer_split on
     port 0 rxq 3 rx_offload buffer_split on 

   Modify common step 5 to::
   
    set rxhdrs ipv6-tcp

   Execute common steps to configure queue buffer split on inner udp.

3. Create a fdir rule::

    flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / tcp dst is 23 / end actions rss queues 2 3 end / mark / end

4. Send matched packets.

    Send MAC_IPV6_TCP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/TCP(dport=23)/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=74 and pay_len=30. 

5. Send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::8",dst="2001::2")/TCP(dport=23)/("Y"*30)], iface="ens260f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/TCP(dport=24)/("Y"*30)], iface="ens260f0")

   If the received packets are distributed to queue 2 or queue 3 by RSS, check the received packets can be devided into two mempools with hdr_len=74 and pay_len=30. 
   Else check the received packets can't be devided into two mempools and the segment length should be empty.

6. Destroy the rule::

    flow destroy 0 rule 0  

Subcase 3: buffer split inner-ipv4-tcp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv4-tcp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner tcp.

Subcase 4: buffer split inner-ipv6-tcp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 2 test step 2 to::

    set rxhdrs inner-ipv6-tcp

2. Execute subcase 2 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner tcp.

Test Case 13: QUEUE_BUFFER_SPLIT_INNER_SCTP
-------------------------------------------
Launch one port with multi queues testpmd, configure queue buffer split on inner sctp, send matched packets and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the inner sctp.

Subcase 1: buffer split ipv4-sctp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Steps
~~~~~~~~~~
1. Launch one port multi queues testpmd::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 --txq=8 --rxq=8

2. Modify common step 2 to::
 
    port 0 rxq 5 rx_offload buffer_split on

   Modify common step 5 to::
   
    set rxhdrs ipv4-sctp

   Execute common steps to configure queue buffer split on inner sctp.

3. Create a fdir rule::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / sctp dst is 23 / end actions queue index 5 / mark / end

4. Send matched packets.

    Send MAC_IPV4_UDP_VXLAN_MAC_IPV4_SCTP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(dport=23)/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=96 and pay_len=30. 

5. Send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.1.1", dst="192.168.0.2")/SCTP(dport=23)/("Y"*30)], iface="ens260f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(dport=24)/("Y"*30)], iface="ens260f0")

   If the received packets are distributed to queue 5 by RSS, check the received packets can be devided into two mempools with hdr_len=96 and pay_len=30. 
   Else check the received packets can't be devided into two mempools and the segment length should be empty.

6. Destroy the rule::

    flow destroy 0 rule 0  

Subcase 2: buffer split ipv6-sctp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Steps
~~~~~~~~~~
1. Launch one port multi queues testpmd::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 --txq=8 --rxq=8

2. Modify common step 2 to::
 
     port 0 rxq 5 rx_offload buffer_split on

   Modify common step 5 to::
   
    set rxhdrs ipv6-sctp

   Execute common steps to configure queue buffer split on inner sctp.

3. Create a fdir rule::

    flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / sctp dst is 23 / end actions queue index 5 / mark / end

4. Send matched packets.

    Send MAC_IPV6_SCTP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/SCTP(dport=23)/("Y"*30)], iface="ens260f0")
    
    Check the received packets can be devided into two mempools with hdr_len=66 and pay_len=30. 
   
5. Send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::8",dst="2001::2")/SCTP(dport=23)/("Y"*30)], iface="ens260f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/SCTP(dport=24)/("Y"*30)], iface="ens260f0")

   If the received packets are distributed to queue 5 by RSS, check the received packets can be devided into two mempools with hdr_len=66 and pay_len=30. 
   Else check the received packets can't be devided into two mempools and the segment length should be empty.

6. Destroy the rule::

    flow destroy 0 rule 0  

Subcase 3: buffer split inner-ipv4-sctp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 1 test step 2 to::

    set rxhdrs inner-ipv4-sctp

2. Execute subcase 1 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner sctp.

Subcase 4: buffer split inner-ipv6-sctp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Modify subcase 2 test step 2 to::

    set rxhdrs inner-ipv6-sctp

2. Execute subcase 2 test steps to check the received packets can be devided into two mempools with expected hdr and payload length/content by the inner sctp.

Test Case 14: QUEUE_BUFFER_SPLIT_TUNNEL
---------------------------------------
Launch one port with multi queues testpmd, configure queue buffer split on tunnel, send matched packets and check the received packets
can be devided into two mempools with expected hdr and payload length/content by the tunnel.

Test Steps
~~~~~~~~~~
1. Launch one port multi queues testpmd::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a 3b:00.0 --force-max-simd-bitwidth=64 -- -i --mbuf-size=2048,2048 --txq=8 --rxq=8

2. Modify common step 2 to::
 
    port 0 rxq 4 rx_offload buffer_split on
    
    port 0 rxq 5 rx_offload buffer_split on

   Modify common step 5 to::
   
    set rxhdrs grenat

   Execute common steps to configure queue buffer split on inner udp.

3. Create a fdir rule::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / udp dst is 23 / end actions rss queues 4 5 end / mark / end

4. Send matched packets.

    Send MAC_IPV4_UDP_VXLAN_MAC_IPV4_SCTP_PAY packet::

      sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(dport=23)/("Y"*30)], iface="ens260f0")

    Check the received packets can be devided into two mempools with hdr_len=50 and pay_len=72. 
  
5. Send mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.1.1", dst="192.168.0.2")/UDP(dport=23)/("Y"*30)], iface="ens260f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(dport=24)/("Y"*30)], iface="ens260f0")
    
   If the received packets are distributed to queue 4 or queue 5 by RSS, check the received packets can be devided into two mempools with hdr_len=50 and pay_len=72. 
   Else check the received packets can't be devided into two mempools and the segment length should be empty.

6. Destroy the rule::

    flow destroy 0 rule 0  

