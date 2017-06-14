.. Copyright (c) <2017>, Intel Corporation
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
   ARISING IN ANY WAY OUT OF THE USE OF TH

==============================
VF One-shot Rx Interrupt Tests
==============================

One-shot Rx interrupt feature will split rx interrupt handling from other
interrupts like LSC interrupt. It implemented one handling mechanism to
eliminate non-deterministic DPDK polling thread wakeup latency.

VFIO' multiple interrupt vectors support mechanism to enable multiple event fds
serving per Rx queue interrupt handling.
UIO has limited interrupt support, specifically it only support a single
interrupt vector, which is not suitable for enabling multi queues Rx/Tx
interrupt.

Prerequisites
=============

Each of the 10Gb Ethernet* ports of the DUT is directly connected in
full-duplex to a different port of the peer traffic generator.

Assume PF port PCI addresses are 0000:04:00.0 and 0000:04:00.1, their
Interfaces name are p786p1 and p786p2. Assume generated VF PCI address will
be 0000:04:10.0, 0000:04:10.1.

Iommu pass through feature has been enabled in kernel::

   intel_iommu=on iommu=pt

Support igb_uio and vfio driver, if used vfio, kernel need 3.6+ and enable vt-d
in bios. When used vfio, requested to insmod two drivers vfio and vfio-pci.

Test Case1: VF interrupt pmd in VM with uio
===========================================

Create one VF per Port in host and add these two VFs into VM::


   usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:04:00.0 0000:04:00.1
        echo 1 >/sys/bus/pci/devices/0000\:04\:00.0/max_vfs
        echo 1 >/sys/bus/pci/devices/0000\:04\:00.1/max_vfs
        usertools/dpdk-devbind.py --force --bind=pci-stub 0000:04:10.0 0000:04:10.1

Start VM and start l3fwd-power with one queue per port in VM::


   l3fwd-power -c 7 -n 4 -- -p 0x3 -P --config="(0,0,1),(1,0,2)"

Send one packet to VF0 and VF1, check that thread on core1 and core2 waked up::


   L3FWD_POWER: lcore 1 is waked up from rx interrupt on port1,rxq0
   L3FWD_POWER: lcore 2 is waked up from rx interrupt on port1,rxq0

Check the packet has been normally forwarded.

After the packet forwarded, thread on core1 and core 2 will return to sleep::

   L3FWD_POWER: lcore 1 sleeps until interrupt on port0,rxq0 triggers
   L3FWD_POWER: lcore 2 sleeps until interrupt on port0,rxq0 triggers

Send packet flows to VF0 and VF1, check that thread on core1 and core2 will
keep up awake.

Test Case2: VF interrupt pmd in Host with uio
=============================================

Create one VF per Port in host and make sure PF interface up
uses kernel driver to create vf::


        echo 1 >/sys/bus/pci/devices/0000\:04\:00.1/sriov_numvf
        echo 1 >/sys/bus/pci/devices/0000\:04\:00.1/sriov_numvf

Bind VF device to igb_uio::


   ./usertools/dpdk-devbind.py --bind=igb_uio 0000:04:10.0 0000:04:10.1

Start host and start l3fwd-power with one queue per port in host::


   l3fwd-power -c 7 -n 4 -- -p 0x3 -P --config="(0,0,1),(1,0,2)"

Send one packet to VF0 and VF1, check that thread on core1 and core2 waked up::


   L3FWD_POWER: lcore 1 is waked up from rx interrupt on port1,rxq0
   L3FWD_POWER: lcore 2 is waked up from rx interrupt on port1,rxq0

Check the packet has been normally forwarded.

After the packet forwarded, thread on core1 and core 2 will return to sleep::

   L3FWD_POWER: lcore 1 sleeps until interrupt on port0,rxq0 triggers
   L3FWD_POWER: lcore 2 sleeps until interrupt on port0,rxq0 triggers

Send packet flows to VF0 and VF1, check that thread on core1 and core2 will
keep up awake.

Test Case3: VF interrupt pmd in Host with vfio
==============================================

Create one VF per Port in host and make sure PF interface up
uses kernel driver to create vf::


        echo 1 >/sys/bus/pci/devices/0000\:04\:00.1/sriov_numvf
        echo 1 >/sys/bus/pci/devices/0000\:04\:00.1/sriov_numvf

Bind VF device to host igb_uio::


   ./usertools/dpdk-devbind.py --bind=vfio-pci 0000:04:10.0 0000:04:10.1

Start VM and start l3fwd-power with two queues per port in VM::


   l3fwd-power -c 1f -n 4 -- -p 0x3 -P \
      --config="(0,0,1),(0,1,2)(1,0,3),(1,1,4)"

Send packets with increased dest IP to Port0 and Port1, check that thread on
core1,core2,core3,core4 waked up::

   L3FWD_POWER: lcore 1 is waked up from rx interrupt on port1,rxq0
   L3FWD_POWER: lcore 2 is waked up from rx interrupt on port1,rxq1
   L3FWD_POWER: lcore 3 is waked up from rx interrupt on port1,rxq0
   L3FWD_POWER: lcore 4 is waked up from rx interrupt on port1,rxq1

Check the packet has been normally forwarded.

After the packet forwarded, thread on core1,core2,core3,core4 will return to
sleep::

   L3FWD_POWER: lcore 1 sleeps until interrupt on port0,rxq0 triggers
   L3FWD_POWER: lcore 2 sleeps until interrupt on port0,rxq1 triggers
   L3FWD_POWER: lcore 3 sleeps until interrupt on port1,rxq0 triggers
   L3FWD_POWER: lcore 4 sleeps until interrupt on port1,rxq1 triggers

Send packet flows to Port0 and Port1, check that thread on core1,core2,core3,
core4 will keep up awake.
