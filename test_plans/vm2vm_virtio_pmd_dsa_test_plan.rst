.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=======================================================
vm2vm vhost-user/virtio-pmd with dsa driver test plan
=======================================================

This document provides the test plan for testing some basic functions with DSA driver(kernel IDXD driver and DPDK vfio-pci driver) 
in vm2vm vhost-user/virtio-pmd topology environment.
1. vm2vm mergeable, non-mergebale path test with virtio 1.0 and virtio1.1 and check virtio-pmd tx chain packets in mergeable path.
2. dynamic change queue number.

..Note:
1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > 5.1, and packed ring multi-queues not support reconnect in qemu yet.
2.For split virtqueue virtio-net with multi-queues server mode test, better to use qemu version >= 5.2.0, dut to qemu(v4.2.0~v5.1.0) exist split ring multi-queues reconnection issue.
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
	iperf

General set up
--------------
1. Compile DPDK::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
	# ninja -C <dpdk build dir> -j 110
	For example:
	CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
	ninja -C x86_64-native-linuxapp-gcc -j 110

2. Get the DMA device ID of DUT, for example, 0000:6a:01.0 is DMA device ID::

	<dpdk dir># ./usertools/dpdk-devbind.py -s

	DMA devices using kernel driver
	===============================
	0000:6a:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	0000:6f:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	0000:74:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	0000:79:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	0000:e7:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	0000:ec:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	0000:f1:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	0000:f6:01.0 'Device 0b25' drv=idxd unused=vfio-pci

Test case
=========

Common steps
------------
1.Bind DSA devices to DPDK vfio-pci driver::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DSA device id>
	For example, bind 2 DMA devices to vfio-pci driver:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:e7:01.0 0000:ec:01.0

.. note::

	One DPDK DSA device can create 8 WQ at most. Below is an example, where DPDK DSA device will create one and
	eight WQ for DSA deivce 0000:e7:01.0 and 0000:ec:01.0. The value of “max_queues” is 1~8:
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:e7:01.0,max_queues=1 -- -i
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:ec:01.0,max_queues=8 -- -i

2. Bind DSA devices to kernel idxd driver, and configure Work Queue (WQ)::

	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd <numDevices * 2>
	<dpdk dir># ./drivers/dma/dma/idxd/dpdk_idxd_cfg.py -q <numWq>

.. note::

	Better to reset WQ when need operate DSA devices that bound to idxd drvier:
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py --reset <numDevices>
	You can check it by 'ls /dev/dsa'
	numDevices: number of devices, where 0<=numDevices<=7, corresponding to 0000:6a:01.0 - 0000:f6:01.0
	numWq: Number of workqueues per DSA endpoint, where 1<=numWq<=8

	For example, bind 2 DMA devices to idxd driver and configure WQ:

	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 1
	Check WQ by 'ls /dev/dsa' and can find "wq0.0 wq1.0 wq1.1 wq1.2 wq1.3"

Test Case 1: VM2VM virtio-pmd split ring mergeable path dynamic queue size with dsa dpdk driver and server mode
-----------------------------------------------------------------------------------------------------------------
This case tests split ring mergeable path in VM2VM vhost-user/virtio-pmd topology when vhost uses the asynchronous operations with dsa dpdk driver, 
check that it can tx chain packets normally after dynamically changing queue number from vhost, reconnection has also been tested.

1. Bind 2 dsa device to vfio-pci, then launch the testpmd with 2 vhost ports below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=4 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4 \
	--lcore-dma=[lcore2@0000:f1:01.0-q0,lcore2@0000:f1:01.0-q1,lcore3@0000:f1:01.0-q2,lcore3@0000:f1:01.0-q3,lcore4@0000:f6:01.0-q0,lcore4@0000:f6:01.0-q1,lcore5@0000:f6:01.0-q2,lcore5@0000:f6:01.0-q3]
	testpmd>start

2. Launch VM1 and VM2 using qemu::

	taskset -c 6-16 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 17-27 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

3. On VM1 and VM2, bind virtio device with vfio-pci driver::

	modprobe vfio
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

4. Launch testpmd in VM1::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
	testpmd>set fwd mac
	testpmd>start

5. Launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins and 4 queues (queue0 to queue3) have packets rx/tx::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
	testpmd>set fwd mac
	testpmd>set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
	testpmd>start tx_first 32
	testpmd>show port stats all

6. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

	perf top

7. Stop vhost, check that both 4 queues can rx/tx queues::

	testpmd>stop

8. On host, dynamic change queue numbers::

	testpmd>stop
	testpmd>port stop all
	testpmd>port config all rxq 8
	testpmd>port config all txq 8
	testpmd>port start all
	testpmd>start

9. Send packets by testpmd in VM2::

	testpmd>stop
	testpmd>start tx_first 32
	testpmd>show port stats all

10. Check vhost testpmd RX/TX can work normally, packets can looped between two VMs and both 8 queues can RX/TX traffic. 

11. Rerun step 6.

12. Relaunch and start vhost side testpmd with 8 queues::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=8 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore2@0000:f1:01.0-q0,lcore2@0000:f1:01.0-q1,lcore3@0000:f1:01.0-q2,lcore3@0000:f1:01.0-q3,lcore4@0000:f1:01.0-q4,lcore4@0000:f1:01.0-q5,lcore5@0000:f1:01.0-q6,lcore5@0000:f1:01.0-q7]
	testpmd>start

13. Send packets by testpmd in VM2, check imix packets can looped between two VMs for 1 mins and 8 queues all have packets rx/tx::

	testpmd>stop
	testpmd>start tx_first 32
	testpmd>show port stats all
	testpmd>stop

14. Rerun step 12-13 for 3 times.

Test Case 2: VM2VM virtio-pmd split ring non-mergeable path dynamic queue size with dsa dpdk driver and server mode
----------------------------------------------------------------------------------------------------------------------
This case tests split ring non-mergeable path in VM2VM vhost-user/virtio-pmd topology when vhost uses the asynchronous operations with dsa dpdk driver, 
check that it can work normally after dynamically changing queue number at virtio-pmd side, reconnection has also been tested.

1. Bind 2 dsa device to vfio-pci, then launch the testpmd with 2 vhost ports below commands::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=4 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore2@0000:f1:01.0-q0,lcore2@0000:f1:01.0-q1,lcore3@0000:f1:01.0-q2,lcore3@0000:f1:01.0-q3,lcore4@0000:f6:01.0-q0,lcore4@0000:f6:01.0-q1,lcore5@0000:f6:01.0-q2,lcore5@0000:f6:01.0-q3]
	testpmd>start

2. Launch VM1 and VM2 using qemu::

	taskset -c 6-16 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 17-27 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

3. On VM1 and VM2, bind virtio device with vfio-pci driver::

	modprobe vfio
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

4. Launch testpmd in VM1::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024	
	testpmd>set fwd mac
	testpmd>start

5. Launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins and 4 queues (queue0 to queue3) have packets rx/tx::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024	
	testpmd>set fwd mac
	testpmd>set txpkts 64,256,512
	testpmd>start tx_first 32
	testpmd>show port stats all

6. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

	perf top

7. Stop vhost, check that both 8 queues can rx/tx queues, then start the vhost.

	testpmd>stop
	testpmd>start

8. On VM2, dynamic change queue numbers at virtio-pmd side from 8 queues to 4 queues::

	testpmd>stop
	testpmd>port stop all
	testpmd>port config all rxq 4
	testpmd>port config all txq 4
	testpmd>port start all
	testpmd>start

9. Send packets by testpmd in VM2, check Check virtio-pmd RX/TX can work normally and imix packets can looped between two VMs for 1 mins::

	testpmd>stop
	testpmd>start tx_first 32
	testpmd>show port stats all

10. Rerun step 6.

11. Stop testpmd in VM2, and check that 4 queues can RX/TX traffic.

Test Case 3: VM2VM virtio-pmd packed ring mergeable path dynamic queue size with dsa dpdk driver and server mode
-----------------------------------------------------------------------------------------------------------------
This case tests packed ring mergeable path in VM2VM vhost-user/virtio-pmd topology when vhost uses the asynchronous operations with dsa dpdk driver,
check that it can tx chain packets normally after dynamically changing queue number.

1. Bind 2 dsa device to vfio-pci, then launch the testpmd with 2 vhost ports below commands::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=4 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4 \
	--lcore-dma=[lcore2@0000:f1:01.0-q0,lcore2@0000:f1:01.0-q1,lcore3@0000:f1:01.0-q2,lcore3@0000:f1:01.0-q3,lcore4@0000:f6:01.0-q0,lcore4@0000:f6:01.0-q1,lcore5@0000:f6:01.0-q2,lcore5@0000:f6:01.0-q3]
	testpmd>start

2. Launch VM1 and VM2 using qemu::

	taskset -c 6-16 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	taskset -c 17-27 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

3. On VM1 and VM2, bind virtio device with vfio-pci driver::

	modprobe vfio
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

4. Launch testpmd in VM1::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
	testpmd>set fwd mac
	testpmd>start

5. Launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins and 4 queues (queue0 to queue3) have packets rx/tx::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
	testpmd>set fwd mac
	testpmd>set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
	testpmd>start tx_first 32
	testpmd>show port stats all
	testpmd>stop

6. Quit VM2 and relaunch VM2 with split ring::

	taskset -c 17-27 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

7. Bind virtio device with vfio-pci driver::

	modprobe vfio
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

8. Launch testpmd in VM2 and send imix pkts from VM2::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
	testpmd>set fwd mac
	testpmd>set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
	testpmd>start tx_first 32
   
9. On host, Check imix packets can looped between two VMs and 4 queues all have packets rx/tx::

	testpmd>show port stats all
	testpmd>stop
	testpmd>start

10. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

	perf top

11. On host, dynamic change queue numbers::

	testpmd>stop
	testpmd>port stop all
	testpmd>port config all rxq 8
	testpmd>port config all txq 8
	testpmd>port start all
	testpmd>start

12. Send packets by testpmd in VM2::

	testpmd>stop
	testpmd>start tx_first 32
	testpmd>show port stats all

13. Check vhost testpmd RX/TX can work normally, packets can looped between two VMs and both 8 queues can RX/TX traffic.

14. Rerun step 10.

Test Case 4: VM2VM virtio-pmd packed ring non-mergeable path dynamic queue size with dsa dpdk driver and server mode
-----------------------------------------------------------------------------------------------------------------------
This case tests packed ring non-mergeable path in VM2VM vhost-user/virtio-pmd topology when vhost uses the asynchronous operations with dsa dpdk driver, 
check that it can work normally after dynamically changing queue number at virtio-pmd side.

1. Bind 2 dsa device to vfio-pci, then launch the testpmd with 2 vhost ports below commands::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=4 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4]' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore2@0000:f1:01.0-q0,lcore2@0000:f1:01.0-q1,lcore3@0000:f1:01.0-q2,lcore3@0000:f1:01.0-q3,lcore4@0000:f6:01.0-q0,lcore4@0000:f6:01.0-q1,lcore5@0000:f6:01.0-q2,lcore5@0000:f6:01.0-q3]
	testpmd>start

2. Launch VM1 and VM2 using qemu::

	taskset -c 6-16 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	taskset -c 17-27 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

3. On VM1 and VM2, bind virtio device with vfio-pci driver::

	modprobe vfio
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

4. Launch testpmd in VM1::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024	
	testpmd>set fwd mac
	testpmd>start

5. Launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024	
	testpmd>set fwd mac
	testpmd>set txpkts 64,256,512
	testpmd>start tx_first 32
	testpmd>show port stats all

6. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

	perf top

7. On VM2, stop the testpmd, check that both 8 queues have packets rx/tx::

	testpmd>stop

8. On VM2, dynamic change queue numbers at virtio-pmd side from 8 queues to 4 queues::

	testpmd>stop
	testpmd>port stop all
	testpmd>port config all rxq 4
	testpmd>port config all txq 4
	testpmd>port start all
	testpmd>start

9. Send packets by testpmd in VM2, check Check virtio-pmd RX/TX can work normally and imix packets can looped between two VMs for 1 mins::

	testpmd>stop
	testpmd>start tx_first 32
	testpmd>show port stats all

10. Rerun step 6.

11. Stop testpmd in VM2, and check that 4 queues can RX/TX traffic.

Test Case 5: VM2VM virtio-pmd split ring mergeable path dynamic queue size with dsa kernel driver and server mode
-------------------------------------------------------------------------------------------------------------------
This case tests split ring mergeable path in VM2VM vhost-user/virtio-pmd topology when vhost uses the asynchronous operations with dsa kernel driver, 
check that it can tx chain packets normally after dynamically changing queue number at vhost side, reconnection has also been tested.

1. Bind 2 dsa device to idxd::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	./drivers/raw/ioat/dpdk_idxd_cfg.py -q 8 0
	./drivers/raw/ioat/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch the testpmd with 2 vhost ports below commands::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4 \
	--lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore3@wq0.2,lcore3@wq0.3,lcore4@wq0.4,lcore4@wq0.5,lcore5@wq0.6,lcore5@wq0.7]
	testpmd>start

3. Launch VM1 and VM2 using qemu::

	taskset -c 6-16 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 17-27 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
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
	testpmd>set fwd mac
	testpmd>start

6. Launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins and 4 queues (queue0 to queue3) have packets rx/tx::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
	testpmd>set fwd mac
	testpmd>set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
	testpmd>start tx_first 32
	testpmd>show port stats all

7. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

	perf top

8. Stop vhost, check that both 4 queues can rx/tx queues.	

9. On host, dynamic change queue numbers::

	testpmd>stop
	testpmd>port stop all
	testpmd>port config all rxq 8
	testpmd>port config all txq 8
	testpmd>port start all
	testpmd>start

10. Send packets by testpmd in VM2::

	testpmd>stop
	testpmd>start tx_first 32
	testpmd>show port stats all

11. Check vhost testpmd RX/TX can work normally, packets can looped between two VMs and both 8 queues can RX/TX traffic.

12. Rerun step 7.

13. Relaunch and start vhost side testpmd with 8 queues::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore3@wq0.2,lcore3@wq0.3,lcore4@wq1.0,lcore4@wq1.1,lcore5@wq1.2,lcore5@wq1.3]
	testpmd>start

14. Send packets by testpmd in VM2, check imix packets can looped between two VMs for 1 mins and 8 queues all have packets rx/tx::

	testpmd>stop
	testpmd>start tx_first 32
	testpmd>show port stats all
	testpmd>stop

15. Rerun step 13-14 for 3 times.

Test Case 6: VM2VM virtio-pmd split ring non-mergeable path dynamic queue size with dsa kernel driver and server mode
-----------------------------------------------------------------------------------------------------------------------
This case tests split ring non-mergeable path in VM2VM vhost-user/virtio-pmd topology when vhost uses the asynchronous operations with dsa kernel driver, 
check that it can work normally after dynamically changing queue number at virtio-pmd side, reconnection has also been tested.

1. Bind 2 dsa device to idxd::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	./drivers/raw/ioat/dpdk_idxd_cfg.py -q 8 0
	./drivers/raw/ioat/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch the testpmd with 2 vhost ports below commands::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore3@wq0.2,lcore3@wq0.3,lcore4@wq0.4,lcore4@wq0.5,lcore5@wq0.6,lcore5@wq0.7]
	testpmd>start

3. Launch VM1 and VM2 using qemu::

	taskset -c 6-16 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 17-27 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
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
	testpmd>set fwd mac
	testpmd>start

6. Launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins and 4 queues (queue0 to queue3) have packets rx/tx::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024	
	testpmd>set fwd mac
	testpmd>set txpkts 64,256,512
	testpmd>start tx_first 32
	testpmd>show port stats all

7. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

	perf top

8. Stop testpmd in host, and check that 8 queues can RX/TX traffic.

8. On VM, dynamic change queue numbers at virtio-pmd side from 8 queues to 4 queues::

	testpmd>stop
	testpmd>port stop all
	testpmd>port config all rxq 4
	testpmd>port config all txq 4
	testpmd>port start all
	testpmd>start

9. Send packets by testpmd in VM2, check Check virtio-pmd RX/TX can work normally and imix packets can looped between two VMs for 1 mins::

	testpmd>stop
	testpmd>start tx_first 32
	testpmd>show port stats all

10. Rerun step 7.

11. Stop testpmd in host, and check that 4 queues can RX/TX traffic.

Test Case 7: VM2VM virtio-pmd packed ring mergeable path dynamic queue size with dsa kernel driver and server mode
-------------------------------------------------------------------------------------------------------------------
This case tests packed ring mergeable path in VM2VM vhost-user/virtio-pmd topology when vhost uses the asynchronous operations with dsa kernel driver, 
check that it can tx chain packets normally after dynamically changing queue number.

1. Bind 1 dsa device to idxd::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0
	./drivers/raw/ioat/dpdk_idxd_cfg.py -q 8 0
	ls /dev/dsa #check wq configure success

2. Launch the testpmd with 2 vhost ports below commands::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3]' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4 \
	--lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore3@wq0.2,lcore3@wq0.3,lcore4@wq0.4,lcore4@wq0.5,lcore5@wq0.6,lcore5@wq0.7]
	testpmd>start

3. Launch VM1 and VM2 using qemu::

	taskset -c 6-16 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	taskset -c 17-27 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
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
	testpmd>set fwd mac
	testpmd>start

6. Launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins and 4 queues (queue0 to queue3) have packets rx/tx::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
	testpmd>set fwd mac
	testpmd>set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
	testpmd>start tx_first 32
	testpmd>show port stats all
	testpmd>stop

7. Quit VM2 and relaunch VM2 with split ring::

	taskset -c 17-27 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

8. Bind virtio device with vfio-pci driver::

	modprobe vfio
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

9. Launch testpmd in VM2 and send imix pkts from VM2::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd mac
	testpmd>set txpkts 64,256,512
	testpmd>start tx_first 32

10. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

	perf top

11. On host, check imix packets can looped between two VMs and 4 queues all have packets rx/tx::

	testpmd>show port stats all
	testpmd>stop

12. On host, dynamic change queue numbers::

	testpmd>stop
	testpmd>port stop all
	testpmd>port config all rxq 8
	testpmd>port config all txq 8
	testpmd>port start all
	testpmd>start

13. Send packets by testpmd in VM2::

	testpmd>stop
	testpmd>start tx_first 32
	testpmd>show port stats all

14. Check vhost testpmd RX/TX can work normally, packets can looped between two VMs and both 8 queues can RX/TX traffic.

15. Rerun step 10.

Test Case 8: VM2VM virtio-pmd packed ring non-mergeable path dynamic queue size with dsa kernel driver and server mode
------------------------------------------------------------------------------------------------------------------------
This case tests packed ring non-mergeable path in VM2VM vhost-user/virtio-pmd topology when vhost uses the asynchronous operations with dsa kernel driver, 
check that it can work normally after dynamically changing queue number at virtio-pmd side.

1. Bind 2 dsa device to idxd::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	./drivers/raw/ioat/dpdk_idxd_cfg.py -q 8 0
	./drivers/raw/ioat/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

1. Launch the testpmd with 2 vhost ports below commands::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore3@wq0.2,lcore3@wq0.3,lcore4@wq1.0,lcore4@wq1.1,lcore5@wq1.2,lcore5@wq1.3]
	testpmd>start

2. Launch VM1 and VM2 using qemu::

	taskset -c 6-16 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	taskset -c 17-27 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

3. On VM1 and VM2, bind virtio device with vfio-pci driver::

	modprobe vfio
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

4. Launch testpmd in VM1::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024	
	testpmd>set fwd mac
	testpmd>start

5. Launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024	
	testpmd>set fwd mac
	testpmd>set txpkts 64,256,512
	testpmd>start tx_first 32
	testpmd>show port stats all

6. Check vhost use the asynchronous data path(funtion like virtio_dev_rx_async_xxx/virtio_dev_tx_async_xxx)::

	perf top

7. On VM2, stop the testpmd, check that both 8 queues have packets rx/tx::

	testpmd>stop

8. On VM2, dynamic change queue numbers at virtio-pmd side from 8 queues to 4 queues::

	testpmd>stop
	testpmd>port stop all
	testpmd>port config all rxq 4
	testpmd>port config all txq 4
	testpmd>port start all
	testpmd>start

9. Send packets by testpmd in VM2, check Check virtio-pmd RX/TX can work normally and imix packets can looped between two VMs for 1 mins::

	testpmd>stop
	testpmd>start tx_first 32
	testpmd>show port stats all

10. Rerun step 6.

11. Stop testpmd in VM2, and check that 4 queues can RX/TX traffic.

12. On VM2, dynamic change queue numbers at virtio-pmd side from 4 queues to 8 queues::

	testpmd>stop
	testpmd>port stop all
	testpmd>port config all rxq 8
	testpmd>port config all txq 8
	testpmd>port start all
	testpmd>start
	
13. Send packets by testpmd in VM2, check Check virtio-pmd RX/TX can work normally and imix packets can looped between two VMs for 1 mins::

	testpmd>stop
	testpmd>start tx_first 32
	testpmd>show port stats all

14. Rerun step 6.

15. Stop testpmd in VM2, and check that 8 queues can RX/TX traffic.	
