.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=====================================================================
Loopback vhost-user/virtio-user server mode with DSA driver test plan
=====================================================================

Description
===========

Vhost asynchronous data path leverages DMA devices to offload memory copies from the CPU and it is implemented in an
asynchronous way. DPDK Vhost with DSA acceleration supports M:N mapping between virtqueues and DSA WQs. Specifically,
one DSA WQ can be used by multiple virtqueues and one virtqueue can offload copies to multiple DSA WQs at the same time.
Vhost async enqueue and async dequeue operation is supported in both split and packed ring.

This document provides the test plan for testing the following features when Vhost-user using asynchronous data path with
DSA driver (kernel IDXD driver and DPDK vfio-pci driver) in loopback vhost-user/virtio-user topology.
1. Virtio-user server mode is a feature to enable virtio-user as the server, vhost as the client, thus after vhost-user
is killed then relaunched, virtio-user can reconnect back to vhost-user again; at another hand, virtio-user also can
reconnect back to vhost-user after virtio-user is killed. This feature test cover different rx/tx paths with virtio 1.0
and virtio 1.1, includes split ring mergeable, non-mergeable, inorder mergeable, inorder non-mergeable, vector_rx path
and packed ring mergeable, non-mergeable, inorder non-mergeable, inorder mergeable, vectorized path.
2. Check payload valid after packets forwarding many times.
3. Stress test with large chain packets.

.. note::

	1.When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
	exceed IOMMU's max capability, better to use 1G guest hugepage.
	2.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd. In this patch,
	we enable asynchronous data path for vhostpmd. Asynchronous data path is enabled per tx/rx queue, and users need to specify
	the DMA device used by the tx/rx queue. Each tx/rx queue only supports to use one DMA device (This is limited by the
	implementation of vhostpmd), but one DMA device can be shared among multiple tx/rx queues of different vhost PMD ports.

Two PMD parameters are added:
- dmas:	specify the used DMA device for a tx/rx queue.(Default: no queues enable asynchronous data path)
- dma-ring-size: DMA ring size.(Default: 4096).

Here is an example:
--vdev 'eth_vhost0,iface=./s0,dmas=[txq0@0000:00.01.0;rxq0@0000:00.01.1],dma-ring-size=2048'

Prerequisites
=============

Topology
--------
	Test flow: Vhost-user <-> Virtio-user

General set up
--------------
1. Compile DPDK::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
	# ninja -C <dpdk build dir> -j 110
	For example:
	CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
	ninja -C x86_64-native-linuxapp-gcc -j 110

2. Get the PCI device of DUT, for example, 0000:6a:01.0 - 0000:f6:01.0 are DSA devices::

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
1. Bind DSA devices to DPDK vfio-pci driver::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <dsa_pci>

	For example, bind 2 DSA devices to vfio-pci driver:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:e7:01.0 0000:ec:01.0

.. note::

	One DPDK DSA device can create 8 WQ at most. Below is an example, where DPDK DSA device will create one WQ for deivce
	0000:e7:01.0 and eight WQs for 0000:ec:01.0. The value range of “max_queues” is 1~8 and the default value is 8:
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:e7:01.0,max_queues=1 -- -i
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:ec:01.0,max_queues=8 -- -i

2. Bind DSA devices to kernel idxd driver, and configure Work Queue (WQ)::

	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd <dsa_pci>
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q <wq_num> <dsa_idx>

.. note::

	dsa_idx: Index of DSA devices, where 0<=dsa_idx<=7, corresponding to 0000:6a:01.0 - 0000:f6:01.0
	wq_num: Number of work queues configured per DSA instance, where 1<=wq_num<=8

	Better to reset WQ when need operate DSA devices that bound to idxd drvier:
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py --reset <dsa_idx>
	You can check it by 'ls /dev/dsa'

	For example, bind 2 DSA devices to idxd driver and configure WQ:
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 1
	Check WQ by 'ls /dev/dsa' and can find "wq0.0 wq1.0 wq1.1 wq1.2 wq1.3"

Test Case 1: Loopback split ring server mode large chain packets stress test with dsa dpdk driver
-------------------------------------------------------------------------------------------------
This is a stress test case about forwarding large chain packets in loopback vhost-user/virtio-user split ring with server mode
when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost -a 0000:e7:01.0,max_queues=1 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q0],client=1' \
	--iova=va -- -i --nb-cores=1 --mbuf-size=65535

3. Launch virtio-user and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=testpmd0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048,server=1 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd> start

4. Send large packets from vhost and check packets can loop normally::

	testpmd> set txpkts 65535,65535
	testpmd> start tx_first 32
	testpmd> show port stats all

Test Case 2: Loopback packed ring server mode large chain packets stress test with dsa dpdk driver
--------------------------------------------------------------------------------------------------
This is a stress test case about forwarding large chain packets in loopback vhost-user/virtio-user packed ring with server mode
when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci as common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 -a 0000:f1:01.0,max_queues=1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q0],client=1' \
	--iova=va -- -i --nb-cores=1 --mbuf-size=65535

3. Launch virtio-user and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4  --file-prefix=testpmd0 --no-pci  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048,server=1 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd> start

4. Send large packets from vhost and check packets can loop normally::

	testpmd> set txpkts 65535,65535
	testpmd> start tx_first 32
	testpmd> show port stats all

Test Case 3: Loopback split ring inorder mergeable path multi-queues payload check with server mode and dsa dpdk driver
-----------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding large chain packets in loopback vhost-user/virtio-user split ring
inorder mergeable path multi-queues with server mode when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u e7:01.0
	./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:e7:01.0,max_queues=8 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;txq2@0000:e7:01.0-q0;txq3@0000:e7:01.0-q0;txq4@0000:e7:01.0-q1;txq5@0000:e7:01.0-q1;rxq2@0000:e7:01.0-q2;rxq3@0000:e7:01.0-q2;rxq4@0000:e7:01.0-q3;rxq5@0000:e7:01.0-q3;rxq6@0000:e7:01.0-q3;rxq7@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

Test Case 4: Loopback split ring mergeable path multi-queues payload check with server mode and dsa dpdk driver
---------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding large chain packets in loopback vhost-user/virtio-user split ring
mergeable path multi-queues with server mode when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u e7:01.0
	./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:e7:01.0,max_queues=8 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;txq2@0000:e7:01.0-q0;txq3@0000:e7:01.0-q0;txq4@0000:e7:01.0-q1;txq5@0000:e7:01.0-q1;rxq2@0000:e7:01.0-q2;rxq3@0000:e7:01.0-q2;rxq4@0000:e7:01.0-q3;rxq5@0000:e7:01.0-q3;rxq6@0000:e7:01.0-q3;rxq7@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

Test Case 5: Loopback split ring non-mergeable path multi-queues payload check with server mode and dsa dpdk driver
-------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user split ring
non-mergeable path multi-queues with server mode when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u e7:01.0
	./usertools/dpdk-devbind.py -b vfio-pci

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:e7:01.0,max_queues=8 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;txq2@0000:e7:01.0-q0;txq3@0000:e7:01.0-q0;txq4@0000:e7:01.0-q1;txq5@0000:e7:01.0-q1;rxq2@0000:e7:01.0-q2;rxq3@0000:e7:01.0-q2;rxq4@0000:e7:01.0-q3;rxq5@0000:e7:01.0-q3;rxq6@0000:e7:01.0-q3;rxq7@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,server=1 \
	-- -i --enable-hw-vlan-strip --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

Test Case 6: Loopback split ring inorder non-mergeable path multi-queues payload check with server mode and dsa dpdk driver
---------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user split ring
inorder non-mergeable path multi-queues with server mode when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u e7:01.0
	./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:e7:01.0,max_queues=8 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;txq2@0000:e7:01.0-q0;txq3@0000:e7:01.0-q0;txq4@0000:e7:01.0-q1;txq5@0000:e7:01.0-q1;rxq2@0000:e7:01.0-q2;rxq3@0000:e7:01.0-q2;rxq4@0000:e7:01.0-q3;rxq5@0000:e7:01.0-q3;rxq6@0000:e7:01.0-q3;rxq7@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring inorder non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

Test Case 7: Loopback split ring vectorized path multi-queues payload check with server mode and dsa dpdk driver
----------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user split ring
vectorized path multi-queues with server mode when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u e7:01.0
	./usertools/dpdk-devbind.py -b vfio-pci

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:e7:01.0,max_queues=8 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;txq2@0000:e7:01.0-q0;txq3@0000:e7:01.0-q0;txq4@0000:e7:01.0-q1;txq5@0000:e7:01.0-q1;rxq2@0000:e7:01.0-q2;rxq3@0000:e7:01.0-q2;rxq4@0000:e7:01.0-q3;rxq5@0000:e7:01.0-q3;rxq6@0000:e7:01.0-q3;rxq7@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring vectorized path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

Test Case 8: Loopback packed ring inorder mergeable path multi-queues payload check with server mode and dsa dpdk driver
------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding large chain packets in loopback vhost-user/virtio-user packed ring
inorder mergeable path multi-queues with server mode when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u e7:01.0
	./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:e7:01.0,max_queues=4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;txq2@0000:e7:01.0-q0;txq3@0000:e7:01.0-q0;txq4@0000:e7:01.0-q1;txq5@0000:e7:01.0-q1;rxq2@0000:e7:01.0-q2;rxq3@0000:e7:01.0-q2;rxq4@0000:e7:01.0-q3;rxq5@0000:e7:01.0-q3;rxq6@0000:e7:01.0-q3;rxq7@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

Test Case 9: Loopback packed ring mergeable path multi-queues payload check with server mode and dsa dpdk driver
----------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding large chain packets in loopback vhost-user/virtio-user packed ring
mergeable path multi-queues with server mode when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u e7:01.0
	./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:e7:01.0,max_queues=4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;txq2@0000:e7:01.0-q0;txq3@0000:e7:01.0-q0;txq4@0000:e7:01.0-q1;txq5@0000:e7:01.0-q1;rxq2@0000:e7:01.0-q2;rxq3@0000:e7:01.0-q2;rxq4@0000:e7:01.0-q3;rxq5@0000:e7:01.0-q3;rxq6@0000:e7:01.0-q3;rxq7@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd csum
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

Test Case 10: Loopback packed ring non-mergeable path multi-queues payload check with server mode and dsa dpdk driver
---------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user packed ring
non-mergeable path multi-queues with server mode when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u e7:01.0
	./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:e7:01.0,max_queues=4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;txq2@0000:e7:01.0-q0;txq3@0000:e7:01.0-q0;txq4@0000:e7:01.0-q1;txq5@0000:e7:01.0-q1;rxq2@0000:e7:01.0-q2;rxq3@0000:e7:01.0-q2;rxq4@0000:e7:01.0-q3;rxq5@0000:e7:01.0-q3;rxq6@0000:e7:01.0-q3;rxq7@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

Test Case 11: Loopback packed ring inorder non-mergeable path multi-queues payload check with server mode and dsa dpdk driver
-----------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user packed ring
inorder non-mergeable path multi-queues with server mode when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u e7:01.0
	./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:e7:01.0,max_queues=4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;txq2@0000:e7:01.0-q0;txq3@0000:e7:01.0-q0;txq4@0000:e7:01.0-q1;txq5@0000:e7:01.0-q1;rxq2@0000:e7:01.0-q2;rxq3@0000:e7:01.0-q2;rxq4@0000:e7:01.0-q3;rxq5@0000:e7:01.0-q3;rxq6@0000:e7:01.0-q3;rxq7@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring inorder non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

Test Case 12: Loopback packed ring vectorized path multi-queues payload check with server mode and dsa dpdk driver
------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user packed ring
vectorized path multi-queues with server mode when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u e7:01.0
	./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:e7:01.0,max_queues=4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;txq2@0000:e7:01.0-q0;txq3@0000:e7:01.0-q0;txq4@0000:e7:01.0-q1;txq5@0000:e7:01.0-q1;rxq2@0000:e7:01.0-q2;rxq3@0000:e7:01.0-q2;rxq4@0000:e7:01.0-q3;rxq5@0000:e7:01.0-q3;rxq6@0000:e7:01.0-q3;rxq7@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring vectorized path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

Test Case 13: Loopback packed ring vectorized path and ring size is not power of 2 multi-queues payload check with server mode and dsa dpdk driver
--------------------------------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user packed ring
vectorized path multi-queues with server mode and ring size is not power of 2 when vhost uses the asynchronous operations with dsa dpdk driver.

1. Bind 1 DSA device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u e7:01.0
	./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:e7:01.0,max_queues=4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;txq2@0000:e7:01.0-q0;txq3@0000:e7:01.0-q0;txq4@0000:e7:01.0-q1;txq5@0000:e7:01.0-q1;rxq2@0000:e7:01.0-q2;rxq3@0000:e7:01.0-q2;rxq4@0000:e7:01.0-q3;rxq5@0000:e7:01.0-q3;rxq6@0000:e7:01.0-q3;rxq7@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring vectorized path and ring size is not power of 2::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1025 --rxd=1025
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

Test Case 14: Loopback split ring server mode large chain packets stress test with dsa kernel driver
----------------------------------------------------------------------------------------------------
This is a stress test case about forwarding large chain packets in loopback vhost-user/virtio-user split ring with server mode
when vhost uses the asynchronous enqueue and dequeue operations with dsa kernel driver.

1. Bind 1 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost --no-pci \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.0],client=1' \
	--iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --mbuf-size=65535

3. launch virtio and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4  --file-prefix=testpmd0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048,server=1 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd> start

4. Send large packets from vhost and check the stats, packets can loop normally::

	testpmd> set txpkts 65535,65535
	testpmd> start tx_first 32
	testpmd> show port stats all

Test Case 15: Loopback packed ring server mode large chain packets stress test with dsa kernel driver
-----------------------------------------------------------------------------------------------------
This is a stress test case about forwarding large chain packets in loopback vhost-user/virtio-user packed ring with server mode
when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 1 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.0],client=1' \
	--iova=va -- -i --nb-cores=1 --mbuf-size=65535

3. launch virtio and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4  --file-prefix=testpmd0 --no-pci  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048,server=1 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd> start

4. Send large packets from vhost and check the stats, packets can loop normally::

	testpmd> set txpkts 65535,65535
	testpmd> start tx_first 32
	testpmd> show port stats all

Test Case 16: Loopback split ring inorder mergeable path multi-queues payload check with server mode and dsa kernel driver
--------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding large chain packets in loopback vhost-user/virtio-user split ring
inorder mergeable path multi-queues with server mode when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 2 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq1.0;rxq3@wq1.0;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost w/ diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024

8. Rerun step 4-6.

Test Case 17: Loopback split ring mergeable path multi-queues payload check with server mode and dsa kernel driver
------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding large chain packets in loopback vhost-user/virtio-user split ring
mergeable path multi-queues with server mode when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 2 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq1.0;rxq3@wq1.0;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost w/ diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024

8. Rerun step 4-6.

Test Case 18: Loopback split ring non-mergeable path multi-queues payload check with server mode and dsa kernel driver
----------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user split ring
non-mergeable path multi-queues with server mode when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 2 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq1.0;rxq3@wq1.0;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,server=1 \
	-- -i --enable-hw-vlan-strip --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost w/ diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024

8. Rerun step 4-6.

Test Case 19: Loopback split ring inorder non-mergeable path multi-queues payload check with server mode and dsa kernel driver
------------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user split ring
inorder non-mergeable path multi-queues with server mode when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 2 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq1.0;rxq3@wq1.0;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring inorder non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost w/ diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024

8. Rerun step 4-6.

Test Case 20: Loopback split ring vectorized path multi-queues payload check with server mode and dsa kernel driver
-------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user split ring
vectorized path multi-queues with server mode when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 2 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq1.0;rxq3@wq1.0;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring vectorized path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost w/ diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024

8. Rerun step 4-6.

Test Case 21: Loopback packed ring inorder mergeable path multi-queues payload check with server mode and dsa kernel driver
---------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding large chain packets in loopback vhost-user/virtio-user packed ring
inorder mergeable path multi-queues with server mode when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 8 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq1.0;rxq3@wq1.0;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost w/ diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

8.Rerun step 4-6.

Test Case 22: Loopback packed ring mergeable path multi-queues payload check with server mode and dsa kernel driver
-------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding large chain packets in loopback vhost-user/virtio-user packed ring
mergeable path multi-queues with server mode when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 8 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq1.0;rxq3@wq1.0;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost w/ diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

8.Rerun step 4-6.

Test Case 23: Loopback packed ring non-mergeable path multi-queues payload check with server mode and dsa kernel driver
-----------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user packed ring
non-mergeable path multi-queues with server mode when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 8 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq1.0;rxq3@wq1.0;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost w/ diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

8.Rerun step 4-6.

Test Case 24: Loopback packed ring inorder non-mergeable path multi-queues payload check with server mode and dsa kernel driver
-------------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user packed ring
inorder non-mergeable path multi-queues with server mode when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 8 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq1.0;rxq3@wq1.0;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring inorder non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost w/ diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

8.Rerun step 4-6.

Test Case 25: Loopback packed ring vectorized path multi-queues payload check with server mode and dsa kernel driver
--------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user packed ring
vectorized path multi-queues with server mode when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 8 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq1.0;rxq3@wq1.0;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring vectorized path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost w/ diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

8.Rerun step 4-6.

Test Case 26: Loopback packed ring vectorized path and ring size is not power of 2 multi-queues payload check with server mode and dsa kernel driver
----------------------------------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwarding chain packets in loopback vhost-user/virtio-user packed ring
vectorized path multi-queues with server mode and ring size is not power of 2 when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 8 DSA device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq1.0;rxq3@wq1.0;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring vectorized path and ring size is not power of 2::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1025 --rxd=1025
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost w/ diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

8.Rerun step 4-6.

Test Case 27: PV split and packed ring server mode test txonly mode with dsa dpdk and kernel driver
---------------------------------------------------------------------------------------------------

1. Bind 2 DSA device to idxd and 2 DSA device to vfio-pci like common step 1-2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 f1:01.0 f6:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 f6:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch vhost-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=2 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@0000:f1:01.0-q0;txq5@0000:f1:01.0-q0;rxq2@0000:f1:01.0-q1;rxq3@0000:f1:01.0-q1;rxq4@wq1.1;rxq5@wq1.1;rxq6@wq1.1;rxq7@wq1.1]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring mergeable inorder path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 --file-prefix=virtio-user --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd rxonly
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=/tmp/pdump-virtio-rx-0.pcap,mbuf-size=8000'
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large packets from vhost::

	testpmd> set fwd txonly
	testpmd> async_vhost tx poll completed on
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file.

7. Quit and relaunch vhost and rerun step 4-6.

8. Quit and relaunch virtio with packed ring mergeable inorder path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4-5 -n 4 --file-prefix=virtio-user --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

9. Stop vhost and rerun step 4-7.
