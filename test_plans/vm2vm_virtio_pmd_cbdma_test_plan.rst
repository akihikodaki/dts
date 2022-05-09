.. Copyright (c) <2022>, Intel Corporation
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

================================================
vm2vm vhost-user/virtio-pmd with cbdma test plan
================================================

Description
===========

Vhost asynchronous data path leverages DMA devices to offload memory copies from the CPU and it is implemented in an asynchronous way.
In addition, vhost supports M:N mapping between vrings and DMA virtual channels. Specifically, one vring can use multiple different DMA
channels and one DMA channel can be shared by multiple vrings at the same time. Vhost enqueue operation with CBDMA channels is supported
in both split and packed ring.

This document provides the test plan for testing some basic functions with CBDMA device in vm2vm vhost-user/virtio-pmd topology environment.
1. vm2vm mergeable, normal path test with virtio 1.0 and virtio 1.1
2. vm2vm mergeable path test with virtio 1.0 and dynamic change queue number.

Note:
1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > 5.1, and packed ring multi-queues not support reconnect in qemu yet.
2.For split virtqueue virtio-net with multi-queues server mode test, need qemu version >= 5.2.0, dut to old qemu exist reconnect issue when multi-queues test.
3.When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
exceed IOMMU's max capability, better to use 1G guest hugepage.
4.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

For more about dpdk-testpmd sample, please refer to the DPDK docments:
https://doc.dpdk.org/guides/testpmd_app_ug/run_app.html
For more about qemu, you can refer to the qemu doc: https://qemu-project.gitlab.io/qemu/system/invocation.html

Prerequisites
=============

Topology
--------
      Test flow: Virtio-pmd-->Vhost-user-->Testpmd-->Vhost-user-->Virtio-pmd

Software
--------
      Trex:http://trex-tgn.cisco.com/trex/release/v2.26.tar.gz

General set up
--------------
1. Compile DPDK::

      # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=<dpdk build dir>
      # ninja -C <dpdk build dir> -j 110
      For example:
      CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=x86_64-native-linuxapp-gcc
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

Common steps
------------
1. Bind 1 NIC port and CBDMA channels to vfio-pci::

      <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
      <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DMA device id>

      For example, Bind 1 NIC port and 2 CBDMA channels::
      <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:18.0
      <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:04.0,0000:00:04.1

2. On VM1 and VM2, bind virtio device(for example,0000:00:05.0) with vfio-pci driver::

    modprobe vfio
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    <dpdk dir># ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

Test Case 1: VM2VM virtio-pmd split ring mergeable path 8 queues CBDMA enable with server mode stable test
----------------------------------------------------------------------------------------------------------
This case uses testpmd and QEMU to test split ring mergeable path with 8 queues and CBDMA enable with server mode,
In VM, use testpmd to send imix packets, and relaunch vhost-user 10 times to test stable.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch the testpmd with 2 vhost port and 8 queues by below commands::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
    -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    -a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
    --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
    --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
    -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
    --lcore-dma=[lcore2@0000:00:04.0,lcore2@0000:00:04.1,lcore2@0000:00:04.2,lcore2@0000:00:04.3,lcore3@0000:00:04.4,lcore3@0000:00:04.5,lcore3@0000:00:04.6,lcore3@0000:00:04.7,\
    lcore4@0000:80:04.0,lcore4@0000:80:04.1,lcore4@0000:80:04.2,lcore4@0000:80:04.3,lcore5@0000:80:04.4,lcore5@0000:80:04.5,lcore5@0000:80:04.6,lcore5@0000:80:04.7]
    testpmd> start

3. Launch VM1 and VM2 using qemu::

    taskset -c 6-16 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,\
    mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

    taskset -c 17-27 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,\
    vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1 and VM2, bind virtio device with vfio-pci driver, as common step 2.

5. Launch testpmd in VM1::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip \
    --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd> set fwd mac
    testpmd> start

6. Launch testpmd in VM2, sent imix pkts from VM2::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip \
    --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd> set fwd mac
    testpmd> set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
    testpmd> start tx_first 1

7. Check imix packets can looped between two VMs and 8 queues all have packets rx/tx::

    testpmd> show port stats all
    testpmd> stop

8. Relaunch and start vhost side testpmd with below cmd::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
    -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    -a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
    --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
    --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
    -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
    --lcore-dma=[lcore2@0000:00:04.0,lcore2@0000:00:04.1,lcore2@0000:00:04.2,lcore2@0000:00:04.3,lcore3@0000:00:04.4,lcore3@0000:00:04.5,lcore3@0000:00:04.6,lcore3@0000:00:04.7,\
    lcore4@0000:80:04.0,lcore4@0000:80:04.1,lcore4@0000:80:04.2,lcore4@0000:80:04.3,lcore5@0000:80:04.4,lcore5@0000:80:04.5,lcore5@0000:80:04.6,lcore5@0000:80:04.7]
    testpmd> start

9. Send pkts by testpmd in VM2, check imix packets can looped between two VMs and 8 queues all have packets rx/tx::

    testpmd> stop
    testpmd> start tx_first 1
    testpmd> show port stats all
    testpmd> stop

10. Rerun step 7-8 for 10 times.

Test Case 2: VM2VM virtio-pmd split ring mergeable path dynamic queue size CBDMA enable with server mode test
-------------------------------------------------------------------------------------------------------------
This case uses testpmd and QEMU to test split ring mergeable path and CBDMA enable with server mode,
In VM, use testpmd to send imix packets, and then dynamic queue size from 4 to 8 to test it works well or not.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch the testpmd with 2 vhost ports below commands::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
    -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    -a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
    --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3]' \
    --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3]' \
    -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4 \
    --lcore-dma=[lcore2@0000:00:04.0,lcore2@0000:00:04.1,lcore2@0000:00:04.2,lcore2@0000:00:04.3,lcore3@0000:00:04.4,lcore3@0000:00:04.5,lcore3@0000:00:04.6,lcore3@0000:00:04.7,\
    lcore4@0000:80:04.0,lcore4@0000:80:04.1,lcore4@0000:80:04.2,lcore4@0000:80:04.3,lcore5@0000:80:04.4,lcore5@0000:80:04.5,lcore5@0000:80:04.6,lcore5@0000:80:04.7]
    testpmd> start

3. Launch VM1 and VM2 using qemu::

    taskset -c 6-16 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,\
    mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

    taskset -c 17-27 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,\
    vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1 and VM2, bind virtio device with vfio-pci driver, as common step 2.

5. Launch testpmd in VM1::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip \
    --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd> set fwd mac
    testpmd> start

6. Launch testpmd in VM2, sent imix pkts from VM2::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip \
    --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd> set fwd mac
    testpmd> set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
    testpmd> start tx_first 1

7. Check imix packets can looped between two VMs and  4 queues (queue0 to queue3) have packets rx/tx::

    testpmd> show port stats all
    testpmd> stop

8. Relaunch and start vhost side testpmd with 8 queues::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
    -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    -a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
    --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
    --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
    -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
    --lcore-dma=[lcore2@0000:00:04.0,lcore2@0000:00:04.1,lcore2@0000:00:04.2,lcore2@0000:00:04.3,lcore3@0000:00:04.4,lcore3@0000:00:04.5,lcore3@0000:00:04.6,lcore3@0000:00:04.7,\
    lcore4@0000:80:04.0,lcore4@0000:80:04.1,lcore4@0000:80:04.2,lcore4@0000:80:04.3,lcore5@0000:80:04.4,lcore5@0000:80:04.5,lcore5@0000:80:04.6,lcore5@0000:80:04.7]
    testpmd> start

9. Send pkts by testpmd in VM2, check imix packets can looped between two VMs and 8 queues all have packets rx/tx::

    testpmd> stop
    testpmd> start tx_first 1
    testpmd> show port stats all
    testpmd> stop

10. Rerun step 7-8 for 10 times.

Test Case 3: VM2VM virtio-pmd packed ring mergeable path 8 queues CBDMA enable test
-----------------------------------------------------------------------------------
This case uses testpmd and QEMU to test packed ring mergeable path with 8 queues and CBDMA enable,
In VM, use testpmd to send imix packets, and then quit VM1 and change VM1 from packed ring path to splirt ring path to test.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch the testpmd with 2 vhost port and 8 queues by below commands::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost  \
    -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    -a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
    --vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
    --vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]'  \
    -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
    --lcore-dma=[lcore2@0000:00:04.0,lcore2@0000:00:04.1,lcore2@0000:00:04.2,lcore2@0000:00:04.3,lcore3@0000:00:04.4,lcore3@0000:00:04.5,lcore3@0000:00:04.6,lcore3@0000:00:04.7,\
    lcore4@0000:80:04.0,lcore4@0000:80:04.1,lcore4@0000:80:04.2,lcore4@0000:80:04.3,lcore5@0000:80:04.4,lcore5@0000:80:04.5,lcore5@0000:80:04.6,lcore5@0000:80:04.7]
    testpmd> start

3. Launch VM1 and VM2 with qemu::

    taskset -c 6-16 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,\
    mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

    taskset -c 17-27 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,\
    vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1 and VM2, bind virtio device with vfio-pci driver, as common step 2.

5. Launch testpmd in VM1::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip \
    --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd> set fwd mac
    testpmd> start

6. Launch testpmd in VM2, sent imix pkts from VM2::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip \
    --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd> set fwd mac
    testpmd> set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
    testpmd> start tx_first 1

7. Check imix packets can looped between two VMs and 8 queues all have packets rx/tx::

    testpmd> show port stats all
    testpmd> stop

8. Quit VM2 and relaunch VM2 with split ring::

    taskset -c 6-16 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,\
    mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

9. Bind virtio device with vfio-pci driver::

    modprobe vfio
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    <dpdk dir># ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

10. Launch testpmd in VM2 and send imix pkts from VM2::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip \
	--txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
	testpmd> set fwd mac
	testpmd> set txpkts 64,256,512,1024,2000,64,256,512,1024,2000

11. Check imix packets can looped between two VMs and 8 queues all have packets rx/tx::

	testpmd> show port stats all
	testpmd> stop