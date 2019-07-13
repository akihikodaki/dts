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

===========
softnic PMD
===========

Description
===========
The SoftNIC allows building custom NIC pipelines in SW. The Soft NIC pipeline
is configurable through firmware (DPDK Packet Framework script).

Prerequisites
=============
1. The DUT must have one 10G Ethernet port connected to a port on tester
   that are controlled by the traffic generator::

    dut_port_0 <---> tester_port_0

   Assume the DUT 10G Ethernet port's pci device id is as the following::

    dut_port_0 : "0000:05:00.0"

   Bind it to dpdk igb_uio driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0

2. Change ./drivers/net/softnic/firmware.cli to meet the specific test environment.

3. Start softnic with following command line::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 \
    --vdev 'net_softnic0,firmware=./drivers/net/softnic/firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --portmask=0x2
    testpmd> start

   Set the thread id consistent to the service core::

    thread 2 pipeline PIPELINE0 enable

Test Case 1: softnic performance
================================
1. Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 \
    --vdev 'net_softnic0,firmware=./drivers/net/softnic/firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --portmask=0x2
    testpmd> start

2. Send packet at line rate from traffic generator (IXIA or other) with packet size from 64~1518B.
3. Check performance number is same as the physical NIC's performance number, no performance drop.

Test Case 2: shaping for pipe
=============================
1. The specifications of the default Hierarchical Scheduler are as follows:

    Root node (x1, level 0)
    Subport node (x1, level 1)
    Pipe node (x4096, level 2)
    Traffic Class node (x16348, level 3)
    Queue node (x65536, level 4)

2. Start softnic with the default hierarchy Qos::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 \
    --vdev 'net_softnic0,firmware=./drivers/net/softnic/tm_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --portmask=0x2
    testpmd> start

3. Send per flow traffic with 100% line rate, verify output flow rate is 1/4096 subport rate.

Test Case 3: NAT
================
1. Set SNAT with proto tcp test, edit nat_firmware.cli to change "table action" as below::

    table action profile AP0 ipv4 offset 270 fwd nat src proto tcp

(a). Start softnic::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x7 -s 0x4 -n 4 \
    --vdev 'net_softnic0,firmware=./drivers/net/softnic/nat_firmware.cli,cpu_id=1,conn_port=8086' \
    -- -i --forward-mode=softnic --portmask=0x2
    testpmd> start

(b). Sent packet, verify the received packet's ipaddr and port was changed as expected.

2. Set DNAT with proto tcp test, edit nat_firmware.cli to change "table action" as below::

    table action profile AP0 ipv4 offset 270 fwd nat dst proto tcp

   Then re-run step (a) & step (b).

3. Set SNAT with proto udp test, edit nat_firmware.cli to change "table action" as below::

    table action profile AP0 ipv4 offset 270 fwd nat src proto udp

   Then re-run step (a) & step (b).

4. Set DNAT with proto udp test, edit nat_firmware.cli to change "table action" as below::

    table action profile AP0 ipv4 offset 270 fwd nat dst proto udp

   Then re-run step (a) & step (b).
