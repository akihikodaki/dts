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

- Hardware maximum queues
    The datasheet xl710-10-40-controller-datasheet2017.pdf described in page 10:
    "The 710 series supports up to 1536 LQPs that can be assigned to PFs or VFs as needed".

    For four ports Fortville NIC, each port has 384 queues,
    the total queues number is 384 * 4 = 1536.
    For two ports Fortville NIC, each port has 768 queues,
    the total queues number is 768 * 2 = 1536.

- Queues PF used
    According to the i40e driver source code, it will alloc 1 queue for FDIR function,
    and alloc 64 queues for PF(each PF support up to 64 queues) at the initialization period.
    So PF will use 64 + 1 = 65 queues.

- Reserved queues per VF
    The firmware will reserve 4 queues for each vf as default, when requested queues exceed 4,
    it need to realloc queues in the left queues, the reserved queues generally can't be reused.

- Max Reserved queues per VF
    The reserved queues can be modified by testpmd parameter "queue-num-per-vf".
    VF queue number must be power of 2 and equal or less than 16.

    Four ports NIC can create 32 vfs per PF, max reserved queues per VF = (384 - 65) / 32 = 9.96875,
    so max value can been set is queue-num-per-vf=8.
    Two ports NIC can create 64 vfs per PF, max reserved queues per VF = (768- 65) / 64 = 10.984375,
    so max value can been set is queue-num-per-vf=8.


Prerequisites
=============

1. Hardware:

- Fortville(X710/XXV710/XL710)

2. Software:

- dpdk: http://dpdk.org/git/dpdk (version: 19.02+)
- scapy: http://www.secdev.org/projects/scapy/

3. Scenario:
   DPDK PF + DPDK VF

Set up scenario
===============

1. Set up max VFs from one PF with DPDK driver
   Create 32 vfs on four ports fortville NIC::

    echo 32 > /sys/bus/pci/devices/0000\:05\:00.0/max_vfs

   Create 64 vfs on two ports fortville NIC::

    echo 64 > /sys/bus/pci/devices/0000\:05\:00.0/max_vfs

   Bind the two of the VFs to DPDK driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 05:02.0 05:05.7



Test case 1:  VF consume max queue number on one PF port
================================================================
1. Start the PF testpmd::

    ./<build_target>/app/dpdk-testpmd -c f -n 4 -a 05:00.0 --file-prefix=test1 \
    --socket-mem 1024,1024 -- -i

2. Start the two testpmd to consume maximum queues::
   Set '--rxq=16 --txq=16' for the first testpmd,
   So four ports NIC can start (384 - 65 - 32 * 4)/16 = int(11.9375) = 11 VFs on one PF,
   the left queues are 384 - 65 - 32 * 4 - 11 * 16 = 15.
   two ports NIC can start (768 - 65 - 64 * 4)/16 = int(27.9375) = 27 VFS on one PF,
   the left queues are 768 - 65 - 64 * 4 - 27 * 16 = 15.
   The driver will alloc queues as power of 2, and queue must be equal or less than 16,
   so the second VF testpmd can only start '--rxq=8 --txq=8'::

    ./<build_target>/app/dpdk-testpmd -c 0xf0 -n 4 -a 05:02.0 -a 05:02.1 -a 05:02.2 -a... --file-prefix=test2 \
    --socket-mem 1024,1024 -- -i --rxq=16 --txq=16

    ./<build_target>/app/dpdk-testpmd -c 0xf00 -n 4 -a 05:05.7 --file-prefix=test3 \
    --socket-mem 1024,1024 -- -i --rxq=8 --txq=8

   Check the Max possible RX queues and TX queues of the two VFs are both 16::

    testpmd> show port info all
    Max possible RX queues: 16
    Max possible TX queues: 16

   Start forwarding, you can see the actual queue number
   VF0::

    testpmd> start
    RX queues=16 - RX desc=128 - RX free threshold=32
    TX queues=16 - TX desc=512 - TX free threshold=32

   VF1::

    testpmd> start
    RX queues=8 - RX desc=128 - RX free threshold=32
    TX queues=8 - TX desc=512 - TX free threshold=32

3. Send 256 packets to VF0 and VF1, make sure packets can be distributed
   to all the queues.

Test case 2: set max queue number per vf on one pf port
================================================================
1. Start the PF testpmd with VF max queue number 16::
   As the feature description describe, the max value of queue-num-per-vf is 8
   for Both two and four ports Fortville NIC::

    ./<build_target>/app/dpdk-testpmd -c f -n 4 -a 05:00.0,queue-num-per-vf=16 --file-prefix=test1 \
    --socket-mem 1024,1024 -- -i

    PF port failed to started with "i40e_pf_parameter_init():
    Failed to allocate 577 queues, which exceeds the hardware maximum 384"
    If create 64 vfs, the maximum is 768.


   The testpmd should not crash.

