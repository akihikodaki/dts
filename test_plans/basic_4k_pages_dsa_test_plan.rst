.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

===============================================================
vhost async operation with DSA driver using 4K-pages test plan
===============================================================

Description
===========

Vhost asynchronous data path leverages DMA devices to offload memory copies from the CPU and it is implemented in an asynchronous way.
In addition, vhost supports M:N mapping between vrings and DMA virtual channels. Specifically, one vring can use multiple different DMA
channels and one DMA channel can be shared by multiple vrings at the same time. Vhost enqueue operation with CBDMA channels is supported
in both split and packed ring.

This document provides the test plan for testing some basic functions when Vhost-user using asynchronous data path with
DSA driver (kernel IDXD driver and DPDK vfio-pci driver) and using 4K-pages memory environment.
1. test Vhost asynchronous data path with DSA driver in the PVP topology environment with testpmd.
2. check Vhost tx offload function by verifing the TSO/cksum in the TCP/IP stack with vm2vm split ring and packed ring 
vhost-user/virtio-net mergeable path.
3.Check the payload of large packet (larger than 1MB) is valid after forwarding packets with vm2vm split ring
and packed ring vhost-user/virtio-net mergeable and non-mergeable path.
4. Multi-queues number dynamic change in vm2vm vhost-user/virtio-net with split ring and packed ring.
5. Vhost-user using 1G hugepges and virtio-user using 4k-pages.

DPDK 19.02 add support for using virtio-user without hugepages. The --no-huge mode was augmented to use memfd-backed
memory (on systems that support memfd), to allow using virtio-user-based NICs without hugepages.

Note:
1. When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
exceed IOMMU's max capability, better to use 1G guest hugepage.
2. DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd, and the suite has not yet been automated.

Prerequisites
=============

General set up
--------------
1. Turn off transparent hugepage in grub by adding GRUB_CMDLINE_LINUX="transparent_hugepage=never".

2. Compile DPDK::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=<dpdk build dir>
	# ninja -C <dpdk build dir> -j 110
	For example,
	CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=x86_64-native-linuxapp-gcc
	ninja -C x86_64-native-linuxapp-gcc -j 110

3. Get the PCI device ID and DSA device ID of DUT, for example, 0000:4f:00.1 is PCI device ID, 0000:6a:01.0 - 0000:f6:01.0 are DSA device IDs::

	<dpdk dir># ./usertools/dpdk-devbind.py -s

	Network devices using kernel driver
	===================================
	0000:4f:00.1 'Ethernet Controller E810-C for QSFP 1592' drv=ice unused=vfio-pci

	4DMA devices using kernel driver
	4===============================
	40000:6a:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	40000:6f:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	40000:74:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	40000:79:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	40000:e7:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	40000:ec:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	40000:f1:01.0 'Device 0b25' drv=idxd unused=vfio-pci
	40000:f6:01.0 'Device 0b25' drv=idxd unused=vfio-pci

4. Prepare tmpfs with 4K-pages::

	mkdir /mnt/tmpfs_4k
	mkdir /mnt/tmpfs_4k_2
	mount tmpfs /mnt/tmpfs_4k -t tmpfs -o size=4G
	mount tmpfs /mnt/tmpfs_4k_2 -t tmpfs -o size=4G

Test case
=========

Common steps
------------
1. Bind 1 NIC port to vfio-pci::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
	For example:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:4f.1

2.Bind DSA devices to DPDK vfio-pci driver::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DSA device id>
	For example, bind 2 DMA devices to vfio-pci driver:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:e7:01.0 0000:ec:01.0

.. note::

	One DPDK DSA device can create 8 WQ at most. Below is an example, where DPDK DSA device will create one and
	eight WQ for DSA deivce 0000:e7:01.0 and 0000:ec:01.0. The value of “max_queues” is 1~8:
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:e7:01.0,max_queues=1 -- -i
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:ec:01.0,max_queues=8 -- -i

3. Bind DSA devices to kernel idxd driver, and configure Work Queue (WQ)::

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

Test Case 1: Basic test vhost/virtio-user split ring with 4K-pages and dsa dpdk driver
----------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test split ring when vhost uses the asynchronous 
enqueue operations with dsa dpdk driver and the mapping between vrings and dsa virtual channels is 1:1 in 4k-pages environment.

1. Bind one dsa device(6a:01.0) and one nic port(4f:00.1) to vfio-pci like common step 1-2.

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 -m 1024 --no-huge --file-prefix=vhost -a 0000:4f:00.1 -a 0000:6a:01.0,max_queues=1 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net,queues=1,dmas=[txq0]' -- -i --no-numa --socket-num=0 --lcore-dma=[lcore4@0000:6a:01.0-q0]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with 4K-pages::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-huge -m 1024 --file-prefix=virtio-user \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/vhost-net,queues=1 -- -i
	testpmd>set fwd mac
	testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

	testpmd>show port stats all

Test Case 2: Basic test vhost/virtio-user packed ring with 4K-pages and dsa dpdk driver
----------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test packed ring when vhost uses the asynchronous 
enqueue operations with dsa dpdk driver and the mapping between vrings and dsa virtual channels is 1:1 in 4k-pages environment.

1. Bind one dsa device(6a:01.0) and one nic port(4f:00.1) to vfio-pci like common step 1-2.

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 -m 1024 --no-huge --file-prefix=vhost -a 0000:4f:00.1 -a 0000:6a:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net,queues=1,dmas=[txq0]' -- -i --no-numa --socket-num=0 --lcore-dma=[lcore4@0000:6a:01.0-q0]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with 4K-pages::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-huge -m 1024 --file-prefix=virtio-user \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/vhost-net,packed_vq=1,queues=1 -- -i
	testpmd>set fwd mac
	testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

	testpmd>show port stats all

Test Case 3: PVP split ring multi-queues with 4K-pages and dsa dpdk driver
-----------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test split ring multi-queues when vhost uses the asynchronous 
enqueue operations with dsa dpdk driver and the mapping between vrings and dsa virtual channels is M:N in 4k-pages environment.

1. Bind 8 dsa device and one nic port to vfio-pci like common step 1-2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0 

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --no-huge -m 1024 -a 0000:4f:00.1 -a 0000:6a:01.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq6;txq7]' \
	--iova=va -- -i --nb-cores=5 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --no-numa --socket-num=0 \
	--lcore-dma=[lcore11@0000:6a:01.0-q0,lcore11@0000:6a:01.0-q7,lcore12@0000:6a:01.0-q1,lcore12@0000:6a:01.0-q2,lcore12@0000:6a:01.0-q3,lcore13@0000:6a:01.0-q2,lcore13@0000:6a:01.0-q3,lcore13@0000:6a:01.0-q4,lcore14@0000:6a:01.0-q2,lcore14@0000:6a:01.0-q3,lcore14@0000:6a:01.0-q4,lcore14@0000:6a:01.0-q5,lcore15@0000:6a:01.0-q0,lcore15@0000:6a:01.0-q1,lcore15@0000:6a:01.0-q2,lcore15@0000:6a:01.0-q3,lcore15@0000:6a:01.0-q4,lcore15@0000:6a:01.0-q5,lcore15@0000:6a:01.0-q6,lcore15@0000:6a:01.0-q7]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-huge -m 1024 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=8,server=1 \
	-- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd mac
	testpmd>start

4. Send imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log::

	testpmd>stop

6. restart vhost port and send imix pkts again, check get same throuhput as above::

	testpmd>start
	testpmd>show port stats all

7. Quit and relaunch vhost with diff M:N(M:1;M>N) mapping between vrings and dsa virtual channels with 1G hugepage::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:4f:00.1 -a 0000:6a:01.0 -a 0000:6f:01.0 -a 0000:74:01.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=5 --txd=1024 --rxd=1024 --txq=8 --rxq=8 \
	--lcore-dma=[lcore11@0000:6a:01.0-q0,lcore12@0000:6a:01.0-q0,lcore13@0000:6f:01.0-q1,lcore13@0000:74:01.0-q2,lcore14@0000:6f:01.0-q1,lcore14@0000:74:01.0-q2,lcore15@0000:6f:01.0-q1,lcore15@0000:74:01.0-q2]
	testpmd>set fwd mac
	testpmd>start

8. Rerun step 3-5.

Test Case 4: PVP packed ring multi-queues with 4K-pages and dsa dpdk driver
------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test packed ring multi-queues when vhost uses the asynchronous 
enqueue operations with dsa dpdk driver and the mapping between vrings and dsa virtual channels is M:N in 4k-pages environment.

1. Bind 8 dsa device and one nic port to vfio-pci like common step 1-2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0 

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --no-huge -m 1024 -a 0000:4f:00.1 -a 0000:6a:01.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq6;txq7]' \
	--iova=va -- -i --nb-cores=5 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --no-numa --socket-num=0 \
	--lcore-dma=[lcore11@0000:6a:01.0-q0,lcore11@0000:6a:01.0-q7,lcore12@0000:6a:01.0-q1,lcore12@0000:6a:01.0-q2,lcore12@0000:6a:01.0-q3,lcore13@0000:6a:01.0-q2,lcore13@0000:6a:01.0-q3,lcore13@0000:6a:01.0-q4,lcore14@0000:6a:01.0-q2,lcore14@0000:6a:01.0-q3,lcore14@0000:6a:01.0-q4,lcore14@0000:6a:01.0-q5,lcore15@0000:6a:01.0-q0,lcore15@0000:6a:01.0-q1,lcore15@0000:6a:01.0-q2,lcore15@0000:6a:01.0-q3,lcore15@0000:6a:01.0-q4,lcore15@0000:6a:01.0-q5,lcore15@0000:6a:01.0-q6,lcore15@0000:6a:01.0-q7]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-huge -m 1024 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=8,server=1 \
	-- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd mac
	testpmd>start

4. Send imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log::

	testpmd>stop

6. restart vhost port and send imix pkts again, check get same throuhput as above::

	testpmd>start
	testpmd>show port stats all

7. Quit and relaunch vhost with diff M:N(M:1;M>N) mapping between vrings and dsa virtual channels with 1G hugepage::::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:4f:00.1 -a 0000:6a:01.0 -a 0000:6f:01.0 -a 0000:74:01.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=5 --txd=1024 --rxd=1024 --txq=8 --rxq=8 \
	--lcore-dma=[lcore11@0000:6a:01.0-q0,lcore12@0000:6a:01.0-q0,lcore13@0000:6f:01.0-q1,lcore13@0000:74:01.0-q2,lcore14@0000:6f:01.0-q1,lcore14@0000:74:01.0-q2,lcore15@0000:6f:01.0-q1,lcore15@0000:74:01.0-q2]
	testpmd>set fwd mac
	testpmd>start

8. Rerun step 3-5.

Test Case 5: VM2VM split ring vhost-user/virtio-net 4K-pages and dsa dpdk driver test with tcp traffic
--------------------------------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net split ring mergeable path 
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue operations with dsa dpdk driver 
in 4k-pages environment.

1. Bind 1 dsa device to vfio-pci like common step 2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --no-huge -m 1024 --file-prefix=vhost -a 0000:6a:01.0,max_queues=2 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0],dma_ring_size=2048' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas=[txq0],dma_ring_size=2048' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --no-numa --socket-num=0 --lcore-dma=[lcore3@0000:6a:01.0-q0,lcore4@0000:6a:01.0-q1]
	testpmd>start

3. Launch VM1 and VM2::

	taskset -c 32 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

	taskset -c 33 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k_2,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

3. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

6. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1522, Port 1 should have rx packets above 1522::

	testpmd>show port xstats all

Test Case 6: VM2VM packed ring vhost-user/virtio-net 4K-pages and dsa dpdk driver test with tcp traffic
---------------------------------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net packed ring mergeable path 
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue operations with dsa dpdk driver 
in 4k-pages environment.

1. Bind 1 dsa device to vfio-pci like common step 2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0
 
2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --no-huge -m 1024 --file-prefix=vhost -a 0000:6a:01.0 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0],dma_ring_size=2048' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas=[txq0],dma_ring_size=2048' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --no-numa --socket-num=0 --lcore-dma=[lcore3@0000:6a:01.0-q0,lcore4@0000:6a:01.0-q1]
	testpmd>start

3. Launch VM1 and VM2::

	taskset -c 32 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

	taskset -c 33 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k_2,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

3. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

6. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1522, Port 1 should have rx packets above 1522::

	testpmd>show port xstats all

Test Case 7: vm2vm vhost/virtio-net split packed ring multi queues with 1G/4k-pages and dsa dpdk driver
---------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net multi-queues mergeable path when vhost uses the asynchronous enqueue operations with dsa dpdk driver.
And one virtio-net is split ring, the other is packed ring. The vhost run in 1G hugepages and the virtio-user run in 4k-pages environment.

1. Bind 2 dsa channel to vfio-pci like common step 2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:6a:01.0 -a 0000:6f:01.0 -a 0000:74:01.0 -a 0000:79:01.0 -a 0000:e7:01.0 -a 0000:ec:01.0 -a 0000:f1:01.0 -a 0000:f6:01.0 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore2@0000:6a:01.0-q0,lcore2@0000:6f:01.0-q1,lcore2@0000:74:01.0-q2,lcore2@0000:79:01.0-q3,lcore3@0000:6a:01.0-q0,lcore3@0000:74:01.0-q2,lcore3@0000:e7:01.0-q4,lcore3@0000:ec:01.0-q5,lcore3@0000:f1:01.0-q6,lcore3@0000:f6:01.0-q7,lcore4@0000:6f:01.0-q1,lcore4@0000:79:01.0-q3,lcore4@0000:6a:01.0-q1,lcore4@0000:6f:01.0-q2,lcore4@0000:74:01.0-q3,lcore4@0000:79:01.0-q4,lcore4@0000:e7:01.0-q5,lcore4@0000:ec:01.0-q6,lcore4@0000:f1:01.0-q7,lcore5@0000:f6:01.0-q0]
	testpmd>start

3. Launch VM qemu::

	taskset -c 32 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

	taskset -c 33 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k_2,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

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

Test Case 8: Basic test vhost/virtio-user split ring with 4K-pages and dsa kernel driver
----------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test split ring when vhost uses the asynchronous 
enqueue operations with dsa kernel driver and the mapping between vrings and dsa virtual channels is 1:1 in 4k-pages environment.

1. Bind one nic port to vfio-pci and one dsa device to idxd like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1

	#ls /dev/dsa,check wq configure, reset if exist
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py --reset 0

	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /dev/dsa #check wq configure success

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 -m 1024 --no-huge --file-prefix=vhost -a 0000:4f:00.1 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net,queues=1,dmas=[txq0]' -- -i --no-numa --socket-num=0 --lcore-dma=[lcore4@wq0.0]
	testpmd>start

3. Launch virtio-user with 4K-pages::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-huge -m 1024 --file-prefix=virtio-user \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/vhost-net,queues=1 -- -i
	testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

	testpmd>show port stats all

Test Case 9: Basic test vhost/virtio-user packed ring with 4K-pages and dsa dpdk driver
----------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test packed ring when vhost uses the asynchronous 
enqueue operations with dsa kernel driver and the mapping between vrings and dsa virtual channels is 1:1 in 4k-pages environment.

1. Bind one nic port to vfio-pci and one dsa device to idxd like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1

	#ls /dev/dsa,check wq configure, reset if exist
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py --reset 0

	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /dev/dsa #check wq configure success

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 -m 1024 --no-huge --file-prefix=vhost -a 0000:4f:00.1 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net,queues=1,dmas=[txq0]' -- -i --no-numa --socket-num=0 --lcore-dma=[lcore4@wq0.1]
	testpmd>start

3. Launch virtio-user with 4K-pages::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-huge -m 1024 --file-prefix=virtio-user \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/vhost-net,packed_vq=1,queues=1 -- -i
	testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

	testpmd>show port stats all

Test Case 10: PVP split ring multi-queues with 4K-pages and dsa kernel driver
--------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test split ring multi-queues when vhost uses the asynchronous 
enqueue operations with dsa kernel driver and the mapping between vrings and dsa virtual channels is M:N in 4k-pages environment.

1. Bind one nic port to vfio-pci and 8 dsa device to idxd like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1

	.ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 4
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 6
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 8
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 10
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 12
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 14
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -m 1024 --no-huge -a 0000:4f:00.1 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq6;txq7]' \
	--iova=va -- -i --nb-cores=5 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --no-numa --socket-num=0 \
	--lcore-dma=[lcore11@wq0.0,lcore11@wq0.7,lcore12@wq0.1,lcore12@wq0.2,lcore12@wq0.3,lcore13@wq0.2,lcore13@wq0.3,lcore13@wq0.4,lcore14@wq0.2,lcore14@wq0.3,lcore14@wq0.4,lcore14@wq0.5,lcore15@wq0.0,lcore15@wq0.1,lcore15@wq0.2,lcore15@wq0.3,lcore15@wq0.4,lcore15@wq0.5,lcore15@wq0.6,lcore15@wq0.7]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-huge -m 1024 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=8,server=1 \
	-- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd mac
	testpmd>start

4. Send imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log::

	testpmd>stop

6. restart vhost port and send imix pkts again, check get same throuhput as above::

	testpmd>start
	testpmd>show port stats all

7. Quit and relaunch vhost with diff M:N(M:1;M>N) mapping between vrings and dsa virtual channels::::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:4f:00.1 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=5 --txd=1024 --rxd=1024 --txq=8 --rxq=8 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.0,lcore13@wq0.1,lcore13@wq0.2,lcore14@wq0.1,lcore14@wq0.2,lcore15@wq0.1,lcore15@wq0.2]
	testpmd>set fwd mac
	testpmd>start

8. Rerun step 4-6.

Test Case 11: PVP packed ring multi-queues with 4K-pages and dsa kernel driver
---------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test packed ring multi-queues when vhost uses the asynchronous
enqueue operations with dsa kernel driver and the mapping between vrings and dsa virtual channels is M:N in 4k-pages environment.

1. Bind one nic port to vfio-pci and 8 dsa device to idxd like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1

	.ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 4
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 6
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 8
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 10
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 12
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 14
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -m 1024 --no-huge -a 0000:4f:00.1 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3]' \
	--iova=va -- -i --nb-cores=8 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --no-numa --socket-num=0 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq2.1,lcore13@wq4.2,lcore14@wq6.3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-huge -m 1024 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=8,server=1 \
	-- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd mac
	testpmd>start

4. Send imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log::

	testpmd>stop

6. restart vhost port and send imix pkts again, check get same throuhput as above::

	testpmd>start
	testpmd>show port stats all

7. Quit and relaunch vhost with diff M:N(M:1;M>N) mapping between vrings and dsa virtual channels::::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18  -a 0000:4f:00.1 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq6;txq7]' \
	--iova=va -- -i --nb-cores=5 --txd=1024 --rxd=1024 --txq=8 --rxq=8 \
	--lcore-dma=[lcore11@wq0.0,lcore11@wq0.7,lcore12@wq0.1,lcore12@wq0.2,lcore12@wq0.3,lcore13@wq0.2,lcore13@wq0.3,lcore13@wq0.4,lcore14@wq0.2,lcore14@wq0.3,lcore14@wq0.4,lcore14@wq0.5,lcore15@wq0.0,lcore15@wq0.1,lcore15@wq0.2,lcore15@wq0.3,lcore15@wq0.4,lcore15@wq0.5,lcore15@wq0.6,lcore15@wq0.7]
	testpmd>set fwd mac
	testpmd>start

8. Rerun step 4-6.

Test Case 12: VM2VM split ring vhost-user/virtio-net 4K-pages and dsa kernel driver test with tcp traffic
---------------------------------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net split ring mergeable path
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue operations with dsa dpdk driver
in 4k-pages environment.

1. Bind 1 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --no-huge -m 1024 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas=[txq0]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1 --no-numa --socket-num=0 --lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore3@wq0.2,lcore3@wq0.3]
	testpmd>start

3. Launch VM1 and VM2 on socket 1::

	taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k_2,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

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

Test Case 13: VM2VM packed ring vhost-user/virtio-net 4K-pages and dsa kernel driver test with tcp traffic
-----------------------------------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net packed ring mergeable path
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue operations with dsa dpdk driver
in 4k-pages environment.

1. Bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --no-huge -m 1024 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas=[txq0]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --no-numa --socket-num=0 --lcore-dma=[lcore3@wq0.0,lcore4@wq2.0]
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

	taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k_2,share=on \
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

Test Case 14: vm2vm vhost/virtio-net split packed ring multi queues with 1G/4k-pages and dsa kernel driver
-----------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net split and packed ring mergeable path when vhost uses the asynchronous enqueue operations with
dsa kernel driver. The vhost run in 1G hugepages and the virtio-user run in 4k-pages environment.

1. Bind 8 dsa device to idxd like common step 3::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 4
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 6
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 8
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 10
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 12
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 14
	ls /dev/dsa #check wq configure success

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore2@wq0.0,lcore2@wq2.1,lcore2@wq4.2,lcore2@wq6.3,lcore3@wq0.0,lcore3@wq4.2,lcore3@wq8.4,lcore3@wq10.5,lcore3@wq12.6,lcore3@wq14.7,lcore4@wq2.1,lcore4@wq6.3,lcore4@wq0.1,lcore4@wq2.2,lcore4@wq4.3,lcore4@wq6.4,lcore4@wq8.5,lcore4@wq10.6,lcore4@wq12.7,lcore5@wq14.0]
	testpmd>start

3. Launch VM qemu::

	taskset -c 32 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

	taskset -c 33 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k_2,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

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

Test Case 15: PVP split and packed ring dynamic queue number test with dsa dpdk and kernel driver
---------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test split and packed ring when vhost uses the asynchronous enqueue operations
with dsa dpdk and kernel driver and if the vhost-user can work well when the queue number dynamic change.

1. bind 2 dsa device to idxd, 2 dsa device to vfio-pci and one nic port to vfio-pci like common step 1-3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 2
	ls /dev/dsa #check wq configure success

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-huge -m 1024 --file-prefix=vhost -a 0000:4f:00.1 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=2,client=1,dmas=[txq0;txq1]' \
	--iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=2 --rxq=2 --no-numa --socket-num=0 --lcore-dma=[lcore3@wq0.0,lcore3@wq2.0]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with split ring mergeable in-order path by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-huge -m 1024 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=8,server=1 \
	-- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>set fwd mac
	testpmd>start

4. Send imix packets from packet generator with random ip, check perforamnce can get target.

5. Stop vhost port, check vhost RX and TX direction both exist packtes in 2 queues from vhost log.

6. Quit and relaunch vhost as below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-huge -m 1024 --file-prefix=vhost -a 0000:4f:00.1 -a 0000:e7:01.0 -a 0000:ec:01.0 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=4,client=1,dmas=[txq0;txq1;txq2;txq3]' \
	--iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=4 --rxq=4 --no-numa --socket-num=0 --lcore-dma=[lcore3@0000:e7:01.0-q0,lcore3@0000:e7:01.0-q1,lcore3@0000:ec:01.0-q2,lcore3@0000:ec:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

7. Send imix packets from packet generator with random ip, check perforamnce can get target.

8. Stop vhost port, check vhost RX and TX direction both exist packtes in 4 queues from vhost log.

9. Quit and relaunch vhost as below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-huge -m 1024 --file-prefix=vhost -a 0000:4f:00.1 -a 0000:e7:01.0 -a 0000:ec:01.0 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5]' \
	--iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --no-numa --socket-num=0 --lcore-dma=[lcore3@wq0.0,lcore3@wq2.0,lcore3@wq2.2,lcore3@0000:e7:01.0-q0,lcore3@0000:e7:01.0-q1,lcore3@0000:ec:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

10. Send imix packets from packet generator with random ip, check perforamnce can get target.

11. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

12. Quit and relaunch vhost with diff cahnnels as below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-huge -m 1024 --file-prefix=vhost -a 0000:4f:00.1 -a 0000:e7:01.0 -a 0000:ec:01.0 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --no-numa --socket-num=0 --lcore-dma=[lcore3@wq0.0,lcore3@wq0.1,lcore3@wq2.1,lcore3@wq2.0,lcore3@0000:e7:01.0-q1,lcore3@0000:ec:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

13. Send imix packets from packet generator with random ip, check perforamnce can get target.

14. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

15. Quit and relaunch virtio-user with packed ring mergeable in-order path by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-huge -m 1024 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=8,server=1 \
	-- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>set fwd mac
	testpmd>start

16. Rerun steps 4-5.

Test Case 16: VM2VM split ring vhost-user/virtio-net non-mergeable 4k-pages 16 queues dsa dpdk and kernel driver test with large packet payload valid check
-------------------------------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net split ring non-mergeable path when vhost uses the asynchronous enqueue operations with dsa dpdk
and kernel driver. The dynamic change of multi-queues number also test.

1. Bind 4 dsa device to vfio-pci and 4 dsa device to idxd like common step 2-3::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0 79:01.0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 4
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 6
	ls /dev/dsa #check wq configure success
	<dpdk dir># ./usertools/dpdk-devbind.py -u 0000:e7:01.0 0000:ec:01.0 0000:f1:01.0 0000:f6:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:e7:01.0 0000:ec:01.0 0000:f1:01.0 0000:f6:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 -m 1024 --no-huge --file-prefix=vhost  \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13;txq14;txq15]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13;txq14;txq15]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16 --no-numa --socket-num=0 \
	--lcore-dma=[lcore2@0000:e7:01.0-q0,lcore2@0000:e7:01.0-q1,lcore2@0000:ec:01.0-q0,lcore2@0000:ec:01.0-q1,lcore3@wq0.0,lcore3@wq2.0,lcore4@0000:e7:01.0-q4,lcore4@0000:e7:01.0-q5,lcore4@0000:ec:01.0-q4,lcore4@0000:ec:01.0-q5,lcore5@wq4.1,lcore5@wq2.1]
	testpmd>start

3. Launch VM1 and VM2::

	taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k_2,share=on \
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

	<VM1># scp <file>> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Quit vhost ports and relaunch vhost ports w/ diff dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 -m 1024 --no-huge --file-prefix=vhost -a 0000:6f:01.0 -a 0000:74:01.0 -a 0000:79:01.0 -a 0000:e7:01.0 -a 0000:f1:01.0 -a 0000:f6:01.0 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16 --no-numa --socket-num=0 --lcore-dma=[lcore2@0000:e7:01.0-q2,lcore2@0000:f1:01.0-q3,lcore2@0000:f1:01.0-q1,lcore2@wq4.2,lcore3@wq6.1,lcore3@wq6.3,lcore4@0000:e7:01.0-q2,lcore4@0000:f6:01.0-q5,lcore4@wq4.2,lcore4@wq6.0,lcore5@wq4.2,lcore5@wq6.0]
	testpmd>start

9. rerun step 6-7.

10. Quit vhost ports and relaunch vhost ports w/o dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 -m 1024 --no-huge --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16 --no-numa --socket-num=0
	testpmd>start

11. Rerun step 6-7.

12. Quit vhost ports and relaunch vhost ports with 1 queues::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 -m 1024 --no-huge --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1 --no-numa --socket-num=0
	testpmd>start

13. On VM1, set virtio device::

	<VM1># ethtool -L ens5 combined 1

14. On VM2, set virtio device::

	<VM2># ethtool -L ens5 combined 1

15. Rerun step 5-6.

Test Case 17: vm2vm packed ring vhost-user/virtio-net mergeable 16 queues dsa dpdk and kernel driver test with large packet payload valid check
--------------------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net packed ring mergeable path when vhost uses the asynchronous enqueue operations with dsa dpdk
and kernel driver. The dynamic change of multi-queues number also test.

1. Bind 4 dsa device to vfio-pci and 4 dsa device to idxd like common step 2-3::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0 79:01.0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 2
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 4
	<dpdk dir># ./<dpdk build dir>/drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 6
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	rm -rf vhost-net*
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 -m 1024 --no-huge --file-prefix=vhost -a 0000:e7:01.0 -a 0000:ec:01.0 -a 0000:f1:01.0 -a 0000:f6:01.0 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13;txq14;txq15]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=16,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;txq8;txq9;txq10;txq11;txq12;txq13;txq14;txq15]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16 --no-numa --socket-num=0 \
	--lcore-dma=[lcore2@wq0.0,lcore2@wq0.1,lcore2@wq2.0,lcore2@wq2.1,lcore3@wq0.1,lcore3@wq2.0,lcore3@0000:e7:01.0-q4,lcore3@0000:ec:01.0-q5,lcore3@0000:f1:01.0-q6,lcore3@0000:f6:01.0-q7,lcore4@0000:e7:01.0-q4,lcore4@0000:ec:01.0-q5,lcore4@0000:f1:01.0-q1,lcore4@wq2.0,lcore5@wq4.1,lcore5@wq2.0,lcore5@wq4.1,lcore5@wq6.2]
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	taskset -c 7 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	taskset -c 8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_4k_2,share=on \
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

	<VM1># scp <file>> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.
