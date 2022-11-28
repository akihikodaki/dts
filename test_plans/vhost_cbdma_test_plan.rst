.. SPDX-License-Identifier: BSD-3-Clause
	Copyright(c) 2022 Intel Corporation

=============================================================
DMA-accelerated Tx/RX operations for vhost-user PMD test plan
=============================================================

Description
===========

This document provides the test plan for testing Vhost asynchronous data path with CBDMA driver in the PVP topology
environment with testpmd.

CBDMA is a kind of DMA engine, Vhost asynchronous data path leverages DMA devices to offload memory copies from the CPU
and it is implemented in an asynchronous way. As a result, large packet copy can be accelerated by the DMA engine, and
vhost can free CPU cycles for higher level functions. In addition, vhost supports M:N mapping between vrings and DMA
virtual channels. Specifically, one vring can use multiple different DMA channels and one DMA channel can be shared by
multiple vrings at the same time. From DPDK22.07, Vhost enqueue and dequeue operation with CBDMA channels is supported
in both split and packed ring.

.. note::

	1.When CBDMA device are bound to vfio driver, VA mode is the default and recommended.
	For PA mode, page by page mapping may exceed IOMMU's max capability, better to use 1G guest hugepage.
	2.By default, the xl710 Intel NIC does not activate the ETH RSS IPv4/TCP data stream. So we need to execute  `port config all rss ipv4-tcp` in testpmd.
	3.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd. In this patch,
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
	For virtio-user vdev parameter, you can refer to the DPDK docments:
	https://doc.dpdk.org/guides/nics/virtio.html#virtio-paths-selection-and-usage.

Prerequisites
=============

Topology
--------
	Test flow: TG-->NIC-->Vhost-->Virtio-->Vhost-->NIC-->TG

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
	For example:
	CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
	ninja -C x86_64-native-linuxapp-gcc -j 110

2. Get the PCI device ID and DMA device ID of DUT, for example, 0000:ca:00.0 is PCI device ID, 0000:00:01.0, 0000:00:01.1 are DMA device IDs::

	<dpdk dir># ./usertools/dpdk-devbind.py -s

	Network devices using kernel driver
	===================================
	0000:ca:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci

	DMA devices using kernel driver
	===============================
	0000:00:01.0 'Sky Lake-E CBDMA Registers 2021' drv=ioatdma unused=vfio-pci
	0000:00:01.1 'Sky Lake-E CBDMA Registers 2021' drv=ioatdma unused=vfio-pci

Test case
=========

Common steps
------------
1. Bind 1 NIC port and CBDMA device to vfio-pci::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DMA device id>

	For example, Bind 1 NIC port and 2 CBDMA device::
	./usertools/dpdk-devbind.py -b vfio-pci 0000:00:ca.0
	./usertools/dpdk-devbind.py -b vfio-pci 0000:00:01.0 0000:00:01.1

2. Send tcp imix packets [64,1518] to NIC by traffic generator::

	The imix packets include packet size [64, 128, 256, 512, 1024, 1518], and the format of packet is as follows.
	+-------------+-------------+-------------+-------------+
	| MAC         | MAC         | IPV4        | IPV4        |
	| Src address | Dst address | Src address | Dst address |
	|-------------|-------------|-------------|-------------|
	| Random MAC  | Virtio mac  | Random IP   | Random IP   |
	+-------------+-------------+-------------+-------------+
	All the packets in this test plan use the Virtio mac: 00:11:22:33:44:10.

Test Case 1: PVP split ring all path multi-queues vhost async operation test with each tx/rx queue using one CBDMA device
--------------------------------------------------------------------------------------------------------------------------
This case tests split ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations
with each tx/rx queue using 1 CBDMA device. Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 4 CBDMA device to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
	-a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=2,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.1;rxq0@0000:00:01.2;rxq1@0000:00:01.3]' \
	--iova=va -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and then check the throughput can get expected data::

	testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd> stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd> start
	testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=0,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=0,queues=2 \
	-- -i --enable-hw-vlan-strip --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

.. note::

	Rx offload(s) are requested when using split ring non-mergeable path. So add the parameter "--enable-hw-vlan-strip".

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=0,vectorized=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

11. Quit all testpmd and relaunch vhost with iova=pa by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
	-a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=2,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.1;rxq0@0000:00:01.2;rxq1@0000:00:01.3]' \
	--iova=pa -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

12. Rerun step 3-6.

Test Case 2: PVP split ring all path multi-queues vhost async operations test with one CBDMA device being shared among multiple tx/rx queues
---------------------------------------------------------------------------------------------------------------------------------------------
This case tests split ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations
with one CBDMA device being shared among multiple tx/rx queues. Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 4 CBDMA device to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=8,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.1;txq5@0000:00:01.1;txq6@0000:00:01.1;txq7@0000:00:01.1;rxq0@0000:00:01.0;rxq1@0000:00:01.0;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.1;rxq5@0000:00:01.1;rxq6@0000:00:01.1;rxq7@0000:00:01.1]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and then check the throughput can get expected data::

	testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd> stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd> start
	testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=0,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=0,queues=8 \
	-- -i --enable-hw-vlan-strip --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=0,vectorized=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

11. Quit all testpmd and relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=8,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.1;txq3@0000:00:01.1;txq4@0000:00:01.2;txq5@0000:00:01.2;txq6@0000:00:01.3;txq7@0000:00:01.3;rxq0@0000:00:01.0;rxq1@0000:00:01.0;rxq2@0000:00:01.1;rxq3@0000:00:01.1;rxq4@0000:00:01.2;rxq5@0000:00:01.2;rxq6@0000:00:01.3;rxq7@0000:00:01.3]' \
	--iova=va -- -i --nb-cores=6 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

12. Rerun step 7.

13. Quit all testpmd and relaunch vhost with iova=pa by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:ca:00.0 -a 0000:00:01.0 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=8,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.0;txq5@0000:00:01.0;txq6@0000:00:01.0;txq7@0000:00:01.0;rxq0@0000:00:01.0;rxq1@0000:00:01.0;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.0;rxq5@0000:00:01.0;rxq6@0000:00:01.0;rxq7@0000:00:01.0]' \
	--iova=pa -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

14. Rerun step 8.

Test Case 3: PVP split ring dynamic queue number vhost async operations with cbdma
----------------------------------------------------------------------------------
This case tests if the vhost-user async operation with cbdma channels can work normally when the queue number of split ring dynamic change. Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 8 CBDMA device to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir>#./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=./vhost_net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.1],dma-ring-size=32' \
	--iova=va -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

3. Launch virtio-user by below command::

	<dpdk dir>#./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=1,queues=8,server=1 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Send imix packets [64,1518] from packet generator with random ip, check perforamnce can get target.

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd> stop

6. Quit and relaunch vhost without CBDMA::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:ca:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=./vhost_net0,queues=8,client=1' \
	--iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

7. Rerun step 4-5.

8. Quit and relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=./vhost_net0,queues=8,client=1,dmas=[rxq0@0000:00:01.0;rxq1@0000:00:01.0;rxq2@0000:00:01.1;rxq3@0000:00:01.1],dma-ring-size=2048' \
	--iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

9. Rerun step 4-5.

10. Quit and relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.0;txq5@0000:00:01.0;txq6@0000:00:01.0;rxq2@0000:00:01.1;rxq3@0000:00:01.1;rxq4@0000:00:01.1;rxq5@0000:00:01.1;rxq6@0000:00:01.1;rxq7@0000:00:01.1],dma-ring-size=32' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

11. Rerun step 4-5.

12. Quit and relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 -a 0000:00:01.4 -a 0000:00:01.5 -a 0000:00:01.6 -a 0000:00:01.7 \
	-a 0000:80:01.0 -a 0000:80:01.1 -a 0000:80:01.2 -a 0000:80:01.3 -a 0000:80:01.4 -a 0000:80:01.5 -a 0000:80:01.6 -a 0000:80:01.7 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.1;txq2@0000:00:01.2;txq3@0000:00:01.3;txq4@0000:00:01.4;txq5@0000:00:01.5;txq6@0000:00:01.6;rxq2@0000:80:01.2;rxq3@0000:80:01.3;rxq4@0000:80:01.4;rxq5@0000:80:01.5;rxq6@0000:80:01.6;rxq7@0000:80:01.7]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

13. Start vhost port and rerun step 4-5.

Test Case 4: PVP packed ring all path multi-queues vhost async operation test with each tx/rx queue using one CBDMA device
---------------------------------------------------------------------------------------------------------------------------
This case tests packed ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 4 CBDMA device to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
	-a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=2,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.1;rxq0@0000:00:01.2;rxq1@0000:00:01.3]' \
	--iova=va -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=1,queues=2,packed_vq=1 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and then check the throughput can get expected data::

	testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd> stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd> start
	testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=0,queues=2,packed_vq=1 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=1,queues=2,packed_vq=1 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=0,queues=2,packed_vq=1 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=2 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

.. note::

	If building and running environment support (AVX512 || NEON) && in-order feature is negotiated && Rx mergeable
	is not negotiated && TCP_LRO Rx offloading is disabled && vectorized option enabled, packed virtqueue vectorized Rx path will be selected.

11. Relaunch virtio-user with vectorized path and ring size is not power of 2, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=2,queue_size=1025 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1025 --rxd=1025
	testpmd> set fwd csum
	testpmd> start

12. Quit all testpmd and relaunch vhost with iova=pa by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
	-a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=2,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.1;rxq0@0000:00:01.2;rxq1@0000:00:01.3]' \
	--iova=pa -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

13. Rerun step 11.

Test Case 5: PVP packed ring all path multi-queues vhost async operations test with one CBDMA device being shared among multiple tx/rx queues
----------------------------------------------------------------------------------------------------------------------------------------------
This case tests packed ring in each virtio path with multi-queues can work normally when vhost uses the asynchronous enqueue and dequeue operations.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 4 CBDMA device to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=8,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.1;txq5@0000:00:01.1;txq6@0000:00:01.1;txq7@0000:00:01.1;rxq0@0000:00:01.1;rxq1@0000:00:01.1;rxq2@0000:00:01.1;rxq3@0000:00:01.1;rxq4@0000:00:01.0;rxq5@0000:00:01.0;rxq6@0000:00:01.0;rxq7@0000:00:01.0]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=1,queues=8,packed_vq=1 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Send imix packets [64, 128, 256, 512, 1024, 1518] from packet generator as common step2, and then check the throughput can get expected data::

	testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd> stop

6. Restart vhost port and send imix packets again, then check the throuhput can get expected data::

	testpmd> start
	testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=0,queues=8,packed_vq=1 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=1,queues=8,packed_vq=1 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=0,queues=8,packed_vq=1 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=8 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

11. Relaunch virtio-user with vectorized path and ring size is not power of 2, then repeat step 4-6::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=8,queue_size=1025 \
	-- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1025 --rxd=1025
	testpmd> set fwd csum
	testpmd> start

12. Quit all testpmd and relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=8,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.1;txq3@0000:00:01.1;txq4@0000:00:01.2;txq5@0000:00:01.2;txq6@0000:00:01.3;txq7@0000:00:01.3;rxq0@0000:00:01.0;rxq1@0000:00:01.0;rxq2@0000:00:01.1;rxq3@0000:00:01.1;rxq4@0000:00:01.2;rxq5@0000:00:01.2;rxq6@0000:00:01.3;rxq7@0000:00:01.3]' \
	--iova=va -- -i --nb-cores=6 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

13. Rerun steps 11.

14. Quit all testpmd and relaunch vhost with iova=pa by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:ca:00.0 -a 0000:00:01.0 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=8,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.0;txq5@0000:00:01.0;txq6@0000:00:01.0;txq7@0000:00:01.0;rxq0@0000:00:01.0;rxq1@0000:00:01.0;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.0;rxq5@0000:00:01.0;rxq6@0000:00:01.0;rxq7@0000:00:01.0]' \
	--iova=pa -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

15. Rerun step 11.

Test Case 6: PVP packed ring dynamic queue number vhost async operations with cbdma
--------------------------------------------------------------------------------------
This case tests if the vhost-user async operation with cbdma channles can work normally when the queue number of split ring dynamic change. Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 8 CBDMA device to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=./vhost_net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.1],dma-ring-size=32' \
	--iova=va -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

3. Launch virtio-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=1,queues=8,server=1,packed_vq=1 \
	-- -i  --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Send imix packets [64,1518] from packet generator with random ip, check perforamnce can get target.

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

	testpmd> stop

6. Quit and relaunch vhost without CBDMA::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:ca:00.0 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=./vhost_net0,queues=8,client=1' \
	--iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

7. Rerun step 4-5.

8. Quit and relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 \
	--file-prefix=vhost --vdev 'net_vhost0,iface=./vhost_net0,queues=8,client=1,dmas=[rxq0@0000:00:01.0;rxq1@0000:00:01.1;rxq2@0000:00:01.0;rxq3@0000:00:01.1],dma-ring-size=2048' \
	--iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

9. Rerun step 4-5.

10. Quit and relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.0;txq5@0000:00:01.0;txq6@0000:00:01.0;rxq2@0000:00:01.1;rxq3@0000:00:01.1;rxq4@0000:00:01.1;rxq5@0000:00:01.1;rxq6@0000:00:01.1;rxq7@0000:00:01.1],dma-ring-size=32' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

11. Rerun step 4-5.

12. Quit and relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:ca:00.0 -a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 -a 0000:00:01.4 -a 0000:00:01.5 -a 0000:00:01.6 -a 0000:00:01.7 \
	-a 0000:80:01.0 -a 0000:80:01.1 -a 0000:80:01.2 -a 0000:80:01.3 -a 0000:80:01.4 -a 0000:80:01.5 -a 0000:80:01.6 -a 0000:80:01.7 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.1;txq2@0000:00:01.2;txq3@0000:00:01.3;txq4@0000:00:01.4;txq5@0000:00:01.5;txq6@0000:00:01.6;rxq2@0000:80:01.2;rxq3@0000:80:01.3;rxq4@0000:80:01.4;rxq5@0000:80:01.5;rxq6@0000:80:01.6;rxq7@0000:80:01.7]' \
	--iova=va -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

13. Start vhost port and rerun step 4-5.
