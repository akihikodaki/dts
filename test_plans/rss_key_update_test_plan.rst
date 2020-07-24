.. # BSD LICENSE
    #
    # Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
    # Copyright © 2018[, 2019] The University of New Hampshire. All rights reserved.
    # All rights reserved.
    #
    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions
    # are met:
    #
    #   * Redistributions of source code must retain the above copyright
    #     notice, this list of conditions and the following disclaimer.
    #   * Redistributions in binary form must reproduce the above copyright
    #     notice, this list of conditions and the following disclaimer in
    #     the documentation and/or other materials provided with the
    #     distribution.
    #   * Neither the name of Intel Corporation nor the names of its
    #     contributors may be used to endorse or promote products derived
    #     from this software without specific prior written permission.
    #
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    # "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    # LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    # A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    # OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    # SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    # LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    # DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    # THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

=====================
RSS Key Update Tests
=====================

This document provides test plan to configure Receive Side Scaling (RSS)
hash key. This test case use similar testing method in ```pmdrss_hash```.
Verify setting a new hash key will result a change in packets queue destination.

=============
Prerequisites
=============

Assuming that ports ``0`` and ``1`` of the test target are directly connected
to the traffic generator and hash function Toeplitz is supported.


Test Case: test_set_hash_key_toeplitz
=====================================

#. Launch the ``testpmd`` application with the following arguments::

    ./testpmd -c ffffff -n 4 -- -i --portmask=0x6 --rxq=16 --txq=16

#. PMD fwd only receive the packets::

    testpmd> set fwd rxonly

#. Set port verbosity to 8::

    testpmd> set verbose 8

#. Configure a RETA table with 512 or 128 entries to store queue::

    testpmd> port config 0 rss reta (hash_index,queue_id)

#. Set hash function, symmetric, port and packet type::

    testpmd> set_hash_global_config 0 toeplitz ipv4-udp enable

#. Send packet and print the hash value and queue id of every packet. \
   Then use the hash value % the table size to find expected queue id. \
   Make sure the expected queue and the destination queue id are the same.

#. Check RSS enable/disable and types of RSS hash function for each port::

    testpmd> show port <port-id> rss-hash

   RSS is on by default, unless ```--disable-rss``` flag is apply.

#. Configure new RSS hash key::

    testpmd> port config <port_id> rss-hash-key <ipv4|ipv4-frag|\
                  ipv4-tcp|ipv4-udp|ipv4-sctp|ipv4-other|\
                  ipv6|ipv6-frag|ipv6-tcp|ipv6-udp|ipv6-sctp|\
                  ipv6-other|l2-payload|ipv6-ex|ipv6-tcp-ex|\
                  ipv6-udp-ex> <string of hex digits>

#. Send packet and print the hash value again to check if they have the same hash value and destination queue id.


Test Case: test_set_hash_key_toeplitz_symmetric
================================================

Same steps as the "test_set_hash_key_toeplitz" test case.
When set hash function you will need to add::

    testpmd>  set_sym_hash_ena_per_port 0 enable

Then send in packet as normal.

Test Case: test_set_hash_key_long_short
========================================

#. Check hash key size is supported in "show port info"

#. Check RSS is enable

#. Configure RSS hash key in testpmd with longer/normal/shorter hash key::

    testpmd> port config <port_id> rss-hash-key <ipv4|ipv4-frag|\
                  ipv4-tcp|ipv4-udp|ipv4-sctp|ipv4-other|\
                  ipv6|ipv6-frag|ipv6-tcp|ipv6-udp|ipv6-sctp|\
                  ipv6-other|l2-payload|ipv6-ex|ipv6-tcp-ex|\
                  ipv6-udp-ex> <string of hex digits>

#. Display updated key and compare it with the original key::

    testpmd> show port <port-id> rss-hash key

