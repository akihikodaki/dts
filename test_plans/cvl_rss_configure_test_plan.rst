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

=============================
CVL: RSS CONFIGURE AND UPDATE
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

   - Intel E810 series ethernet cards: columbiaville

2. Software:

   - dpdk: http://dpdk.org/git/dpdk
   - scapy: http://www.secdev.org/projects/scapy/

3. bind the CVL port to dpdk driver in DUT::

    modprobe vfio-pci
    usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:18:00.0

Test Case: test_command_line_option_rss_ip
==========================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10 --rss-ip
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

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10 --rss-udp
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

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10 --disable-rss
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

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
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

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
    testpmd>set fwd rxonly
    testpmd>set verbose 1

2. rss received package type configuration::

    testpmd> port config all rss udp
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

Test Case: test_RSS_configure_to_tcp
====================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
    testpmd>set fwd rxonly
    testpmd>set verbose 1

2. rss received package type configuration::

    testpmd> port config all rss tcp
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

Test Case: test_RSS_configure_to_sctp
=====================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
    testpmd>set fwd rxonly
    testpmd>set verbose 1

2. rss received package type configuration::

    testpmd> port config all rss sctp
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

10. check ipv6-sctp packets:
    send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

Test Case: test_RSS_configure_to_all
====================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
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

10. check ipv6-sctp packets:
    send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

Test Case: test_RSS_configure_to_default
========================================

1. Launch the testpmd in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=10 --txq=10
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

10. check ipv6-sctp packets:
    send a basic packet, record the hash value::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")

   send packets with changed input set, check the received packets have different hash value with the basic packet::

        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::4",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
        sendp([Ether(dst="00:00:00:00:01:00")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::5")/SCTP(sport=1024,dport=1025)/("X"*40)], iface="enp27s0f2")
