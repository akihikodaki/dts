.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

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

====================================================
vhost/virtio-pmd interrupt mode with cbdma test plan
====================================================

Description
===========

Virtio-pmd interrupt need test with l3fwd-power sample, small packets send from traffic generator
to virtio-pmd side，check virtio-pmd cores can be wakeup status，and virtio-pmd cores should be
sleep status after stop sending packets from traffic generator when cbdma enable.This test plan
cover virtio 0.95, virtio 1.0 and virtio 1.1.

..Note:
1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > 5.1, and packed ring multi-queues not support reconnect in qemu yet.
2.For split virtqueue virtio-net with multi-queues server mode test, better to use qemu version >= 5.2.0, dut to qemu(v4.2.0~v5.1.0) exist split ring multi-queues reconnection issue.
3.Kernel version > 4.8.0, mostly linux distribution don't support vfio-noiommu mode by default,
so testing this case need rebuild kernel to enable vfio-noiommu.
4.When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
exceed IOMMU's max capability, better to use 1G guest hugepage.
5.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

Prerequisites
=============
Topology
--------
Test flow:TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Software
--------
    Trex:http://trex-tgn.cisco.com/trex/release/v2.26.tar.gz

General set up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110
    For example:
    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

2. Get the PCI device ID and DMA device ID of DUT, for example, 0000:18:00.0 is PCI device ID, 0000:00:04.0, 0000:00:04.1 is DMA device ID::

    <dpdk dir># ./usertools/dpdk-devbind.py -s

    Network devices using kernel driver
    ===================================
    0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci

    DMA devices using kernel driver
    ===============================
    0000:00:04.0 'Sky Lake-E CBDMA Registers 2021' drv=ioatdma unused=vfio-pci
    0000:00:04.1 'Sky Lake-E CBDMA Registers 2021' drv=ioatdma unused=vfio-pci

Test case
=========

Test Case1: Basic virtio0.95 interrupt test with 16 queues and cbdma enable
---------------------------------------------------------------------------
This case tests virtio0.95 pmd interrupt with l3fwd-power sample when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 16 cbdma channels and one NIC port to vfio-pci, then launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x1ffff -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13;txq14;txq15;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7;rxq8;rxq9;rxq10;rxq11;rxq12;rxq13;rxq14;rxq15]' \
    -- -i --nb-cores=16 --rxq=16 --txq=16 --rss-ip --lcore-dma=[lcore1@0000:00:04.0,lcore2@0000:00:04.0,lcore3@0000:00:04.1,lcore3@0000:00:04.2,lcore4@0000:00:04.3,lcore5@0000:00:04.4,lcore6@0000:00:04.5,lcore7@0000:00:04.6,lcore8@0000:00:04.7,\
	lcore9@0000:80:04.0,lcore10@0000:80:04.1,lcore11@0000:80:04.2,lcore12@0000:80:04.3,lcore13@0000:80:04.4,lcore14@0000:80:04.5,lcore15@0000:80:04.6,lcore16@0000:80:04.7]

2. Launch VM1, set queues=16, vectors>=2xqueues+2, mq=on::

    taskset -c 34-35 qemu-system-x86_64 -name us-vhost-vm2 \
    -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
    -smp cores=16,sockets=1 -drive file=/home/osimg/ubuntu1910.img \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char1,path=./vhost-net -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce,queues=16 \
    -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,disable-modern=ture,mrg_rxbuf=on,csum=on,mq=on,vectors=40  \
    -vnc :11 -daemonize

3. Bind virtio port to vfio-pci::

    modprobe vfio enable_unsafe_noiommu_mode=1
    modprobe vfio-pci
    ./usertools/dpdk-devbind.py --bind=vfio-pci xx:xx.x

4. In VM, launch l3fwd-power sample::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -c 0x0ffff -n 4 --log-level='user1,7' \
    -- -p 1 -P  --config '(0,0,0),(0,1,1),(0,2,2),(0,3,3)(0,4,4),(0,5,5),(0,6,6),(0,7,7)(0,8,8),(0,9,9),(0,10,10),(0,11,11)(0,12,12),(0,13,13),(0,14,14),(0,15,15)' \
    --no-numa  --parse-ptype

5. Send random dest IP packets to host NIC with packet generator, packets will distribute to all queues, check l3fwd-power log that all related cores are waked up.

6. Change dest IP to fixed ip, packets will distribute to 1 queue, check l3fwd-power log that only one related core is waked up.

7. Stop the date transmitter, check all related core will be back to sleep status.

Test Case2: Basic virtio-1.0 interrupt test with 4 queues and cbdma enable
--------------------------------------------------------------------------
This case tests virtio1.0 pmd interrupt with l3fwd-power sample when vhost uses the asynchronous operations with CBDMA channels.

1. Bind four cbdma channels and one NIC port to vfio-pci, then launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7c -n 4 \
    --vdev 'net_vhost0,iface=vhost-net,queues=4,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
    -- -i --nb-cores=4 --rxq=4 --txq=4 --rss-ip --lcore-dma=[lcore3@0000:00:04.0,lcore4@0000:00:04.0,lcore5@0000:00:04.0,lcore5@0000:00:04.1,lcore6@0000:00:04.1]

2. Launch VM1, set queues=4, vectors>=2xqueues+2, mq=on::

    taskset -c 34-35 \
    qemu-system-x86_64 -name us-vhost-vm2 \
    -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
    -smp cores=4,sockets=1 -drive file=/home/osimg/ubuntu1910.img \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char1,path=./vhost-net -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce,queues=4 \
    -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,disable-modern=false,mrg_rxbuf=on,csum=on,mq=on,vectors=15  \
    -vnc :11 -daemonize

3. Bind virtio port to vfio-pci::

    modprobe vfio enable_unsafe_noiommu_mode=1
    modprobe vfio-pci
    ./usertools/dpdk-devbind.py --bind=vfio-pci xx:xx.x

4. In VM, launch l3fwd-power sample::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -c 0xf -n 4 --log-level='user1,7' -- -p 1 -P --config="(0,0,0),(0,1,1),(0,2,2),(0,3,3)" --no-numa --parse-ptype

5. Send random dest IP packets to host NIC with packet generator, packets will distribute to all queues, check l3fwd-power log that all related cores are waked up.

6. Change dest IP to fixed ip, packets will distribute to 1 queue, check l3fwd-power log that only one related core is waked up.

7. Stop the date transmitter, check all related core will be back to sleep status.

Test Case3: Basic virtio-1.1 interrupt test with 16 queues and cbdma enable
-----------------------------------------------------------------------------
This case tests packed ring virtio-pmd interrupt with l3fwd-power sample when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 16 cbdma channels ports and one NIC port to vfio-pci, then launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x1ffff -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13;txq14;txq15;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7;rxq8;rxq9;rxq10;rxq11;rxq12;rxq13;rxq14;rxq15]' \
    -- -i --nb-cores=16 --rxq=16 --txq=16 --rss-ip --lcore-dma=[lcore1@0000:00:04.0,lcore2@0000:00:04.0,lcore3@0000:00:04.1,lcore3@0000:00:04.2,lcore4@0000:00:04.3,lcore5@0000:00:04.4,lcore6@0000:00:04.5,lcore7@0000:00:04.6,lcore8@0000:00:04.7,\
	lcore9@0000:80:04.0,lcore10@0000:80:04.1,lcore11@0000:80:04.2,lcore12@0000:80:04.3,lcore13@0000:80:04.4,lcore14@0000:80:04.5,lcore15@0000:80:04.6,lcore16@0000:80:04.7]

2. Launch VM1, set queues=16, vectors>=2xqueues+2, mq=on::

    taskset -c 34-35 \
    qemu-system-x86_64 -name us-vhost-vm2 \
    -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
    -smp cores=16,sockets=1 -drive file=/home/osimg/ubuntu1910.img \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char1,path=./vhost-net -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce,queues=16 \
    -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,disable-modern=false,mrg_rxbuf=on,csum=on,mq=on,vectors=40,packed=on  \
    -vnc :11 -daemonize

3. Bind virtio port to vfio-pci::

    modprobe vfio enable_unsafe_noiommu_mode=1
    modprobe vfio-pci
    ./usertools/dpdk-devbind.py --bind=vfio-pci xx:xx.x

4. In VM, launch l3fwd-power sample::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -c 0x0ffff -n 4 --log-level='user1,7' -- -p 1 -P  --config '(0,0,0),(0,1,1),(0,2,2),(0,3,3)(0,4,4),(0,5,5),(0,6,6),(0,7,7)(0,8,8),(0,9,9),(0,10,10),(0,11,11)(0,12,12),(0,13,13),(0,14,14),(0,15,15)' --no-numa  --parse-ptype

5. Send random dest IP packets to host NIC with packet generator, packets will distribute to all queues, check l3fwd-power log that all related cores are waked up.

6. Change dest IP to fixed ip, packets will distribute to 1 queue, check l3fwd-power log that only one related core is waked up.

7. Stop the date transmitter, check all related core will be back to sleep status.
