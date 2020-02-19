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

1. Bind NIC PF to vfio-pci drvier::

    modprobe vfio-pci;

    usertools/dpdk-devbind.py --bind=vfio-pci 0000:04:00.0

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

    usertools/dpdk-devbind.py --bind=igb_uio 0000:04:00.0

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

Test Case4: VF interrupt pmd in VM with vfio-pci
================================================

1. Generate NIC VF, then bind it to vfio drvier::

    echo 1 > /sys/bus/pci/devices/0000\:04\:00.0/sriov_numvfs

    modprobe vfio-pci
    usertools/dpdk-devbind.py --bind=vfio-pci 0000:04:10.0(vf_pci)

2. passthrough VF 0 to VM0 and start VM0::

    taskset -c 4,5,6,7 qemu-system-x86_64 \
    -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
    -device e1000,netdev=nttsip1  -netdev user,id=nttsip1,hostfwd=tcp:10.240.176.207:6000-:22 \
    -device vfio-pci,host=0000:04:02.0,id=pt_0 -cpu host -smp 4 -m 10240 \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :11 \
    -drive file=/home/image/ubuntu16-0.img,format=qcow2,if=virtio,index=0,media=disk

3. Modify the DPDK-l3fwd-power source code and recompile the l3fwd-power::

    sed -i -e '/DEV_RX_OFFLOAD_CHECKSUM,/d' ./examples/l3fwd-power/main.c

    export RTE_TARGET=x86_64-native-linuxapp-gcc
    export RTE_SDK=`/root/DPDK`
    make -C examples/l3fwd-power

4. Bind VF 0 to the vfio-pci driver::

    modprobe -r vfio_iommu_type1
    modprobe -r vfio
    modprobe vfio enable_unsafe_noiommu_mode=1
    modprobe vfio-pci

    usertools/dpdk-devbind.py -b vfio-pci 0000:00:04.0

5. start l3fwd-power in VM::

    examples/l3fwd-power/build/l3fwd-power -l 1-3 -n 4 -- -P -p 0x01  --config '(0,0,2)'

6. Send packet with packet generator to the VM, check that thread core2 waked up::

    sendp([Ether(dst='vf_mac')/IP()/UDP()/Raw(load='XXXXXXXXXXXXXXXXXX')], iface="tester_intf")

    L3FWD_POWER: lcore 2 is waked up from rx interrupt on port 0 queue 0

7. Check if threads on core 2 have returned to sleep mode::

    L3FWD_POWER: lcore 2 sleeps until interrupt triggers

Test Case5: vf multi-queue interrupt with vfio-pci on i40e 
==========================================================

1. Generate NIC VF, then bind it to vfio drvier::

    echo 1 > /sys/bus/pci/devices/0000\:04\:00.0/sriov_numvfs
    modprobe vfio-pci
    usertools/dpdk-devbind.py --bind=vfio-pci 0000:04:10.0(vf_pci)

  Notice:  If your PF is kernel driver, make sure PF link is up when your start testpmd on VF.

2. Start l3fwd-power with VF::

    examples/l3fwd-power/build/l3fwd-power -c 3f -n 4 -m 2048 -- -P -p 0x1 --config="(0,0,1),(0,1,2),(0,2,3),(0,3,4)"

3. Send UDP packets with random ip and dest mac = vf mac addr::

      for x in range(0,10):
       sendp(Ether(src="00:00:00:00:01:00",dst="vf_mac")/IP(src='2.1.1.' + str(x),dst='2.1.1.5')/UDP()/"Hello!0",iface="tester_intf")

4. Check if threads on all cores have waked up::

    L3FWD_POWER: lcore 1 is waked up from rx interrupt on port 0 queue 0
    L3FWD_POWER: lcore 2 is waked up from rx interrupt on port 0 queue 1
    L3FWD_POWER: lcore 3 is waked up from rx interrupt on port 0 queue 2
    L3FWD_POWER: lcore 4 is waked up from rx interrupt on port 0 queue 3

Test Case6: VF multi-queue interrupt in VM with vfio-pci on i40e
================================================================
    
1. Generate NIC VF, then bind it to vfio drvier::

    echo 1 > /sys/bus/pci/devices/0000\:88:00.1/sriov_numvfs
    modprobe vfio-pci
    usertools/dpdk-devbind.py --bind=vfio-pci 0000:88:0a.0(vf_pci)

  Notice:  If your PF is kernel driver, make sure PF link is up when your start testpmd on VF.

2. Passthrough VF 0 to VM0 and start VM0::

    taskset -c 4,5,6,7,8 qemu-system-x86_64 \
    -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
    -device e1000,netdev=nttsip1  -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 \
    -device vfio-pci,host=0000:88:0a.0,id=pt_0 -cpu host -smp 5 -m 10240 \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :11 \
    -drive file=/home/osimg/noiommu-ubt16.img,format=qcow2,if=virtio,index=0,media=disk

  Notice: VM needs Kernel version > 4.8.0, mostly linux distribution don't support vfio-noiommu mode by default, so testing this case need rebuild kernel to enable vfio-noiommu.

3. Bind VF 0 to the vfio-pci driver::

    modprobe -r vfio_iommu_type1
    modprobe -r vfio
    modprobe vfio enable_unsafe_noiommu_mode=1
    modprobe vfio-pci
    usertools/dpdk-devbind.py -b vfio-pci 0000:00:04.0

4.Start l3fwd-power in VM::

    ./build/l3fwd-power -l 0-3 -n 4 -m 2048 -- -P -p 0x1 --config="(0,0,0),(0,1,1),(0,2,2),(0,3,3)"

5. Send UDP packets with random ip and dest mac = vf mac addr::

    for x in range(0,10):
     sendp(Ether(src="00:00:00:00:01:00",dst="vf_mac")/IP(src='2.1.1.' + str(x),dst='2.1.1.5')/UDP()/"Hello!0",iface="tester_intf")

6. Check if threads on core 0 to core 3 can be waked up in VM::

    L3FWD_POWER: lcore 0 is waked up from rx interrupt on port 0 queue 0
    L3FWD_POWER: lcore 1 is waked up from rx interrupt on port 0 queue 1
    L3FWD_POWER: lcore 2 is waked up from rx interrupt on port 0 queue 2
    L3FWD_POWER: lcore 3 is waked up from rx interrupt on port 0 queue 3