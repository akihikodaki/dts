.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2017 Intel Corporation

===========================
One-shot Rx Interrupt Tests
===========================

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

Assume PF port PCI addresses are 0000:08:00.0 and 0000:08:00.1,
their Interfaces name are p786p1 and p786p2.
Assume generated VF PCI address will be 0000:08:10.0, 0000:08:10.1.

Iommu pass through feature has been enabled in kernel::

    intel_iommu=on iommu=pt

Support igb_uio and vfio driver, if used vfio, kernel need 3.6+ and enable vt-d
in bios. When used vfio, requested to insmod two drivers vfio and vfio-pci.

Build dpdk and examples=l3fwd-power:
   CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static <build_target>
   ninja -C <build_target>

   meson configure -Dexamples=l3fwd-power <build_target>
   ninja -C <build_target>

Test Case1: PF interrupt pmd with different queue
=================================================

Run l3fwd-power with one queue per port::

    ./<build_target>/examples/dpdk-l3fwd-power -c 0x7 -n 4 -- -p 0x3 -P --config="(0,0,1),(1,0,2)"

Send one packet to Port0 and Port1, check that thread on core1 and core2
waked up::

    L3FWD_POWER: lcore 1 is waked up from rx interrupt on port1,rxq0
    L3FWD_POWER: lcore 2 is waked up from rx interrupt on port1,rxq0

Check the packet has been normally forwarded.

After the packet forwarded, thread on core1 and core 2 will return to sleep::

    L3FWD_POWER: lcore 1 sleeps until interrupt on port0,rxq0 triggers
    L3FWD_POWER: lcore 2 sleeps until interrupt on port0,rxq0 triggers

Send packet flows to Port0 and Port1, check that thread on core1 and core2 will
keep up awake.

Run l3fwd-power with random number queue per port, if is 4::

    ./<build_target>/examples/dpdk-l3fwd-power -c 0x7 -n 4 -- -p 0x3 -P --config="0,0,0),(0,1,1),\
       (0,2,2),(0,3,3),(0,4,4)"

Send packet with increased dest IP to Port0, check that all threads waked up

Send packet flows to Port0 and Port1, check that thread on core1 and core2 will
keep up awake.

Run l3fwd-power with 15 queues per port::

    ./<build_target>/examples/dpdk-l3fwd-power -c 0xffffff -n 4 -- -p 0x3 -P --config="(0,0,0),(0,1,1),\
        (0,2,2),(0,3,3),(0,4,4),(0,5,5),(0,6,6),(0,7,7),(1,0,8),\
        (1,1,9),(1,2,10),(1,3,11),(1,4,12),(1,5,13),(1,6,14)"

Send packet with increased dest IP to Port0, check that all threads waked up

igb_uio driver only uses one queue 0


Test Case2: PF lsc interrupt with vfio
======================================

Run l3fwd-power with one queue per port::

    ./<build_target>/examples/dpdk-l3fwd-power -c 0x7 -n 4 -- -p 0x3 -P --config="(0,0,1),(1,0,2)"

Plug out Port0 cable, check that link down interrupt captured and handled by
pmd driver.

Plug out Port1 cable, check that link down interrupt captured and handled by
pmd driver.

Plug in Port0 cable, check that link up interrupt captured and handled by pmd
driver.

Plug in Port1 cable, check that link up interrupt captured and handled by pmd
driver.


Test Case3: PF interrupt pmd latency test
=========================================

Setup validation scenario the case as test1
Send burst packet flow to Port0 and Port1, use IXIA capture the maximum
latency.

Compare latency(l3fwd-power PF interrupt pmd with uio) with l3fwd latency.

Setup validation scenario the case as test2
Send burst packet flow to Port0 and Port1, use IXIA capture the maximum
latency.
