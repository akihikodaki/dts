.. Copyright (c) <2019>, Intel Corporation
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

==========================================
VF Request Maximum Queue Number At Runtime
==========================================

This test plan is an additional tests for VF Request Queue Number At Runtime.
In order to make testing excution efficiency, we put the test case of
maximum queue number in this plan, because of different test scenarios.

Feature Description
===================

see runtime_vf_queue_number_test_plan.rst

Prerequisites
=============

1. Hardware:

- Fortville(X710/XXV710/XL710)

2. Software:

- dpdk: http://dpdk.org/git/dpdk (version: 19.02+)
- scapy: http://www.secdev.org/projects/scapy/

3. Scenario:
   DPDK PF + DPDK VF

Test case 1: set VF max queue number with max VFs on one PF port
================================================================

1. Set up max VFs from one PF with DPDK driver
   Create 32 vfs on four ports fortville NIC::

    echo 32 > /sys/bus/pci/devices/0000\:05\:00.0/max_vfs

   Create 64 vfs on two ports fortville NIC::

    echo 64 > /sys/bus/pci/devices/0000\:05\:00.0/max_vfs

   Bind the two of the VFs to DPDK driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 05:02.0 05:05.7

2. Set VF max queue number to 16::

    ./testpmd -c f -n 4 -w 05:00.0,queue-num-per-vf=16 \
    --file-prefix=test1 --socket-mem 1024,1024 -- -i

   PF port failed to started with "i40e_pf_parameter_init():
   Failed to allocate 577 queues, which exceeds the hardware maximum 384"
   If create 64 vfs, the maximum is 768.

3. Set VF max queue number to 8::

    ./testpmd -c f -n 4 -w 05:00.0,queue-num-per-vf=8 \
    --file-prefix=test1 --socket-mem 1024,1024 -- -i

4. Start the two VFs testpmd with "--rxq=8 --txq=8" and "--rxq=6 --txq=6"::

    ./testpmd -c 0xf0 -n 4 -w 05:02.0 --file-prefix=test2 \
    --socket-mem 1024,1024 -- -i --rxq=8 --txq=8

    ./testpmd -c 0xf00 -n 4 -w 05:05.7 --file-prefix=test3 \
    --socket-mem 1024,1024 -- -i --rxq=6 --txq=6

   Check the Max possible RX queues and TX queues of the two VFs are both 8::

    testpmd> show port info all
    Max possible RX queues: 8
    Max possible TX queues: 8

   Start forwarding, you can see the actual queue number
   VF0::

    testpmd> start
    RX queues=8 - RX desc=128 - RX free threshold=32
    TX queues=8 - TX desc=512 - TX free threshold=32

   VF1::

    testpmd> start
    RX queues=6 - RX desc=128 - RX free threshold=32
    TX queues=6 - TX desc=512 - TX free threshold=32

   Modify the queue number of VF1::

    testpmd> stop
    testpmd> port stop all
    testpmd> port config all rxq 8
    testpmd> port config all txq 7
    testpmd> port start all

   Start forwarding, you can see the VF1 actual queue number is 8 and 7::

    testpmd> start
    RX queues=8 - RX desc=128 - RX free threshold=32
    TX queues=7 - TX desc=512 - TX free threshold=32

5. Send 256 packets to VF0 and VF1, make sure packets can be distributed
   to all the queues.
