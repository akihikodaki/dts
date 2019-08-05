.. Copyright (c) <2017-2019>, Intel Corporation
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

Assume PF port PCI addresses is 0000:04:00.0, their
Interfaces name is p786p0. Assume generated VF PCI address will
be 0000:04:10.0.

Iommu pass through feature has been enabled in kernel::

    intel_iommu=on iommu=pt

Modify the DPDK-l3fwd-power source code and recompile the l3fwd-power::

    sed -i -e '/DEV_RX_OFFLOAD_CHECKSUM,/d' ./examples/l3fwd-power/main.c

    export RTE_TARGET=x86_64-native-linuxapp-gcc
    export RTE_SDK=`/root/DPDK`
    make -C examples/l3fwd-power

Support igb_uio and vfio driver, if used vfio, kernel need 3.6+ and enable vt-d
in bios. When used vfio, requested to insmod two drivers vfio and vfio-pci.

Test Case1: Check Interrupt for PF with vfio driver on ixgbe and i40e
=====================================================================

1. Bind NIC PF to igb_uio drvier::

    modprobe vfio-pci;

    usertools/dpdk-devbind.py --bind=igb-uio 0000:04:00.0

2. start l3fwd-power with PF::

    examples/l3fwd-power/build/l3fwd-power -l 1-3 -n 4 -- -P -p 0x01  --config '(0,0,2)'

3. Send packet with packet generator to the pf NIC, check that thread core2 waked up::

    sendp([Ether(dst='pf_mac')/IP()/UDP()/Raw(load='XXXXXXXXXXXXXXXXXX')], iface="tester_intf")

    L3FWD_POWER: lcore 2 is waked up from rx interrupt on port 0 queue 0

4. Check if threads on core 2 have returned to sleep mode::

    L3FWD_POWER: lcore 2 sleeps until interrupt triggers

Test Case2: Check Interrupt for PF with igb_uio driver on ixgbe and i40e
========================================================================

1. Bind NIC PF to igb_uio drvier::

    modprobe uio;
    insmod x86_64-native-linuxapp-gcc/kmod/igb_uio.ko;

    usertools/dpdk-devbind.py --bind=vfio-pci 0000:04:00.0

2. start l3fwd-power with PF::

    examples/l3fwd-power/build/l3fwd-power -l 1-3 -n 4 -- -P -p 0x01  --config '(0,0,2)'

3. Send packet with packet generator to the pf NIC, check that thread core2 waked up::

    sendp([Ether(dst='pf_mac')/IP()/UDP()/Raw(load='XXXXXXXXXXXXXXXXXX')], iface="tester_intf")

    L3FWD_POWER: lcore 2 is waked up from rx interrupt on port 0 queue 0

4. Check if threads on core 2 have returned to sleep mode::

    L3FWD_POWER: lcore 2 sleeps until interrupt triggers

Test Case3: Check Interrupt for VF with vfio driver on ixgbe and i40e
=====================================================================

1. Generate NIC VF, then bind it to vfio drvier::

    echo 1 > /sys/bus/pci/devices/0000\:04\:00.0/sriov_numvfs

    modprobe vfio-pci
    usertools/dpdk-devbind.py --bind=vfio-pci 0000:04:10.0(vf_pci)

  Notice:  If your PF is kernel driver, make sure PF link is up when your start testpmd on VF.

2. Start l3fwd-power with VF::

    examples/l3fwd-power/build/l3fwd-power -l 1-3 -n 4 -- -P -p 0x01  --config '(0,0,2)'

3. Send packet with packet generator to the pf NIC, check that thread core2 waked up::

    sendp([Ether(dst='vf_mac')/IP()/UDP()/Raw(load='XXXXXXXXXXXXXXXXXX')], iface="tester_intf")

    L3FWD_POWER: lcore 2 is waked up from rx interrupt on port 0 queue 0

4. Check if threads on core 2 have returned to sleep mode::

    L3FWD_POWER: lcore 2 sleeps until interrupt triggers
