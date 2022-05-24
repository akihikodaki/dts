.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

======================================================
VM2VM vhost-user/virtio-net with DSA driver test plan
======================================================

Description
===========

Vhost asynchronous data path leverages DMA devices to offload memory copies from the CPU and it is implemented in an asynchronous way.
In addition, vhost supports M:N mapping between vrings and DMA virtual channels. Specifically, one vring can use multiple different DMA
channels and one DMA channel can be shared by multiple vrings at the same time.Vhost enqueue operation with CBDMA channels is supported
in both split and packed ring.

This document provides the test plan for testing the following features when Vhost-user using asynchronous data path with
DSA driver (kernel IDXD driver and DPDK vfio-pci driver) in VM2VM virtio-net topology.
1. check Vhost tx offload function by verifing the TSO/cksum in the TCP/IP stack with vm2vm split ring and packed ring 
vhost-user/virtio-net mergeable path.
2.Check the payload of large packet (larger than 1MB) is valid after forwarding packets with vm2vm split ring
and packed ring vhost-user/virtio-net mergeable and non-mergeable path.
3. Multi-queues number dynamic change in vm2vm vhost-user/virtio-net with split ring and packed ring.

IOMMU impact:
If iommu off, idxd can work with iova=pa
If iommu on, kernel dsa driver only can work with iova=va by program IOMMU, can't use iova=pa(fwd not work due to pkts payload wrong).

Note: 
1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > v5.1, and packed ring multi-queues not support reconnect in qemu yet.
2.For split virtqueue virtio-net with multi-queues server mode test, need qemu version >= 5.2.0, dut to old qemu exist reconnect issue when multi-queues test.
3.When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
exceed IOMMU's max capability, better to use 1G guest hugepage.
4.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd, and the suite has not yet been automated.

Prerequisites
=============

Topology
--------
	Test flow: Virtio-net <-> Vhost-user <-> Testpmd <-> Vhost-user <-> Virtio-net

Software
--------
	iperf
	qemu: https://download.qemu.org/qemu-6.2.0.tar.xz

General set up
--------------
1. Compile DPDK::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=<dpdk build dir>
	# ninja -C <dpdk build dir> -j 110
	For example,
	CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=x86_64-native-linuxapp-gcc
	ninja -C x86_64-native-linuxapp-gcc -j 110

2. Get the PCI device ID and DSA device ID of DUT, for example, 0000:4f:00.1 is PCI device ID, 0000:6a:01.0 - 0000:f6:01.0 are DSA device IDs::

	<dpdk dir># ./usertools/dpdk-devbind.py -s

	Network devices using kernel driver
	===================================
	0000:4f:00.1 'Ethernet Controller E810-C for QSFP 1592' drv=ice unused=vfio-pci

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
1. Bind DSA devices to DPDK vfio-pci driver::

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
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q <numWq>

.. note::

	Better to reset WQ when need operate DSA devices that bound to idxd drvier:
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py --reset <numDevices * 2>
	You can check it by 'ls /dev/dsa'
	numDevices: number of devices, where 0<=numDevices<=7, corresponding to 0000:6a:01.0 - 0000:f6:01.0
	numWq: Number of workqueues per DSA endpoint, where 1<=numWq<=8

	For example, bind 2 DMA devices to idxd driver and configure WQ:

	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 2
	Check WQ by 'ls /dev/dsa' and can find "wq0.0 wq2.0 wq2.1 wq2.2 wq2.3"

Test Case 1: VM2VM vhost-user/virtio-net split ring test TSO with dsa dpdk driver
-----------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net split ring mergeable path 
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue operations with dsa dpdk driver.

1. Bind 1 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch the Vhost testpmd by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:e7:01.0,max_queues=2 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas=[txq0]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1 --lcore-dma=[lcore2@0000:e7:01.0-q0,lcore3@0000:e7:01.0-q1]
	testpmd>start

3. Launch VM1 and VM2 with split ring mergeable path and tso on::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

7. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1522, Port 1 should have rx packets above 1522::

	testpmd>show port xstats all

Test Case 2: VM2VM vhost-user/virtio-net split ring mergeable path 8 queues test with large packet payload with dsa dpdk driver
---------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net split ring mergeable path when vhost uses the asynchronous enqueue operations with dsa dpdk driver.
The dynamic change of multi-queues number, iova as VA and PA mode also test.

1. Bind 4 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0 f1:01.0 f6:01.1

2. Launch the Vhost testpmd by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:e7:01.0,max_queues=8  -a 0000:ec:01.0,max_queues=8 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 --lcore-dma=[lcore2@0000:e7:01.0-q0,lcore2@0000:e7:01.0-q1,lcore2@0000:e7:01.0-q2,lcore2@0000:e7:01.0-q3,lcore2@0000:e7:01.0-q4,lcore2@0000:e7:01.0-q5,lcore3@0000:e7:01.0-q6,lcore3@0000:e7:01.0-q7,lcore4@0000:ec:01.0-q0,lcore4@0000:ec:01.0-q1,lcore4@0000:ec:01.0-q2,lcore4@0000:ec:01.0-q3,lcore4@0000:ec:01.0-q4,lcore4@0000:ec:01.0-q5,lcore4@0000:ec:01.0-q6,lcore5@0000:ec:01.0-q7]
	testpmd>start

3. Launch VM1 and VM2 using qemu 6.2.0::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Quit and relaunch vhost w/ diff dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=8  -a 0000:f6:01.0,max_queues=8 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 --lcore-dma=[lcore2@0000:f1:01.0-q0,lcore2@0000:f1:01.0-q1,lcore2@0000:f1:01.0-q2,lcore2@0000:f1:01.0-q3,lcore3@0000:f1:01.0-q0,lcore3@0000:f1:01.0-q2,lcore3@0000:f1:01.0-q4,lcore3@0000:f1:01.0-q5,lcore3@0000:f1:01.0-q6,lcore3@0000:f1:01.0-q7,lcore4@0000:f1:01.0-q1,lcore4@0000:f1:01.0-q3,lcore4@0000:f6:01.0-q0,lcore4@0000:f6:01.0-q1,lcore4@0000:f6:01.0-q2,lcore4@0000:f6:01.0-q3,lcore4@0000:f6:01.0-q4,lcore4@0000:f6:01.0-q5,lcore4@0000:f6:01.0-q6,lcore5@0000:f6:01.0-q7]
	testpmd>start

9. Rerun step 6-7.

10. Quit and relaunch vhost w/ iova=pa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:e7:01.0,max_queues=8  -a 0000:ec:01.0,max_queues=8 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=pa -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 --lcore-dma=[lcore2@0000:e7:01.0-q0,lcore2@0000:e7:01.0-q1,lcore2@0000:e7:01.0-q2,lcore2@0000:e7:01.0-q3,lcore3@0000:e7:01.0-q0,lcore3@0000:e7:01.0-q2,lcore3@0000:e7:01.0-q4,lcore3@0000:e7:01.0-q5,lcore3@0000:e7:01.0-q6,lcore3@0000:e7:01.0-q7,lcore4@0000:e7:01.0-q1,lcore4@0000:e7:01.0-q3,lcore4@0000:ec:01.0-q0,lcore4@0000:ec:01.0-q1,lcore4@0000:ec:01.0-q2,lcore4@0000:ec:01.0-q3,lcore4@0000:ec:01.0-q4,lcore4@0000:ec:01.0-q5,lcore4@0000:ec:01.0-q6,lcore5@0000:ec:01.0-q7]
	testpmd>start

11. Rerun step 6-7.

12. Quit vhost ports and relaunch vhost ports w/o dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4
	testpmd>start

13. On VM1, set virtio device::

	<VM1># ethtool -L ens5 combined 4

14. On VM2, set virtio device::

	<VM2># ethtool -L ens5 combined 4

15. Rerun step 6-7.

16. Quit vhost ports and relaunch vhost ports with 1 queues::

	 <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=4' \
	 --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=4'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	 testpmd>start

17. On VM1, set virtio device::

	<VM1># ethtool -L ens5 combined 1

18. On VM2, set virtio device::

	<VM2># ethtool -L ens5 combined 1

19. Rerun step 6-7.

Test Case 3: VM2VM vhost-user/virtio-net split ring non-mergeable path 8 queues test with large packet payload with dsa dpdk driver
------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net split ring non-mergeable path when vhost uses the asynchronous enqueue operations with dsa dpdk driver.
The dynamic change of multi-queues number also test.

1. Bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:e7:01.0,max_queues=8 -a 0000:ec:01.0,max_queues=8  \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 --lcore-dma=[lcore2@0000:e7:01.0-q0,lcore2@0000:e7:01.0-q1,lcore2@0000:e7:01.0-q2,lcore2@0000:e7:01.0-q3,lcore2@0000:e7:01.0-q4,lcore2@0000:e7:01.0-q5,lcore3@0000:e7:01.0-q6,lcore3@0000:e7:01.0-q7,lcore4@0000:ec:01.0-q0,lcore4@0000:ec:01.0-q1,lcore4@0000:ec:01.0-q2,lcore4@0000:ec:01.0-q3,lcore4@0000:ec:01.0-q4,lcore4@0000:ec:01.0-q5,lcore4@0000:ec:01.0-q6,lcore5@0000:ec:01.0-q7]
	testpmd>start

3. Launch VM1 and VM2::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Quit vhost ports and relaunch vhost ports w/o dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

9. Rerun step 6-7.

10. Quit vhost ports and relaunch vhost ports with 1 queues::

	 <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8' \
	 --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	 testpmd>start

11. On VM1, set virtio device::

	<VM1># ethtool -L ens5 combined 1

12. On VM2, set virtio device::

	<VM2># ethtool -L ens5 combined 1

13. Rerun step 6-7.

Test Case 4: VM2VM vhost-user/virtio-net packed ring test TSO with dsa dpdk driver
-----------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net packed ring mergeable path 
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue operations with dsa dpdk driver.

1. Bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --file-prefix=vhost -a 0000:e7:01.0,max_queues=1 -a 0000:ec:01.0,max_queues=1 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas=[txq0]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --lcore-dma=[lcore3@0000:e7:01.0-q0,lcore4@0000:ec:01.0-q0]
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

7. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1522, Port 1 should have rx packets above 1522::

	testpmd>show port xstats all

Test Case 5: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with large packet payload with dsa dpdk driver
---------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net packed ring mergeable path when vhost uses the asynchronous enqueue operations with dsa dpdk driver.
The dynamic change of multi-queues number also test.

1. Bind 8 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:6a:01.0 -a 0000:6f:01.0 -a 0000:74:01.0 -a 0000:79:01.0 -a 0000:e7:01.0 -a 0000:ec:01.0 -a 0000:f1:01.0 -a 0000:f6:01.0 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore2@0000:6a:01.0-q0,lcore2@0000:6f:01.0-q1,lcore2@0000:74:01.0-q2,lcore2@0000:79:01.0-q3,lcore3@0000:6a:01.0-q0,lcore3@0000:74:01.0-q2,lcore3@0000:e7:01.0-q4,lcore3@0000:ec:01.0-q5,lcore3@0000:f1:01.0-q6,lcore3@0000:f6:01.0-q7,lcore4@0000:6f:01.0-q1,lcore4@0000:79:01.0-q3,lcore4@0000:6a:01.0-q1,lcore4@0000:6f:01.0-q2,lcore4@0000:74:01.0-q3,lcore4@0000:79:01.0-q4,lcore4@0000:e7:01.0-q5,lcore4@0000:ec:01.0-q6,lcore4@0000:f1:01.0-q7,lcore5@0000:f6:01.0-q0]
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1>: scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.

Test Case 6: VM2VM vhost-user/virtio-net packed ring non-mergeable path 8 queues test with large packet payload with dsa dpdk driver
-------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net packed ring non-mergeable path when vhost uses the asynchronous enqueue operations with dsa dpdk driver.
The dynamic change of multi-queues number also test.

1. Bind 8 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:6a:01.0 -a 0000:6f:01.0 -a 0000:74:01.0 -a 0000:79:01.0 -a 0000:e7:01.0 -a 0000:ec:01.0 -a 0000:f1:01.0 -a 0000:f6:01.0 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 --lcore-dma=[lcore2@0000:6a:01.0-q0,lcore2@0000:6f:01.0-q1,lcore2@0000:74:01.0-q2,lcore2@0000:79:01.0-q3,lcore2@0000:e7:01.0-q4,lcore2@0000:ec:01.0-q5,lcore3@0000:f1:01.0-q6,lcore3@0000:f6:01.0-q7,lcore4@0000:6a:01.0-q1,lcore4@0000:6f:01.0-q2,lcore4@0000:74:01.0-q3,lcore4@0000:79:01.0-q4,lcore4@0000:e7:01.0-q5,lcore4@0000:ec:01.0-q6,lcore4@0000:f1:01.0-q7,lcore5@0000:f6:01.0-q0]
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.

Test Case 7: VM2VM vhost-user/virtio-net packed ring test TSO with dsa dpdk driver and pa mode
-----------------------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net packed ring mergeable path 
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue operations with dsa dpdk driver and iova as PA mode.

1. Bind 2  dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch the Vhost sample with PA mode by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --file-prefix=vhost -a 0000:e7:01.0 -a 0000:ec:01.0 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas=[txq0]' \
	--iova=pa -- -i --nb-cores=2 --txd=1024 --rxd=1024 --lcore-dma=[lcore3@0000:e7:01.0-q0,lcore4@0000:ec:01.0-q0]
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

7. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1522, Port 1 should have rx packets above 1522::

	testpmd>show port xstats all

Test Case 8: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with large packet payload with dsa dpdk driver and pa mode
---------------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net packed ring mergeable path when vhost uses the asynchronous enqueue operations with dsa dpdk driver
and iova as PA mode. The dynamic change of multi-queues number also test.

1. Bind 8  dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:6a:01.0 -a 0000:6f:01.0 -a 0000:74:01.0 -a 0000:79:01.0 -a 0000:e7:01.0 -a 0000:ec:01.0 -a 0000:f1:01.0 -a 0000:f6:01.0 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=pa -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 --lcore-dma=[lcore2@0000:6a:01.0-q0,lcore2@0000:6f:01.0-q1,lcore2@0000:74:01.0-q2,lcore2@0000:79:01.0-q3,lcore3@0000:6a:01.0-q0,lcore3@0000:74:01.0-q2,lcore3@0000:e7:01.0-q4,lcore3@0000:ec:01.0-q5,lcore3@0000:f1:01.0-q6,lcore3@0000:f6:01.0-q7,lcore4@0000:6f:01.0-q1,lcore4@0000:79:01.0-q3,lcore4@0000:6a:01.0-q1,lcore4@0000:6f:01.0-q2,lcore4@0000:74:01.0-q3,lcore4@0000:79:01.0-q4,lcore4@0000:e7:01.0-q5,lcore4@0000:ec:01.0-q6,lcore4@0000:f1:01.0-q7,lcore5@0000:f6:01.0-q0]
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.

Test Case 9: VM2VM vhost-user/virtio-net split ring test TSO with dsa kernel driver
------------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net split ring mergeable path 
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue operations with dsa kernel driver.

1. Bind 1 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas=[txq0]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1 --lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore3@wq0.2,lcore3@wq0.3]
	testpmd>start

3. Launch VM1 and VM2 on socket 1::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM3># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

7. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1522, Port 1 should have rx packets above 1522::

	testpmd>show port xstats all

Test Case 10: VM2VM vhost-user/virtio-net split ring mergeable path 8 queues test with large packet payload with dsa kernel driver
-----------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net split ring mergeable path when vhost uses the asynchronous enqueue operations with dsa kernel driver.
The dynamic change of multi-queues number also test.

1. Bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore2@wq0.2,lcore2@wq0.3,lcore2@wq0.4,lcore2@wq0.5,lcore3@wq0.6,lcore3@wq0.7,lcore4@wq2.0,lcore4@wq2.1,lcore4@wq2.2,lcore4@wq2.3,lcore4@wq2.4,lcore4@wq2.5,lcore4@wq2.6,lcore5@wq2.7]
	testpmd>start

3. Launch VM1 and VM2 using qemu::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Quit and relaunch vhost w/ diff dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 --lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore2@wq0.2,lcore2@wq0.3,lcore3@wq0.0,lcore3@wq0.2,lcore3@wq0.4,lcore3@wq0.5,lcore3@wq0.6,lcore3@wq0.7,lcore4@wq0.1,lcore4@wq0.3,lcore4@wq2.0,lcore4@wq2.1,lcore4@wq2.2,lcore4@wq2.3,lcore4@wq2.4,lcore4@wq2.5,lcore4@wq2.6,lcore5@wq2.7]
	testpmd>start

9. Rerun step 6-7.

10. Quit vhost ports and relaunch vhost ports w/o dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4
	testpmd>start

11. On VM1, set virtio device::

	ethtool -L ens5 combined 4

12. On VM2, set virtio device::

	ethtool -L ens5 combined 4

13. Rerun step 6-7.

14. Quit vhost ports and relaunch vhost ports with 1 queues::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=4' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=4'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	testpmd>start

15. On VM1, set virtio device::

	ethtool -L ens5 combined 1

16. On VM2, set virtio device::

	ethtool -L ens5 combined 1

17. Rerun step 6-7.

Test Case 11: VM2VM vhost-user/virtio-net split ring non-mergeable path 8 queues test with large packet payload with dsa kernel driver
---------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net split ring non-mergeable path when vhost uses the asynchronous enqueue operations with dsa kernel driver.
The dynamic change of multi-queues number also test.

1. Bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 --lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore2@wq0.2,lcore2@wq0.3,lcore2@wq0.4,lcore2@wq0.5,lcore3@wq0.6,lcore3@wq0.7,lcore4@wq2.0,lcore4@wq2.1,lcore4@wq2.2,lcore4@wq2.3,lcore4@wq2.4,lcore4@wq2.5,lcore4@wq2.6,lcore5@wq2.7]
	testpmd>start

3. Launch VM1 and VM2::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Quit vhost ports and relaunch vhost ports w/o dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

9. Rerun step 6-7.

10. Quit vhost ports and relaunch vhost ports with 1 queues::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	testpmd>start

11. On VM1, set virtio device::

	<VM1># ethtool -L ens5 combined 1

12. On VM2, set virtio device::

	<VM2># ethtool -L ens5 combined 1

13. Rerun step 6-7.

Test Case 12: VM2VM vhost-user/virtio-net packed ring test TSO with dsa kernel driver
-------------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net packed ring mergeable path
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue operations with dsa kernel driver.

1. Bind 2 dsa device to idxd::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 2
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas=[txq0]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --lcore-dma=[lcore3@wq0.0,lcore4@wq2.0]
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

7. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1522, Port 1 should have rx packets above 1522::

	testpmd>show port xstats all

Test Case 13: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with large packet payload with dsa kernel driver
-------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net packed ring mergeable path when vhost uses the asynchronous enqueue operations with dsa kernel driver.
The dynamic change of multi-queues number also test.

1. Bind 8 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 4
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 6
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 8
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 10
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 12
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 14
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 --lcore-dma=[lcore2@wq0.0,lcore2@wq2.1,lcore2@wq4.2,lcore2@wq6.3,lcore3@wq0.0,lcore3@wq4.2,lcore3@wq8.4,lcore3@wq10.5,lcore3@wq12.6,lcore3@wq14.7,lcore4@wq2.1,lcore4@wq6.3,lcore4@wq0.1,lcore4@wq2.2,lcore4@wq4.3,lcore4@wq6.4,lcore4@wq8.5,lcore4@wq10.6,lcore4@wq12.7,lcore5@wq14.0]
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.

Test Case 14: VM2VM vhost-user/virtio-net packed ring non-mergeable path 8 queues test with large packet payload with dsa kernel driver
----------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net packed ring mergeable path when vhost uses the asynchronous enqueue operations with dsa kernel driver.
The dynamic change of multi-queues number also test.

1. Bind 8 dsa device to vfio-pci like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 4
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 6
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 8
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 10
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 12
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 14
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 --lcore-dma=[lcore2@wq0.0,lcore2@wq2.1,lcore2@wq4.2,lcore2@wq6.3,lcore3@wq0.0,lcore3@wq4.2,lcore3@wq8.4,lcore3@wq10.5,lcore3@wq12.6,lcore3@wq14.7,lcore4@wq2.1,lcore4@wq6.3,lcore4@wq0.1,lcore4@wq2.2,lcore4@wq4.3,lcore4@wq6.4,lcore4@wq8.5,lcore4@wq10.6,lcore4@wq12.7,lcore5@wq14.0]
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.

Test Case 15: VM2VM vhost-user/virtio-net split ring non-mergeable 16 queues test with large packet payload with dsa dpdk and kernel driver
--------------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net split ring non-mergeable path when vhost uses the asynchronous enqueue operations with dsa dpdk
and kernel driver. The dynamic change of multi-queues number also test.

1. Bind 4 dsa device to vfio-pci and 4 dsa device to idxd like common step 1-2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0 79:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 4
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 6
	ls /dev/dsa #check wq configure success

	<dpdk dir># ./usertools/dpdk-devbind.py -u 0000:e7:01.0 0000:ec:01.0 0000:f1:01.0 0000:f6:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:e7:01.0 0000:ec:01.0 0000:f1:01.0 0000:f6:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:e7:01.0 -a 0000:ec:01.0  \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13;txq14;txq15]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13;txq14;txq15]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16 --lcore-dma=[lcore2@0000:e7:01.0-q0,lcore2@0000:e7:01.0-q1,lcore2@0000:ec:01.0-q0,lcore2@0000:ec:01.0-q1,lcore3@wq0.0,lcore3@wq2.0,lcore4@0000:e7:01.0-q4,lcore4@0000:e7:01.0-q5,lcore4@0000:ec:01.0-q4,lcore4@0000:ec:01.0-q5,lcore5@wq4.1,lcore5@wq2.1]
	testpmd>start

3. Launch VM1 and VM2::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 16
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 16
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Quit vhost ports and relaunch vhost ports w/ diff dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:e7:01.0,max_queues=2 -a 0000:f1:01.0,max_queues=2 -a 0000:f6:01.0,max_queues=2 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16 --lcore-dma=[lcore2@0000:e7:01.0-q0,lcore2@0000:f1:01.0-q0,lcore2@0000:f1:01.0-q1,lcore2@wq4.2,lcore3@wq6.1,lcore3@wq6.3,lcore4@0000:e7:01.0-q1,lcore4@0000:f6:01.0-q0,lcore4@wq4.2,lcore4@wq6.0,lcore5@wq4.2,lcore5@wq6.0]
	testpmd>start

9. rerun step 6-7.

10. Quit vhost ports and relaunch vhost ports w/o dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16
	testpmd>start

11. Rerun step 6-7.

12. Quit vhost ports and relaunch vhost ports with 1 queues::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	testpmd>start

13. On VM1, set virtio device::

	<VM1># ethtool -L ens5 combined 1

14. On VM2, set virtio device::

	<VM2># ethtool -L ens5 combined 1

15. Rerun step 6-7.

Test Case 16: VM2VM vhost-user/virtio-net packed ring mergeable 16 queues test with large packet payload with dsa dpdk and kernel driver
------------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net packed ring mergeable path when vhost uses the asynchronous enqueue operations with dsa dpdk
and kernel driver. The dynamic change of multi-queues number also test.

1. Bind 4 dsa device to vfio-pci and 4 dsa device to idxd like common step 1-2::

	ls /dev/dsa #check wq configure, reset if exist

	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0 79:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 2
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 4
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 6
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:e7:01.0 -a 0000:ec:01.0 -a 0000:f1:01.0 -a 0000:f6:01.0 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13;txq14;txq15]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13;txq14;txq15]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16 --lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore2@wq2.0,lcore2@wq2.1,lcore3@wq0.1,lcore3@wq2.0,lcore3@0000:e7:01.0-q4,lcore3@0000:ec:01.0-q5,lcore3@0000:f1:01.0-q6,lcore3@0000:f6:01.0-q7,lcore4@0000:e7:01.0-q4,lcore4@0000:ec:01.0-q5,lcore4@0000:f1:01.0-q1,lcore4@wq2.0,lcore5@wq4.1,lcore5@wq2.0,lcore5@wq4.1,lcore5@wq6.2]
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 16
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 16
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.



