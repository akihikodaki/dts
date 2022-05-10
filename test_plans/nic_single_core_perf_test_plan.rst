.. Copyright (c) <2016>, Intel Corporation
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

========================================================================================
Benchmark the performance of single core forwarding with XXV710 and 82599/500 Series 10G
========================================================================================

Prerequisites
=============

1. Hardware:

    1.1) nic_single_core_perf test for Intel® Ethernet Network Adapter XXV710-DA2 :
        two dual port Intel® Ethernet Network Adapter XXV710-DA2 nics, all installed
        on the same socket, pick one port per nic
    1.2) nic_single_core_perf test for 82599/500 Series 10G: four 82599 nics, all
        installed on the same socket, pick one port per nic
  
2. Software::

    dpdk: git clone http://dpdk.org/git/dpdk
    scapy: http://www.secdev.org/projects/scapy/
    dts (next branch): git clone http://dpdk.org/git/tools/dts, 
                       then "git checkout next" 
    Trex code: http://trex-tgn.cisco.com/trex/release/v2.26.tar.gz 
               (to be run in stateless Layer 2 mode, see section in
                Getting Started Guide for more details)
    python-prettytable:
        apt install python-prettytable (for ubuntu os) 
        or dnf install python-prettytable (for fedora os). 

3. Connect all the selected nic ports to traffic generator(IXIA,TREX,
   PKTGEN) ports(TG ports)::

    2 TG 25g ports for Intel® Ethernet Network Adapter XXV710-DA2 ports
    4 TG 10g ports for 4 82599/500 Series 10G ports

4. Case config::

    For Intel® Ethernet Converged Network Adapter XL710-QDA2, if test 16
    Byte Descriptor, need to be configured with the
    "-Dc_args=-DRTE_LIBRTE_I40E_16BYTE_RX_DESC" option at compile time.

    For Intel® Ethernet Network Adapter E810-XXVDA4, if test 16 Byte Descriptor,
    need to be configured with the
    "-Dc_args=-DRTE_LIBRTE_ICE_16BYTE_RX_DESC" option at compile time.
    

Test Case : Single Core Performance Measurement
===============================================
1) Bind tested ports to igb_uio

2) Start testpmd::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 -- -i \
         --portmask=0xf  --txd=128 --rxd=128
        testpmd> start
        
3) Configure traffic generator to send traffic
    configure one below stream for each TG port
        dst mac: peer nic port mac
        src ip : random
        dst ip : random
        packet length : 64 byte
        
4)  check throughput and compare it with the expected value.

5)  for 82599/500 Series 10G, repeat above step 1-4 for txd=rxd=512,2048 separately.
    for Intel® Ethernet Network Adapter XXV710-DA2  nic, just test
    txd=rxd=512,2048 following above steps 1-4.

6) Result tables for different NICs:

   Intel® Ethernet Network Adapter XXV710-DA2:

   +------------+---------+-------------+---------+---------------------+
   | Frame Size | TXD/RXD |  Throughput |   Rate  | Expected Throughput |
   +------------+---------+-------------+---------+---------------------+
   |     64     |   512   | xxxxxx Mpps |   xxx % |     xxx    Mpps     |
   +------------+---------+-------------+---------+---------------------+
   |     64     |   2048  | xxxxxx Mpps |   xxx % |     xxx    Mpps     |
   +------------+---------+-------------+---------+---------------------+

   82599/500 Series 10G:

   +------------+---------+-------------+---------+---------------------+
   | Frame Size | TXD/RXD |  Throughput |   Rate  | Expected Throughput |
   +------------+---------+-------------+---------+---------------------+
   |     64     |   128   | xxxxxx Mpps |   xxx % |       xxx  Mpps     |
   +------------+---------+-------------+---------+---------------------+
   |     64     |   512   | xxxxxx Mpps |   xxx % |       xxx  Mpps     |
   +------------+---------+-------------+---------+---------------------+
   |     64     |   2048  | xxxxxx Mpps |   xxx % |       xxx  Mpps     |
   +------------+---------+-------------+---------+---------------------+

Note : The values for the expected throughput may vary due to different
       platform and OS, and traffic generator, please correct threshold
       values accordingly. (the above expected values for XXV710 and
       82599/500 Series 10G were got from the combination of Purly,
       Ubuntu 16.04, and traffic generator IXIA)

Case will raise failure if actual throughputs have more than 1Mpps gap
from expected ones. 
