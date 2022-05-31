.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2011-2017 Intel Corporation

================================================================
Intel® Ethernet 700 Series RSS - Configuring Hash Function Tests
================================================================

This document provides test plan for testing the function of Intel® Ethernet 700 Series:
Support configuring hash functions.


Prerequisites
=============

* 2x 82599 NICs (2x 10GbE full duplex optical ports per NIC)
* 1x X710 NIC (4x 10G)
* 1x XL710 NIC (2x 40G)
* 2x XL710 NIC (1x 40G)

The four ports of the 82599 connect to the X710;
The two ports of XL710 connect to XL710.
The three kinds of NICs are the target NICs. the connected NICs can send packets
to these three NICs using scapy.

Network Traffic
---------------

The RSS feature is designed to improve networking performance by load balancing
the packets received from a NIC port to multiple NIC RX queues, with each queue
handled by a different logical core.

#. The receive packet is parsed into the header fields used by the hash
   operation (such as IP addresses, TCP port, etc.)

#. A hash calculation is performed. The Intel® Ethernet 700 Series supports four
   hash function:
   Toeplitz, simple XOR and their Symmetric RSS.

#. The seven LSBs of the hash result are used as an index into a 128/512 entry
   'redirection table'. Each entry provides a 4-bit RSS output index.

#. There are four cases to test the four hash function.

Test Case:  test_toeplitz
=========================

Testpmd configuration - 16 RX/TX queues per port
------------------------------------------------

#. set up testpmd with Intel® Ethernet 700 Series NICs::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c fffff -n %d -- -i --coremask=0xffffe --rxq=16 --txq=16

#. Reta Configuration.  128 reta entries configuration::

       testpmd command: port config 0 rss reta (hash_index,queue_id)

#. PMD fwd only receive the packets::

       testpmd command: set fwd rxonly

#. rss received package type configuration two received packet types configuration::

       testpmd command: port config 0 rss ip/udp

#. verbose configuration::

       testpmd command: set verbose 8

#. set hash functions, can choose symmetric or not, choose port, rss type and packet type::

       Toeplitz hash function: toeplitz
       testpmd command:
         flow create <port_id> ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end func toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / end actions rss types ipv4-other end queues end func toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / end actions rss types ipv4-frag end queues end func toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end func toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end func toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / end actions rss types ipv6-other end queues end func toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end func toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end func toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end func toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / end actions rss types ipv6-frag end queues end func toeplitz queues end / end

#. start packet receive::

       testpmd command: start

tester Configuration
--------------------

#. set up scapy

#. send packets with different type ipv4/ipv4 with tcp/ipv4 with udp/
   ipv6/ipv6 with tcp/ipv6 with udp::

    sendp([Ether(dst="90:e2:ba:36:99:3c")/IP(src="192.168.0.4", dst="192.168.0.5")], iface="eth3")

test result
-----------

The testpmd will print the hash value and actual queue of every packet.

#. Calculate the queue id: hash value%128or512, then refer to the redirection table
   to get the theoretical queue id.

#. Compare the theoretical queue id with the actual queue id.


Test Case:  test_toeplitz_symmetric
===================================

The same with the above steps, pay attention to "set hash function", should use::

       Symmetric Toeplitz hash function: symmetric_toeplitz
       testpmd command:
         flow create <port_id> ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end func symmetric_toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / end actions rss types ipv4-other end queues end func symmetric_toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / end actions rss types ipv4-frag end queues end func symmetric_toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end func symmetric_toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end func symmetric_toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / end actions rss types ipv6-other end queues end func symmetric_toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end func symmetric_toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end func symmetric_toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end func symmetric_toeplitz queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / end actions rss types ipv6-frag end queues end func symmetric_toeplitz queues end / end

And send packets with the same flow in different direction::

  sendp([Ether(dst="90:e2:ba:36:99:3c")/IP(src="192.168.0.4", dst="192.168.0.5")], iface="eth3")
  sendp([Ether(dst="90:e2:ba:36:99:3c")/IP(src="192.168.0.5", dst="192.168.0.4")], iface="eth3")

And the hash value and queue should be the same for these two flow .

Test Case:  test_simple
=======================

The same as the above test case "test_toeplitz". Just pay attention to set the hash function to "simple xor"::

       simple XOR hash function: simple_xor
       testpmd command:
         flow create <port_id> ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end func simple_xor queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / end actions rss types ipv4-other end queues end func simple_xor queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / end actions rss types ipv4-frag end queues end func simple_xor queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end func simple_xor queues end / end
         flow create <port_id> ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end func simple_xor queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / end actions rss types ipv6-other end queues end func simple_xor queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end func simple_xor queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end func simple_xor queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end func simple_xor queues end / end
         flow create <port_id> ingress pattern eth / ipv6 / end actions rss types ipv6-frag end queues end func simple_xor queues end / end

