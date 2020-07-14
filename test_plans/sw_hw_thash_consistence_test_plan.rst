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

======================================================
Software/hardware Toeplitz hash consistence test suite
======================================================

This test suite is to check if the Toeplitz hash by hardware (NIC) is consistence 
with by software (rte_hash)

First apply a DPDK patch, which provide an example for calling rte_hash ::

    cd <dpdk>
    git apply <dts>/dep/0001-Generate-an-example-for-calling-thash-lib.patch

Compile the example ::

    export RTE_SDK=<dpdk>
    cd <dpdk>/examples/thash
    make

Run thash example, which supported format: thash_test TYPE(ipv4|ipv4-udp|ipv4-tcp) IP_DST IP_SRC PORT_DST PORT_SRC ::

    ./build/thash_test ipv6 ::22 ::11 1234 4321
    # The output
    ipv6
    ::22
    ::11
    1234
    4321

    Hash value = 914e08e4

Then, configure the NIC and send packets to the NIC, expect the hash value by NIC is same to thash_test ::

    # Launch testpmd, and configure the hash key
    testpmd> set verbose 1
    testpmd> start
    testpmd> port config 0 rss-hash-key ipv6 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
    # Send packet to testpmd's interface
    sendp(Ether(dst="52:36:30:A0:73:69")/IPv6(dst="::22",src="::11"),iface='ens801f1')
    # The RSS hash value is same to thash_test result
    port 0/queue 4: received 1 packets
    src=00:00:00:00:00:00 - dst=52:36:30:A0:73:69 - type=0x86dd - length=60 - nb_segs=1 - RSS hash=0x914e08e4 - RSS queue=0x4 - sw ptype: L2_ETHER L3_IPV6  - l2_len=14 - l3_len=40 - Receive queue=0x4
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN 
