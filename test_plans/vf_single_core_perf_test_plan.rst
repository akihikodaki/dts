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
Benchmark the performance of VF single core forwarding
======================================================

Prerequisites
=============

1.  Nic single core performance test requirements:

    1.1) Intel® Ethernet Network Adapter XXV710-DA2:
         two dual port Intel® Ethernet Network Adapter XXV710-DA2 nics,all
         installed on the same socket, pick one port per nic.
    1.2) 82599/500 Series 10G:
         four 82599 nics, all installed on the same socket, pick one port per nic.
    1.3) Intel® Ethernet Network Adapter E810-CQDA2:
         one Intel® Ethernet Network Adapter E810-CQDA2 nics, all installed on the
         same socket, pick one port per nic.

2. Software::

    dpdk: git clone http://dpdk.org/git/dpdk
    scapy: http://www.secdev.org/projects/scapy/
    dts (next branch): git clone http://dpdk.org/git/tools/dts, 
                       then "git checkout next" 
    Trex code: http://trex-tgn.cisco.com/trex/release/v2.84.tar.gz 
               (to be run in stateless Layer 2 mode, see section in
                Getting Started Guide for more details)
    python-prettytable:
        apt install python-prettytable (for ubuntu os) 
        or dnf install python-prettytable (for fedora os). 

3. Connect all the selected nic ports to traffic generator(IXIA,TREX,
   PKTGEN) ports(TG ports)::

    2 TG 25g  ports for Intel® Ethernet Network Adapter XXV710-DA2 ports
    4 TG 10g  ports for 4 82599/500 Series 10G ports
    1 TG 100g ports for Intel® Ethernet Network Adapter E810-CQDA2 port

Test Case : Vf Single Core Performance Measurement
==================================================

1. Bind PF ports to kernel driver, i40e/ixgbe/ice, then create 1 VF from each PF,
   take XXV710 for example::

    echo 1 > /sys/bus/pci/devices/0000\:af\:00.0/sriov_numvfs
    echo 1 > /sys/bus/pci/devices/0000\:b1\:00.1/sriov_numvfs

2. Set vf mac address::

    ip link set ens5f0 vf 0 mac 00:12:34:56:78:01
    ip link set ens6f0 vf 0 mac 00:12:34:56:78:02

3. Bind all the created VFs to dpdk driver, vfio-pci or igb_uio::

    ./usertools/dpdk-devbind.py -b vfio-pci af:02.0 b1:02.0

4. Start testpmd::

    ./<build_target>/app/dpdk-testpmd -l 28,29 -n 4 -- -i --portmask=0x3  --txd=512 --rxd=512 \
    --txq=2 --rxq=2 --nb-cores=1

    testpmd> set fwd mac
    testpmd> start

5. Configure traffic generator to send traffic::

    dst mac: peer nic port mac
    src ip : random
    dst ip : fixed
    frame size: 64 byte
    transmit rate: 100%

6. Result tables.

   +-----------+------------+---------+-------------+---------+---------------------+
   |  Fwd_core | Frame Size | TXD/RXD |  Throughput |   Rate  | Expected Throughput |
   +===========+============+=========+=============+=========+=====================+
   |  1C/1T    |    64      |   512   |  xxxxx Mpps |   xxx % |  xxxxxxx   Mpps     |
   +-----------+------------+---------+-------------+---------+---------------------+
   |  1C/1T    |    64      |   2048  |  xxxxx Mpps |   xxx % |  xxxxxxx   Mpps     |
   +-----------+------------+---------+-------------+---------+---------------------+
   |  1C/2T    |    64      |   512   |  xxxxx Mpps |   xxx % |  xxxxxxx   Mpps     |
   +-----------+------------+---------+-------------+---------+---------------------+
   |  1C/2T    |    64      |   2048  |  xxxxx Mpps |   xxx % |  xxxxxxx   Mpps     |
   +-----------+------------+---------+-------------+---------+---------------------+

  Check throughput and compare it with the expected value. Case will raise failure 
  if actual throughputs have more than 1Mpps gap from expected ones.

Note : 
   The values for the expected throughput may vary due to different platform and OS, 
   and traffic generator, please correct threshold values accordingly. 
