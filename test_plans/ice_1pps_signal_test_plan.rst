.. Copyright (c) <2021>, Intel Corporation
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

=========================
ICE 1PPS Signal Test Plan
=========================

Description
===========
The Intel® Ethernet 800 Series supports a total of four single-ended GPIO signals(SPD[20:23])plus
one different GPIO signal (CLK_OUT_P/N), which is configured by default 1PPS(out). The SPD[20:23]
is mapping to pin_id[0:3]. This test plan is designed to check the value of related registers,
which make up the 1PPS signal. The registers address depends on some hardware config.
The test cases only give the example of E810-XXVDA4 and E810-CQ.


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
scapy: http://www.secdev.org/projects/scapy/

General set up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110

2. Get the pci device id and interface of DUT and tester.
   For example, 0000:18:00.0 and 0000:18:00.1 is pci device id,
   ens785f0 and ens785f1 is interface::

    <dpdk dir># ./usertools/dpdk-devbind.py -s

    0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci
    0000:18:00.1 'Device 159b' if=ens785f1 drv=ice unused=vfio-pci

3. Bind the DUT port to dpdk::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>


Test case
=========

Test case 1: check registers when pin id is 0
---------------------------------------------

this case is designed to check the register value is right when pin id is 0.

test steps
~~~~~~~~~~
1. start testpmd with different pin_id and dump registers::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -a <DUT port pci device id>,pps_out='[pin:0]' -- -i --rxq=4 --txq=4
    testpmd> read reg 0 0x00088998
    testpmd> read reg 0 0x000889B8
    testpmd> read reg 0 0x00088928
    testpmd> read reg 0 0x00088930
    testpmd> read reg 0 0x000880C8

2. check the GLTSYN_AUX_OUT_0[0] 0x00088998 is 0x00000007 (7), GLTSYN_CLKO_0[0] 0x000889B8 is 0x1DCD6500 (500000000), the 0x00088928 and 0x00088930 is non-zero,
   The 3rd Hexadecimal digit of GLGEN_GPIO_CTL[0] 0x000880C8 is 8. And the 5th binary digit is 1.

Test case 2: check registers when pin id is 1
---------------------------------------------

this case is designed to check the register value is right when pin id is 1.

test steps
~~~~~~~~~~
1. start testpmd with different pin_id and dump registers::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:00.0,pps_out='[pin:1]' -- -i --rxq=4 --txq=4
    testpmd> read reg 0 0x000889A0
    testpmd> read reg 0 0x000889C0
    testpmd> read reg 0 0x00088938
    testpmd> read reg 0 0x00088940
    testpmd> read reg 0 0x000880CC

2. check the GLTSYN_AUX_OUT_1[0] 0x000889A0 is 0x00000007 (7), GLTSYN_CLKO_1[0] 0x000889C0 is 0x1DCD6500 (500000000), the 0x00088938 and 0x00088940 is non-zero,
   The 3rd Hexadecimal digit of GLGEN_GPIO_CTL[1] 0x000880CC is 9. And the 5th binary digit is 1.

Test case 3: check registers when pin id is 2
---------------------------------------------

this case is designed to check the register value is right when pin id is 2.

test steps
~~~~~~~~~~
1. start testpmd with different pin_id and dump registers::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:00.0,pps_out='[pin:2]' -- -i --rxq=4 --txq=4
    testpmd> read reg 0 0x000889A8
    testpmd> read reg 0 0x000889C8
    testpmd> read reg 0 0x00088948
    testpmd> read reg 0 0x00088950
    testpmd> read reg 0 0x000880D0

2. check the GLTSYN_AUX_OUT_2[0] 0x000889A8 is 0x00000007 (7), GLTSYN_CLKO_2[0] 0x000889C8 is 0x1DCD6500 (500000000), the 0x00088948 and 0x00088950 is non-zero,
   The 3rd Hexadecimal digit of GLGEN_GPIO_CTL[2] 0x000880D0 is A. And the 5th binary digit is 1.

Test case 4: check registers when pin id is 3
---------------------------------------------

this case is designed to check the register value is right when pin id is 3.

test steps
~~~~~~~~~~
1. start testpmd with different pin_id and dump registers::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:00.0,pps_out='[pin:3]' -- -i --rxq=4 --txq=4
    testpmd> read reg 0 0x000889B0
    testpmd> read reg 0 0x000889D0
    testpmd> read reg 0 0x00088958
    testpmd> read reg 0 0x00088960
    testpmd> read reg 0 0x000880D4

2. check the GLTSYN_AUX_OUT_3[0] 0x000889B0 is 0x00000007 (7), GLTSYN_CLKO_3[0] 0x000889D0 is 0x1DCD6500 (500000000), the 0x00088958 and 0x00088960 is non-zero,
   The 3rd Hexadecimal digit of GLGEN_GPIO_CTL[3] 0x000880D4 is B. And the 5th binary digit is 1.