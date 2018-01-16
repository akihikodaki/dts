.. Copyright (c) <2011-2017>, Intel Corporation
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

===============================================
Fortville RSS - Configuring Hash Function Tests
===============================================

This document provides test plan for testing the function of Fortville:
Support configuring hash functions.


Prerequisites
=============

* 2x Intel® 82599 (Niantic) NICs (2x 10GbE full duplex optical ports per NIC)
* 1x Fortville_eagle NIC (4x 10G)
* 1x Fortville_spirit NIC (2x 40G)
* 2x Fortville_spirit_single NIC (1x 40G)

The four ports of the 82599 connect to the Fortville_eagle;
The two ports of Fortville_spirit connect to Fortville_spirit_single.
The three kinds of NICs are the target NICs. the connected NICs can send packets
to these three NICs using scapy.

Network Traffic
---------------

The RSS feature is designed to improve networking performance by load balancing
the packets received from a NIC port to multiple NIC RX queues, with each queue
handled by a different logical core.

#. The receive packet is parsed into the header fields used by the hash
   operation (such as IP addresses, TCP port, etc.)

#. A hash calculation is performed. The Fortville supports four hash function:
   Toeplitz, simple XOR and their Symmetric RSS.

#. The seven LSBs of the hash result are used as an index into a 128/512 entry
   'redirection table'. Each entry provides a 4-bit RSS output index.

#. There are four cases to test the four hash function.

Test Case:  test_toeplitz
=========================

Testpmd configuration - 16 RX/TX queues per port
------------------------------------------------

#. set up testpmd with fortville NICs::

      ./testpmd -c fffff -n %d -- -i --coremask=0xffffe --rxq=16 --txq=16

#. Reta Configuration.  128 reta entries configuration::

       testpmd command: port config 0 rss reta (hash_index,queue_id)

#. PMD fwd only receive the packets::

       testpmd command: set fwd rxonly

#. rss received package type configuration two received packet types configuration::

       testpmd command: port config 0 rss ip/udp

#. verbose configuration::

       testpmd command: set verbose 8

#. set hash functions, can choose symmetric or not, choose port and packet type::

       set_hash_function 0 toeplitz

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

  set_hash_function 0 toeplitz
  set_sym_hash_ena_per_port 0 enable
  set_sym_hash_ena_per_pctype 0 35 enable

And send packets with the same flow in different direction::

  sendp([Ether(dst="90:e2:ba:36:99:3c")/IP(src="192.168.0.4", dst="192.168.0.5")], iface="eth3")
  sendp([Ether(dst="90:e2:ba:36:99:3c")/IP(src="192.168.0.5", dst="192.168.0.4")], iface="eth3")

And the hash value and queue should be the same for these two flow .

Test Case:  test_simple
=======================

The same as the above two test cases. Just pay attention to set the hash function to "simple xor"

Test Case:  test_simple_symmetric
=================================

The same as the above two test cases. Just pay attention to set the hash function to "simple xor"

Test Case:  test_dynamic_rss_bond_config
========================================
This case test bond slaves will auto sync rss hash config, it only support by fortville.

#. set up testpmd with fortville NICs::

      ./testpmd -c f -n 4 -- -i --portmask 0x3 --tx-offloads=0x8fff

#. create bond device with mode 3::

      create bonded device 3 0

#. add slave to bond device::

      add bonding slave 0 2
      add bonding slave 1 2

#. get default hash algorithm on slave::

      get_hash_global_config 0
      get_hash_global_config 1

#. set hash algorithm on slave 0::

      set_hash_global_config 0 simple_xor ipv4-other enable

#. get hash algorithm on slave 0 and 1::

      get_hash_global_config 0
      get_hash_global_config 1

#. check slave 0 and 1 use same hash algorithm
