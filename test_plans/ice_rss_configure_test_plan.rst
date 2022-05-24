.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2020 Intel Corporation

=============================
ICE: RSS CONFIGURE AND UPDATE
=============================

Description
===========

Initialize and update RSS configure based on user request, dont't remove exist
configure just to make sure all the request has been applied.

enable or disable corresponding flows' RSS base on  rte_eth_rss_conf->rss_hf
parameters in dev_config and rss_hash_update ops.

1. Enable the flowing command of testpmd:

Testpmd Command-line Options:

--rss-ip:set RSS functions for IPv4/IPv6 only.

--rss-udp: set RSS functions for IPv4/IPv6 and UDP.

--disable-rss:disable RSS (Receive Side Scaling).

2. Testpmd Runtime Functions:

port config all rss: set the RSS (Receive Side Scaling) mode on or off.

port config all rss ip/udp/tcp/sctp/all/default

Prerequisites
=============

1. Hardware:

   - Intel® Ethernet 800 Series

2. Software:

   - dpdk: http://dpdk.org/git/dpdk
   - scapy: http://www.secdev.org/projects/scapy/

3. bind the Intel® Ethernet 800 Series port to dpdk driver in DUT::

    modprobe vfio-pci
    usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:18:00.0

Test Case: test_command_line_option_rss_ip
==========================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10 --rss-ip
    testpmd>set fwd rxonly
    testpmd>set verbose 1
    testpmd>start

2. check ipv4 packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/("X"*40)], iface="enp27s0f2")

3. check ipv6 packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/("X"*40)], iface="enp27s0f2")

4. check ipv4-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

5. check ipv6-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

6. check ipv4-tcp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

7. check ipv6-tcp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

8. check ipv4-sctp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

9. check ipv6-sctp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

Test Case: test_command_line_option_rss_udp
===========================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10 --rss-udp
    testpmd>set fwd rxonly
    testpmd>set verbose 1
    testpmd>start

2. check ipv4-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

3. check ipv6-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

4. check ipv4 packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")

5. check ipv6 packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")

6. check ipv4-tcp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

7. check ipv6-tcp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

8. check ipv4-sctp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

9. check ipv6-sctp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

Test Case: test_command_line_option_disable-rss
===============================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10 --disable-rss
    testpmd>set fwd rxonly
    testpmd>set verbose 1
    testpmd>start

2. check all tyep packets:
   send basic packets, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

Test Case: test_RSS_configure_to_ip
===================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
    testpmd>set fwd rxonly
    testpmd>set verbose 1

2. rss received package type configuration::

    testpmd> port config all rss ip
    testpmd> start

3. check ipv4 packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/("X"*40)], iface="enp27s0f2")

4. check ipv6 packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/("X"*40)], iface="enp27s0f2")

5. check ipv4-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

6. check ipv6-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

7. check ipv4-tcp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

8. check ipv6-tcp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

9. check ipv4-sctp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

10. check ipv6-sctp packets:
    send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send a packet with same input set and changed other parameters.
   check the received packet have same hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1026,dport=1027)/("X"*40)], iface="enp27s0f2")

Test Case: test_RSS_configure_to_udp
====================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
    testpmd>set fwd rxonly
    testpmd>set verbose 1

2. rss received package type configuration::

    testpmd> port config all rss udp
    testpmd> start

3. check ipv4-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

4. check ipv6-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

5. check ipv4 packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")

6. check ipv6 packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")

7. check ipv4-tcp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

8. check ipv6-tcp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

9. check ipv4-sctp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

10. check ipv6-sctp packets:
    send a basic packet, verify no hash value::

         sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

Test Case: test_RSS_configure_to_tcp
====================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
    testpmd>set fwd rxonly
    testpmd>set verbose 1

2. rss received package type configuration::

    testpmd> port config all rss tcp
    testpmd> start

3. check ipv4-tcp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")

4. check ipv6-tcp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")

5. check ipv4 packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")

6. check ipv6 packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")

7. check ipv4-udp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

8. check ipv6-udp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

9. check ipv4-sctp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

10. check ipv6-sctp packets:
    send a basic packet, verify no hash value::

         sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

Test Case: test_RSS_configure_to_sctp
=====================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
    testpmd>set fwd rxonly
    testpmd>set verbose 1

2. rss received package type configuration::

    testpmd> port config all rss sctp
    testpmd> start

3. check ipv4-sctp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/SCTP(sport=1024,dport=1026)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/SCTP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

4. check ipv6-sctp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1026)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/SCTP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

5. check ipv4 packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")

6. check ipv6 packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")

7. check ipv4-tcp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

8. check ipv6-tcp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

9. check ipv4-udp packets:
   send a basic packet, verify no hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

10. check ipv6-udp packets:
    send a basic packet, verify no hash value::

         sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

Test Case: test_RSS_configure_to_all
====================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
    testpmd>set fwd rxonly
    testpmd>set verbose 1

2. rss received package type configuration::

    testpmd> port config all rss all
    testpmd> start

3. check ipv4 packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/("X"*40)], iface="enp27s0f2")

4. check ipv6 packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/("X"*40)], iface="enp27s0f2")

5. check ipv4-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

6. check ipv6-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

7. check ipv4-tcp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")

8. check ipv6-tcp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")

9. check ipv4-sctp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1026)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

10. check ipv6-sctp packets:
    send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1026)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

Test Case: test_RSS_configure_to_default
========================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
    testpmd>set fwd rxonly
    testpmd>set verbose 1

2. rss received package type configuration::

    testpmd> port config all rss default
    testpmd> start

3. check ipv4 packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/("X"*40)], iface="enp27s0f2")

4. check ipv6 packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/("X"*40)], iface="enp27s0f2")

5. check ipv4-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

6. check ipv6-udp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/UDP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

7. check ipv4-tcp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")

8. check ipv6-tcp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/TCP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1027)/("X"*40)], iface="enp27s0f2")

9. check ipv4-sctp packets:
   send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.4",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1026)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")

10. check ipv6-sctp packets:
    send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1026)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1026,dport=1025)/("X"*40)], iface="enp27s0f2")
