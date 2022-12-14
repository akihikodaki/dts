.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

================================================
vm2vm vhost-user/virtio-pmd with cbdma test plan
================================================

Description
===========

Vhost asynchronous data path leverages DMA devices to offload memory copies from the CPU and it is implemented in an asynchronous way.
In addition, vhost supports M:N mapping between vrings and DMA virtual channels. Specifically, one vring can use multiple different DMA
channels and one DMA channel can be shared by multiple vrings at the same time. From DPDK22.07, Vhost enqueue and dequeue operation with
CBDMA channels is supported in both split and packed ring.

This document provides the test plan for testing some basic functions with CBDMA channels in vm2vm vhost-user/virtio-pmd topology environment.
1. vm2vm mergeable, non-mergebale path test with virtio 1.0 and virtio1.1 and check virtio-pmd tx chain packets in mergeable path.
2. dynamic change queue number.

.. note::

   1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > 5.1, and packed ring multi-queues not support reconnect in qemu yet.
   2.For split virtqueue virtio-net with multi-queues server mode test, better to use qemu version >= 5.2.0, dut to qemu(v4.2.0~v5.1.0) exist split ring multi-queues reconnection issue.
   3.When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
   exceed IOMMU's max capability, better to use 1G guest hugepage.
   4.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd. In this patch,
   we enable asynchronous data path for vhostpmd. Asynchronous data path is enabled per tx/rx queue, and users need to specify
   the DMA device used by the tx/rx queue. Each tx/rx queue only supports to use one DMA device (This is limited by the
   implementation of vhostpmd), but one DMA device can be shared among multiple tx/rx queues of different vhost PMD ports.

Two PMD parameters are added:
- dmas:	specify the used DMA device for a tx/rx queue.(Default: no queues enable asynchronous data path)
- dma-ring-size: DMA ring size.(Default: 4096).

Here is an example:
--vdev 'eth_vhost0,iface=./s0,dmas=[txq0@0000:00.01.0;rxq0@0000:00.01.1],dma-ring-size=2048'

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
    qemu: https://download.qemu.org/qemu-7.1.0.tar.xz

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

Common steps
------------
1. Bind 1 NIC port and CBDMA channels to vfio-pci::

      <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
      <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DMA device id>

      For example, Bind 1 NIC port and 2 CBDMA channels::
      <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:18.0
      <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:04.0 0000:00:04.1

2. On VM1 and VM2, bind virtio device(for example,0000:00:05.0) with vfio-pci driver::

      modprobe vfio
      modprobe vfio-pci
      echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
      <dpdk dir># ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

Test Case 1: VM2VM virtio-pmd split ring mergeable path dynamic queue size with cbdma enable and server mode
------------------------------------------------------------------------------------------------------------
This case tests split ring mergeable path in VM2VM vhost-user/virtio-pmd topology when vhost uses the asynchronous
operations with CBDMA channels, check that it can work normally after dynamically changing queue number, reconnection has also been tested.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch the testpmd with 2 vhost ports below commands::

      <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
      -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 \
      --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.1;txq3@0000:00:04.1;rxq0@0000:00:04.0;rxq1@0000:00:04.0;rxq2@0000:00:04.1;rxq3@0000:00:04.1]' \
      --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.2;txq2@0000:00:04.3;txq3@0000:00:04.3;rxq0@0000:00:04.2;rxq1@0000:00:04.2;rxq2@0000:00:04.3;rxq3@0000:00:04.3]' \
      -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4
      testpmd> start

3. Launch VM1 and VM2 using qemu::

      taskset -c 6-16 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
      -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
      -n uma node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
      -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
      -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
      -monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
      -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
      -chardev socket,id=char0,path=./vhost-net0,server \
      -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
      -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

      taskset -c 17-27 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
      -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
      -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
      -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
      -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
      -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
      -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
      -chardev socket,id=char0,path=./vhost-net1,server \
      -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
      -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1 and VM2, bind virtio device with vfio-pci driver::

      modprobe vfio
      modprobe vfio-pci
      echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
      ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

5. Launch testpmd in VM1::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
      testpmd> set fwd mac
      testpmd> start

6. Launch testpmd in VM2 and send imix packets, check imix packets can loop between two VMs for 1 mins and 4 queues (queue0 to queue3) have packets rx/tx::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
      testpmd> set fwd mac
      testpmd> set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
      testpmd> start tx_first 32
      testpmd> show port stats all

7. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

      perf top

8. On host, dynamic change queue numbers::

      testpmd> stop
      testpmd> port stop all
      testpmd> port config all rxq 8
      testpmd> port config all txq 8
      testpmd> port start all
      testpmd> start

9. Send packets by testpmd in VM2::

      testpmd> stop
      testpmd> start tx_first 32
      testpmd> show port stats all

10. Check vhost testpmd RX/TX can work normally, packets can loop between two VMs and both 8 queues can RX/TX traffic.

11. Rerun step 7.

12. Relaunch and start vhost side testpmd with 8 queues::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
      -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
      -a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
      --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1;txq2@0000:00:04.2;txq3@0000:00:04.3;txq4@0000:00:04.4;txq5@0000:00:04.1;rxq2@0000:00:04.2;rxq3@0000:00:04.3;rxq4@0000:00:04.4;rxq5@0000:00:04.5;rxq6@0000:00:04.6;rxq7@0000:00:04.7]' \
      --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1;txq2@0000:80:04.2;txq3@0000:80:04.3;txq4@0000:80:04.4;txq5@0000:80:04.1;rxq2@0000:80:04.2;rxq3@0000:80:04.3;rxq4@0000:80:04.4;rxq5@0000:80:04.5;rxq6@0000:80:04.6;rxq7@0000:80:04.7]' \
      -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
      testpmd> set fwd mac
      testpmd> start

13. Send packets by testpmd in VM2, check imix packets can loop between two VMs for 1 mins and 8 queues all have packets rx/tx::

      testpmd> stop
      testpmd> start tx_first 32
      testpmd> show port stats all

14. Rerun step 12-13 for 3 times.

Test Case 2: VM2VM virtio-pmd split ring non-mergeable path dynamic queue size with cbdma enable and server mode
----------------------------------------------------------------------------------------------------------------
This case tests split ring non-mergeable path in VM2VM vhost-user/virtio-pmd topology when vhost uses the asynchronous
operations with CBDMA channels, check that it can work normally after dynamically changing queue number, reconnection has also been tested.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch the testpmd with 2 vhost ports below commands::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
      -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 \
      --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.1;txq3@0000:00:04.1;rxq0@0000:00:04.0;rxq1@0000:00:04.0;rxq2@0000:00:04.1;rxq3@0000:00:04.1]' \
      --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.1;txq3@0000:00:04.1;rxq0@0000:00:04.0;rxq1@0000:00:04.0;rxq2@0000:00:04.1;rxq3@0000:00:04.1]' \
      -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4
      testpmd> start

3. Launch VM1 and VM2 using qemu::

      taskset -c 6-16 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
      -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
      -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
      -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
      -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
      -monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
      -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
      -chardev socket,id=char0,path=./vhost-net0,server \
      -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
      -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

      taskset -c 17-27 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
      -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
      -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
      -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
      -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
      -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
      -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
      -chardev socket,id=char0,path=./vhost-net1,server \
      -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
      -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1 and VM2, bind virtio device with vfio-pci driver::

      modprobe vfio
      modprobe vfio-pci
      echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
      ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

5. Launch testpmd in VM1::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024
      testpmd> set fwd mac
      testpmd> start

6. Launch testpmd in VM2 and send imix pkts, check imix packets can loop between two VMs for 1 mins and 4 queues (queue0 to queue3) have packets rx/tx::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024
      testpmd> set fwd mac
      testpmd> set txpkts 64,256,512
      testpmd> start tx_first 32
      testpmd> show port stats all

7. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

      perf top

8. On VM1 and VM2, dynamic change queue numbers at virtio-pmd side from 8 queues to 4 queues::

      testpmd> stop
      testpmd> port stop all
      testpmd> port config all rxq 4
      testpmd> port config all txq 4
      testpmd> port start all
      testpmd> start

9. Send packets by testpmd in VM2, check Check virtio-pmd RX/TX can work normally and imix packets can loop between two VMs for 1 mins::

      testpmd> stop
      testpmd> start tx_first 32
      testpmd> show port stats all

10. Rerun step 7.

11. Stop testpmd in VM2, and check that 4 queues can RX/TX traffic.

Test Case 3: VM2VM virtio-pmd packed ring mergeable path dynamic queue size with cbdma enable and server mode
-------------------------------------------------------------------------------------------------------------
This case tests packed ring mergeable path with virtio1.1 and server mode in VM2VM vhost-user/virtio-pmd topology
when vhost uses the asynchronous operations with CBDMA channels, check that it can work normally after dynamically changing queue number.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch the testpmd with 2 vhost ports below commands::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
      -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 \
      --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.1;txq3@0000:00:04.1;rxq0@0000:00:04.0;rxq1@0000:00:04.0;rxq2@0000:00:04.1;rxq3@0000:00:04.1]' \
      --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.1;txq3@0000:00:04.1;rxq0@0000:00:04.0;rxq1@0000:00:04.0;rxq2@0000:00:04.1;rxq3@0000:00:04.1]' \
      -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4
      testpmd> set fwd mac
      testpmd> start

3. Launch VM1 and VM2 using qemu::

      taskset -c 6-16 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
      -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
      -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
      -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
      -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
      -monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
      -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
      -chardev socket,id=char0,path=./vhost-net0,server \
      -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
      -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

      taskset -c 17-27 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
      -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
      -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
      -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
      -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
      -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
      -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
      -chardev socket,id=char0,path=./vhost-net1,server \
      -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
      -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1 and VM2, bind virtio device with vfio-pci driver::

      modprobe vfio
      modprobe vfio-pci
      echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
      ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

5. Launch testpmd in VM1::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
      testpmd> set mac fwd
      testpmd> start

6. Launch testpmd in VM2 and send imix pkts, check imix packets can loop between two VMs for 1 mins and 4 queues (queue0 to queue3) have packets rx/tx::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
      testpmd> set mac fwd
      testpmd> set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
      testpmd> start tx_first 32
      testpmd> show port stats all
      testpmd> stop

7. Quit VM2 and relaunch VM2 with split ring::

      taskset -c 17-27 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
      -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
      -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
      -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
      -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
      -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
      -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
      -chardev socket,id=char0,path=./vhost-net1,server \
      -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
      -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

8. On VM2, bind virtio device with vfio-pci driver::

      modprobe vfio
      modprobe vfio-pci
      echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
      <dpdk dir># ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

9. Launch testpmd in VM2 and send imix pkts from VM2::

      <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip \
      --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
      testpmd> set fwd mac
      testpmd> set txpkts 64,256,512,1024,2000,64,256,512,1024,2000

10. Check imix packets can loop between two VMs and 4 queues all have packets rx/tx::

      testpmd> show port stats all
      testpmd> stop
      testpmd> start

11. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

      perf top

12. On host, dynamic change queue numbers::

      testpmd> stop
      testpmd> port stop all
      testpmd> port config all rxq 8
      testpmd> port config all txq 8
      testpmd> port start all
      testpmd> start

13. Send packets by testpmd in VM2::

      testpmd> stop
      testpmd> start tx_first 32
      testpmd> show port stats all

14. Check vhost testpmd RX/TX can work normally, packets can loop between two VMs and both 8 queues can RX/TX traffic.

15. Rerun step 11.

Test Case 4: VM2VM virtio-pmd packed ring non-mergeable path dynamic queue size with cbdma enable and server mode
-----------------------------------------------------------------------------------------------------------------
This case tests packed ring non-mergeable path with virtio1.1 and server mode in VM2VM vhost-user/virtio-pmd topology
when vhost uses the asynchronous operations with CBDMA channels,check that it can work normally after dynamically changing queue number.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch the testpmd with 2 vhost ports below commands::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
      -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
      -a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
      --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1;txq2@0000:00:04.2;txq3@0000:00:04.3;txq4@0000:00:04.4;txq5@0000:00:04.1;rxq2@0000:00:04.2;rxq3@0000:00:04.3;rxq4@0000:00:04.4;rxq5@0000:00:04.5;rxq6@0000:00:04.6;rxq7@0000:00:04.7]' \
      --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1;txq2@0000:80:04.2;txq3@0000:80:04.3;txq4@0000:80:04.4;txq5@0000:80:04.1;rxq2@0000:80:04.2;rxq3@0000:80:04.3;rxq4@0000:80:04.4;rxq5@0000:80:04.5;rxq6@0000:80:04.6;rxq7@0000:80:04.7]' \
      -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
      testpmd> start

3. Launch VM1 and VM2 using qemu::

      taskset -c 6-16 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
      -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
      -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
      -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
      -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
      -monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
      -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
      -chardev socket,id=char0,path=./vhost-net0,server \
      -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
      -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

      taskset -c 17-27 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
      -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
      -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
      -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
      -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
      -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
      -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
      -chardev socket,id=char0,path=./vhost-net1,server \
      -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
      -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1 and VM2, bind virtio device with vfio-pci driver::

      modprobe vfio
      modprobe vfio-pci
      echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
      ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

5. Launch testpmd in VM1::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=4 --rxq=4 --txd=1024 --rxd=1024
      testpmd> set mac fwd
      testpmd> start

6. Launch testpmd in VM2 and send imix pkts, check imix packets can loop between two VMs for 1 mins::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=4 --rxq=4 --txd=1024 --rxd=1024
      testpmd> set mac fwd
      testpmd> set txpkts 64,256,512
      testpmd> start tx_first 32
      testpmd> show port stats all

7. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

      perf top

8. On VM2, stop the testpmd, check that both 4 queues have packets rx/tx::

      testpmd> stop

9. On VM1 and VM2, dynamic change queue numbers at virtio-pmd side from 4 queues to 8 queues::

      testpmd> stop
      testpmd> port stop all
      testpmd> port config all rxq 8
      testpmd> port config all txq 8
      testpmd> port start all
      testpmd> start

10. Send packets by testpmd in VM2, check Check virtio-pmd RX/TX can work normally and imix packets can loop between two VMs for 1 mins::

      testpmd> stop
      testpmd> start tx_first 32
      testpmd> show port stats all

11. Rerun step 7.

12. Stop testpmd in VM2, and check that 4 queues can RX/TX traffic.
