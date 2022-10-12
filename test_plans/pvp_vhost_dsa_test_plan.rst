.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

====================================================
PVP vhost async operation with DSA driver test plan
====================================================

Description
===========

This document provides the test plan for testing Vhost asynchronous
data path with DSA driver (kernel IDXD driver and DPDK vfio-pci driver)
in the PVP topology environment with testpmd.

DSA is a kind of DMA engine, Vhost asynchronous data path leverages DMA devices
to offload memory copies from the CPU and it is implemented in an asynchronous way.
Linux kernel and DPDK provide DSA driver (kernel IDXD driver and DPDK vfio-pci driver),
no matter which driver is used, DPDK DMA library is used in data-path to offload copies
to DSA, and the only difference is which driver configures DSA. It enables applications,
like OVS, to save CPU cycles and hide memory copy overhead, thus achieving higher throughput.
Vhost doesn't manage DMA devices and applications, like OVS, need to manage and configure DSA
devices. Applications need to tell vhost what DSA devices to use in every data path function call.
This design enables the flexibility for applications to dynamically use DMA channels in different
function modules, not limited in vhost. In addition, vhost supports M:N mapping between vrings
and DMA virtual channels. Specifically, one vring can use multiple different DMA channels
and one DMA channel can be shared by multiple vrings at the same time.

IOMMU impact:
If iommu off, idxd can work with iova=pa
If iommu on, kernel dsa driver only can work with iova=va by program IOMMU, can't use iova=pa(fwd not work due to pkts payload wrong).

..Note:
DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

Prerequisites
=============
Topology
--------
	Test flow: TG-->NIC-->Vhost-user-->Virtio-user-->Vhost-user-->NIC-->TG

Hardware
--------
	Supportted NICs: ALL

Software
--------
	Trex:http://trex-tgn.cisco.com/trex/release/v2.26.tar.gz

General set up
--------------
1. Compile DPDK::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
	# ninja -C <dpdk build dir> -j 110
	For example,
	CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
	ninja -C x86_64-native-linuxapp-gcc -j 110

2. Get the PCI device ID and DSA device ID of DUT, for example, 0000:6a:00.0 is PCI device ID, 0000:6a:01.0 - 0000:f6:01.0 are DSA device IDs::

	<dpdk dir># ./usertools/dpdk-devbind.py -s

	Network devices using kernel driver
	===================================
	0000:6a:00.0 'Ethernet Controller E810-C for QSFP 1592' drv=ice unused=vfio-pci

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
1. Bind 1 NIC port to vfio-pci::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>

	For example:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:4f.1

2. Bind DSA devices to DPDK vfio-pci driver::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DSA device id>

	For example, bind 2 DMA devices to vfio-pci driver:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:e7:01.0 0000:ec:01.0

.. note::

	One DPDK DSA device can create 8 WQ at most. Below is an example, where DPDK DSA device will create one and
	eight WQ for DSA deivce 0000:e7:01.0 and 0000:ec:01.0. The value of “max_queues” is 1~8:
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:e7:01.0,max_queues=1 -- -i
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:ec:01.0,max_queues=8 -- -i

3. Bind DSA devices to kernel idxd driver, and configure Work Queue (WQ)::

	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd <numDevices>
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q <numWq> <numDevices>

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

4. Send tcp imix packets [64,1518] to NIC by traffic generator::

	The imix packets include packet size [64, 128, 256, 512, 1024, 1518], and the format of packet is as follows.
	+-------------+-------------+-------------+-------------+
	| MAC		  |   MAC		| IPV4		  | IPV4		|
	| Src address | Dst address | Src address | Dst address |
	|-------------|-------------|-------------|-------------|
	| Random MAC  | Virtio mac  | Random IP   | Random IP   |
	+-------------+-------------+-------------+-------------+
	All the packets in this test plan use the Virtio mac: 00:11:22:33:44:10.

Test Case 1: PVP split ring all path multi-queues vhost async operation with 1:1 mapping between vrings and dsa dpdk driver channels
-------------------------------------------------------------------------------------------------------------------------------------
This case tests split ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver
and the mapping between vrings and virtual channels is 1:1. Both iova as VA and PA mode have been tested.

1. Bind 2 dsa device(f1:01.0,f6:01.0) and one nic port(6a:00.0) to vfio-pci like common step 1-2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 f6:01.0 6a:00.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=2,dmas=[txq0;txq1;rxq0;rxq1]' \
	--iova=va -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore3@0000:f1:01.0-q0,lcore3@0000:f1:01.0-q1,lcore3@0000:f1:01.0-q2,lcore3@0000:f1:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-14 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Send tcp imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd>start
	testpmd>show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-14 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-14 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=2 \
	-- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-14 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,queues=2 \
	-- -i --enable-hw-vlan-strip --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

10. Relaunch virtio-user with vector_rx path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-14 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,queues=2,vectorized=1 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

11. Quit all testpmd and relaunch vhost with pa mode by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=2 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=2,dmas=[txq0;txq1;rxq0;rxq1]' \
	--iova=pa -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore3@0000:f1:01.0-q0,lcore3@0000:f1:01.0-q1,lcore4@0000:f6:01.0-q0,lcore4@0000:f6:01.0-q1]
	testpmd>set fwd mac
	testpmd>start

12. Rerun step 3-6.

Test Case 2: PVP split ring all path multi-queues vhost async operations with M to 1 mapping between vrings and dsa dpdk driver channels
-----------------------------------------------------------------------------------------------------------------------------------------
This case tests split ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver
and the mapping between vrings and virtual channels is M:1. Both iova as VA and PA mode have been tested.

1. Bind 2 dsa device and one nic port to vfio-pci like comon step 1-2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0 f1:01.0 f6:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q1,lcore13@0000:f1:01.0-q2,lcore14@0000:f1:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Send tcp imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd>start
	testpmd>show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,queues=8 \
	-- -i --enable-hw-vlan-strip --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

10. Relaunch virtio-user with vector_rx path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,queues=8,vectorized=1 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

11. Quit all testpmd and relaunch vhost with pa mode by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=1 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=pa -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f6:01.0-q0,lcore13@0000:f6:01.0-q1,lcore14@0000:f6:01.0-q2]
	testpmd>set fwd mac
	testpmd>start

12. Rerun step 7.

Test Case 3: PVP split ring dynamic queues vhost async operation with dsa dpdk driver channels
-------------------------------------------------------------------------------------------------
This case tests if the vhost-user async operation with dsa dpdk driver can work normally when the queue number of split ring dynamic change. Both iova as VA and PA mode have been tested.

1. Bind 2 dsa devices and 1 NIC port to vfio-pci like common step 1-2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:6a:00.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 f6:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3]' \
	--iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q1,lcore13@0000:f1:01.0-q2,lcore14@0000:f1:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-9 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/vhost-net0,mrg_rxbuf=1,in_order=1,queues=8,server=1 \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>set fwd csum
	testpmd>start

4. Send tcp imix packets[64,1518] from packet generator with random ip, check perforamnce can get target.

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Quit and relaunch vhost without dsa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:18:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1' \
	--iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd>set fwd mac
	testpmd>start

7. Rerun step 4-5.

8. Quit and relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[rxq0;rxq1;rxq2;rxq3]' \
	--iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q1,lcore13@0000:f1:01.0-q2,lcore14@0000:f1:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

9. Rerun step 4-5.

10. Quit and relaunch vhost with with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=8 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=2 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore11@0000:f1:01.0-q1,lcore12@0000:f1:01.0-q1,lcore12@0000:f1:01.0-q2,lcore12@0000:f1:01.0-q3,lcore12@0000:f1:01.0-q4,lcore12@0000:f1:01.0-q5,lcore12@0000:f1:01.0-q6,lcore12@0000:f1:01.0-q7]
	testpmd>set fwd mac
	testpmd>start

11. Rerun step 4-5.

12. Quit and relaunch vhost with with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q1,lcore12@0000:f1:01.0-q2,lcore13@0000:f1:01.0-q3,lcore13@0000:f6:01.0-q0,lcore13@0000:f6:01.0-q1,lcore13@0000:f6:01.0-q2,lcore14@0000:f6:01.0-q0,lcore14@0000:f6:01.0-q1,lcore14@0000:f6:01.0-q2,lcore14@0000:f6:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

13. Rerun step 4-5.

14. Quit and relaunch vhost with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q1,lcore13@0000:f1:01.0-q2,lcore14@0000:f1:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

15. Rerun step 4-5, then start vhost port.

16. Relaunch virtio-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-9 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/vhost-net0,mrg_rxbuf=0,in_order=0,queues=8,server=1 \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>set fwd csum
	testpmd>start

17. Rerun step 4-5.

18. Quit and relaunch vhost with iova=pa by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=2 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;rxq1;rxq2;rxq3]' \
	--iova=pa -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=4 --rxq=4 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q0,lcore13@0000:f1:01.0-q1,lcore14@0000:f1:01.0-q1,lcore15@0000:f1:01.0-q1]
	testpmd>set fwd mac
	testpmd>start

19. Rerun step 4-5.

Test Case 4: PVP packed ring all path mulit-queues vhost async operation with 1:1 mapping between vrings and dsa dpdk driver channels
----------------------------------------------------------------------------------------------------------------------------------------
This case tests packed ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver
and the mapping between vrings and virtual channels is 1:1. Both iova as VA and PA mode have been tested.

1. Bind 2 dsa device(f1:01.0,f6:01.0) and one nic port(6a:00.0) to vfio-pci like common step 1-2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 f6:01.0 6a:00.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-14 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=2,dmas=[txq0;txq1;rxq0;rxq1]' \
	--iova=va -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore3@0000:f1:01.0-q0,lcore3@0000:f1:01.0-q1,lcore3@0000:f1:01.0-q2,lcore3@0000:f1:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=4 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Send tcp imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd>start
	testpmd>show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,packed_vq=1,queues=4 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,packed_vq=1,queues=4 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,packed_vq=1,queues=4 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

10. Relaunch virtio-user with vector_rx path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,packed_vq=1,queues=4,vectorized=1 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

11. Relaunch virtio-user with vector_rx path and ring size is not power of 2, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,packed_vq=1,queues=4,vectorized=1,queue_size=1025 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1025 --rxd=1025
	testpmd>set fwd csum
	testpmd>start

12. Quit all testpmd and relaunch vhost with pa mode by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-14 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=2 -a 0000:f6:01.0,max_queues=2 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=2,dmas=[txq0;txq1;rxq0;rxq1]' \
	--iova=pa -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore3@0000:f1:01.0-q0,lcore3@0000:f1:01.0-q1,lcore4@0000:f6:01.0-q0,lcore4@0000:f6:01.0-q1]
	testpmd>set fwd mac
	testpmd>start

13. Rerun step 3-6.

Test Case 5: PVP packed ring all path mulit-queues vhost async operation with M:1 mapping between vrings and dsa dpdk driver channels
----------------------------------------------------------------------------------------------------------------------------------------
This case tests packed ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver
and the mapping between vrings and virtual channels is M:1. Both iova as VA and PA mode have been tested.

1. Bind 2 dsa device and one nic port to vfio-pci like comon step 1-2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0 f1:01.0 f6:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-12 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q1,lcore13@0000:f1:01.0-q2,lcore14@0000:f1:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Send tcp imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd>start
	testpmd>show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,packed_vq=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,packed_vq=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,packed_vq=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

10. Relaunch virtio-user with vector_rx path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,packed_vq=1,queues=8,vectorized=1 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

11. Relaunch virtio-user with vector_rx path and ring size is not power of 2, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,packed_vq=1,queues=8,vectorized=1,queue_size=1025 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1025 --rxd=1025
	testpmd>set fwd csum
	testpmd>start

12. Quit all testpmd and relaunch vhost with pa mode by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=1 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=pa -- -i --nb-cores=2 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f6:01.0-q0,lcore12@0000:f6:01.0-q1,lcore12@0000:f6:01.0-q2,lcore12@0000:f6:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

13. Rerun step 7.

Test Case 6: PVP packed ring dynamic queues vhost async operation with dsa dpdk driver channels
-------------------------------------------------------------------------------------------------
This case tests if the vhost-user async operation with dsa dpdk driver can work normally when the queue number of split ring dynamic change. Both iova as VA and PA mode have been tested.

1. Bind 2 dsa devices and 1 NIC port to vfio-pci like common step 1-2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:6a:00.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 f6:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3]' \
	--iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q1,lcore13@0000:f1:01.0-q2,lcore14@0000:f1:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=8,server=1 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Send tcp imix packets[64,1518] from packet generator with random ip, check perforamnce can get target.

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Quit and relaunch vhost without dsa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:18:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1' \
	--iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd>set fwd mac
	testpmd>start

7. Rerun step 4-5.

8. Quit and relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[rxq0;rxq1;rxq2;rxq3]' \
	--iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q1,lcore13@0000:f1:01.0-q2,lcore14@0000:f1:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

9. Rerun step 4-5.

10. Quit and relaunch vhost with with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=8 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=2 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore11@0000:f1:01.0-q1,lcore12@0000:f1:01.0-q1,lcore12@0000:f1:01.0-q2,lcore12@0000:f1:01.0-q3,lcore12@0000:f1:01.0-q4,lcore12@0000:f1:01.0-q5,lcore12@0000:f1:01.0-q6,lcore12@0000:f1:01.0-q7]
	testpmd>set fwd mac
	testpmd>start

11. Rerun step 4-5.

12. Quit and relaunch vhost with with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q1,lcore12@0000:f1:01.0-q2,lcore13@0000:f1:01.0-q3,lcore13@0000:f6:01.0-q0,lcore13@0000:f6:01.0-q1,lcore13@0000:f6:01.0-q2,lcore14@0000:f6:01.0-q0,lcore14@0000:f6:01.0-q1,lcore14@0000:f6:01.0-q2,lcore14@0000:f6:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

13. Rerun step 4-5.

14. Quit and relaunch vhost with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=4 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q1,lcore13@0000:f1:01.0-q2,lcore14@0000:f1:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

15. Rerun step 4-5, then start vhost port.

16. Relaunch virtio-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-9 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/vhost-net0,mrg_rxbuf=0,in_order=0,packed_vq=1,queues=8,server=1 \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>set fwd csum
	testpmd>start

17. Rerun step 4-5.

18. Quit and relaunch vhost with iova=pa by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=2 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;rxq1;rxq2;rxq3]' \
	--iova=pa -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=4 --rxq=4 \
	--lcore-dma=[lcore11@0000:f1:01.0-q0,lcore12@0000:f1:01.0-q0,lcore13@0000:f1:01.0-q1,lcore14@0000:f1:01.0-q1,lcore15@0000:f1:01.0-q1]
	testpmd>set fwd mac
	testpmd>start

19. Rerun step 4-5.

Test Case 7: PVP split ring all path multi-queues vhost async operation with 1:1 mapping between vrings and dsa kernel driver channels
--------------------------------------------------------------------------------------------------------------------------------------
This case tests split ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations with dsa kernel driver
and the mapping between vrings and virtual channels is 1:1.

1. Bind 1 dsa device to idxd driver and one nic port to vfio-pci like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0

	#ls /dev/dsa,check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-14 --file-prefix=vhost -a 0000:6a:00.0 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=2,dmas=[txq0;txq1;rxq0;rxq1]' \
	--iova=va -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore11@wq0.1,lcore11@wq0.2,lcore11@wq0.3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd mac
	testpmd>start

4. Send tcp imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd>start
	testpmd>show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,queues=2 \
	-- -i --enable-hw-vlan-strip --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

10. Relaunch virtio-user with vector_rx path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,vectorized=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

Test Case 8: PVP split ring all path multi-queues vhost async operation with M:1 mapping between vrings and dsa kernel driver channels
--------------------------------------------------------------------------------------------------------------------------------------
This case tests split ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations with dsa kernel driver
and the mapping between vrings and virtual channels is M:1.

1. Bind 1 dsa device to idxd driver and one nic port to vfio-pci like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.1,lcore13@wq0.2,lcore14@wq0.3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Send imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd>start
	testpmd>show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,queues=8 \
	-- -i --enable-hw-vlan-strip --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

10. Relaunch virtio-user with vector_rx path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,vectorized=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

Test Case 9: PVP split ring dynamic queues vhost async operation with dsa kernel driver channels
--------------------------------------------------------------------------------------------------
This case tests if the vhost-user async operation with dsa kernel driver can work normally when the queue number of split ring dynamic change.

1. Bind 2 dsa device to idxd driver and 1 NIC port to vfio-pci like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --file-prefix=vhost -a 0000:6a:00.0 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3]' \
	--iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.1,lcore13@wq0.2,lcore14@wq0.3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-9 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/vhost-net0,mrg_rxbuf=1,in_order=1,queues=8,server=1 \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>set fwd mac
	testpmd>start

4. Send tcp imix packets[64,1518] from packet generator with random ip, check perforamnce can get target.

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Quit and relaunch vhost without dsa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:18:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1' \
	--iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd>set fwd mac
	testpmd>start

7. Rerun step 4-5.

8. Quit and relaunch vhost with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[rxq0;rxq1;rxq2;rxq3]' \
	--iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.1,lcore13@wq0.2,lcore14@wq0.3]
	testpmd>set fwd mac
	testpmd>start

9. Rerun step 4-5.

10. Quit and relaunch vhost with with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=2 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore11@wq0.1,lcore12@wq0.1,lcore12@wq0.2,lcore12@wq0.3,lcore12@wq0.4,lcore12@wq0.5,lcore12@wq0.6,lcore12@wq0.7]
	testpmd>set fwd mac
	testpmd>start

11. Rerun step 4-5.

12. Quit and relaunch vhost with with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.0,lcore12@wq0.1,lcore12@wq0.2,lcore13@wq0.3,lcore13@wq1.0,lcore13@wq1.1,lcore13@wq1.2,lcore14@wq1.0,lcore14@wq1.1,lcore14@wq1.2,lcore14@wq1.3]
	testpmd>set fwd mac
	testpmd>start

13. Rerun step 4-5.

14. Quit and relaunch vhost with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=4 --rxq=4 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.1,lcore13@wq0.2,lcore14@wq0.3]
	testpmd>set fwd mac
	testpmd>start

15. Rerun step 4-5, then start vhost port

16. Relaunch virtio-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/vhost-net0,mrg_rxbuf=0,in_order=0,queues=8,server=1 \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>set fwd mac
	testpmd>start

17. Rerun step 4-5.

Test Case 10: PVP packed ring all path multi-queues vhost async operation with 1:1 mapping between vrings and dsa kernel driver channels
-------------------------------------------------------------------------------------------------------------------------------------------
This case tests packed ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations with dsa kernel driver and the mapping between vrings and virtual channels is 1:1.

1. Bind 2 dsa device to idxd driver and one nic port to vfio-pci like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0

	#ls /dev/dsa,check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 1
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-14 --file-prefix=vhost -a 0000:6a:00.0 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=2,dmas=[txq0;txq1;rxq0;rxq1]' \
	--iova=va -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore11@wq0.1,lcore11@wq1.0,lcore11@wq1.1]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Send tcp imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd>start
	testpmd>show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,packed_vq=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,packed_vq=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,packed_vq=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

10. Relaunch virtio-user with vector_rx path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=2,packed_vq=1,vectorized=1 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

11. Relaunch virtio-user with vector_rx path and ring size is not power of 2, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=2,packed_vq=1,vectorized=1,queue_size=1025 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1025 --rxd=1025
	testpmd>set fwd csum
	testpmd>start

Test Case 11: PVP packed ring all path multi-queues vhost async operation with M:1 mapping between vrings and dsa kernel driver channels
------------------------------------------------------------------------------------------------------------------------------------------
This case tests packed ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations with dsa kernel driver and the mapping between vrings and virtual channels is M:1.

1. Bind 1 dsa device to idxd driver and one nic port to vfio-pci like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.1,lcore13@wq0.2,lcore14@wq0.3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Send tcp imix packets [64,1518] from packet generator, check the throughput can get expected data::

	testpmd>show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd>start
	testpmd>show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,packed_vq=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,packed_vq=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,packed_vq=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

10. Relaunch virtio-user with vector_rx path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=8,packed_vq=1,vectorized=1 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

11. Relaunch virtio-user with vector_rx path and ring size is not power of 2, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=8,packed_vq=1,vectorized=1,queue_size=1025 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1025 --rxd=1025
	testpmd>set fwd csum
	testpmd>start

Test Case 12: PVP packed ring dynamic queues vhost async operation with dsa kernel driver channels
---------------------------------------------------------------------------------------------------
This case tests if the vhost-user async operation with dsa kernel driver can work normally when the queue number of packed ring dynamic change.

1. Bind 2 dsa device to idxd driver and 1 NIC port to vfio-pci like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --file-prefix=vhost -a 0000:6a:00.0 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3]' \
	--iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.1,lcore13@wq0.2,lcore14@wq0.3]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 1-5 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=8,server=1 \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>set fwd mac
	testpmd>start

4. Send tcp imix packets[64,1518] from packet generator with random ip, check perforamnce can get target.

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd>stop

6. Quit and relaunch vhost without dsa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:18:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1' \
	--iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd>set fwd mac
	testpmd>start

7. Rerun step 4-5.

8. Quit and relaunch vhost with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[rxq0;rxq1;rxq2;rxq3]' \
	--iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.1,lcore13@wq0.2,lcore14@wq0.3]
	testpmd>set fwd mac
	testpmd>start

9. Rerun step 4-5.

10. Quit and relaunch vhost with with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=2 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore11@wq0.1,lcore12@wq0.1,lcore12@wq0.2,lcore12@wq0.3,lcore12@wq0.4,lcore12@wq0.5,lcore12@wq0.6,lcore12@wq0.7]
	testpmd>set fwd mac
	testpmd>start

11. Rerun step 4-5.

12. Quit and relaunch vhost with with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.0,lcore12@wq0.1,lcore12@wq0.2,lcore13@wq0.3,lcore13@wq1.0,lcore13@wq1.1,lcore13@wq1.2,lcore14@wq1.0,lcore14@wq1.1,lcore14@wq1.2,lcore14@wq1.3]
	testpmd>set fwd mac
	testpmd>start

13. Rerun step 4-5.

14. Quit and relaunch vhost with diff channel by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:6a:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=4 --rxq=4 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.1,lcore13@wq0.2,lcore14@wq0.3]
	testpmd>set fwd mac
	testpmd>start

15. Rerun step 4-5, then start vhost port.

16. Quit and relaunch virtio-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,packed_vq=1,queues=8,server=1 \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>set fwd csum
	testpmd>start

17. Rerun step 4-5.

Test Case 13: PVP split and packed ring dynamic queues vhost async operation with dsa dpdk and kernel driver channels
-----------------------------------------------------------------------------------------------------------------------
This case tests if the vhost-user async operation with dsa kernel driver and dsa dpdk driver can work normally when the queue number of split ring and packed ring dynamic change.

1. Bind 2 dsa device to idxd driver, 2 dsa device and 1 NIC port to vfio-pci like common step 1-3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 f6:01.0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 1
	ls /dev/dsa #check wq configure success

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1]' \
	--iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=2 --rxq=2 --lcore-dma=[lcore11@wq0.0,lcore11@wq1.0]
	testpmd>set fwd mac
	testpmd>start

3. Launch virtio-user with split ring mergeable in-order path by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=8,server=1 \
	-- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>set fwd csum
	testpmd>start

4. Send tcp imix packets from packet generator with random ip, check perforamnce can get target.

5. Stop vhost port, check vhost RX and TX direction both exist packtes in 2 queues from vhost log.

6. Quit and relaunch vhost as below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=2 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;rxq0;rxq1;rxq2;rxq3]' \
	--iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=4 --rxq=4 --lcore-dma=[lcore11@0000:f1:01.0-q0,lcore11@0000:f1:01.0-q1,lcore11@0000:f6:01.0-q2,lcore11@0000:f6:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

7. Send imix packets from packet generator with random ip, check perforamnce can get target.

8. Stop vhost port, check vhost RX and TX direction both exist packtes in 4 queues from vhost log.

9. Quit and relaunch vhost as below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=2 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --lcore-dma=[lcore11@wq0.0,lcore11@wq1.0,lcore12@wq1.2,lcore12@0000:f1:01.0-q0,lcore13@0000:f1:01.0-q1,lcore14@0000:f6:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

10. Send imix packets from packet generator with random ip, check perforamnce can get target.

11. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

12. Quit and relaunch virtio-user with packed ring mergeable in-order path by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=8,server=1 \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>set fwd mac
	testpmd>start

13. Start vhost port and rerun steps 10-11.

14. Quit and relaunch vhost with diff cahnnels as below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:6a:00.0 -a 0000:f1:01.0,max_queues=2 -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --lcore-dma=[lcore11@wq0.0,lcore11@wq0.1,lcore12@wq1.1,lcore13@wq1.0,lcore14@0000:f1:01.0-q1,lcore14@0000:f6:01.0-q3]
	testpmd>set fwd mac
	testpmd>start

15. Send imix packets from packet generator with random ip, check perforamnce can get target.

16. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.
