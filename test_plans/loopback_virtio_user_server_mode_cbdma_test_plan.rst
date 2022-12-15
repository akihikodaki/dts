.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

===========================================================
Loopback vhost/virtio-user server mode with CBDMA test plan
===========================================================

Description
===========

CBDMA is a kind of DMA engine, Vhost asynchronous data path leverages DMA devices
to offload memory copies from the CPU and it is implemented in an asynchronous way.
As a result, large packet copy can be accelerated by the DMA engine, and vhost can
free CPU cycles for higher level functions.

This document provides the test plan for testing the following features when Vhost-user using asynchronous data path with
CBDMA channels in loopback vhost-user/virtio-user topology.
1. Virtio-user server mode is a feature to enable virtio-user as the server, vhost as the client, thus after vhost-user
is killed then relaunched, virtio-user can reconnect back to vhost-user again; at another hand, virtio-user also can
reconnect back to vhost-user after virtio-user is killed. This feature test need cover different rx/tx paths with
virtio 1.0 and virtio 1.1, includes split ring mergeable, non-mergeable, inorder mergeable, inorder non-mergeable,
vector_rx path and packed ring mergeable, non-mergeable, inorder non-mergeable, inorder mergeable, vectorized path.
2. Check payload valid after packets forwarding many times.
3. Stress test with large chain packets.

.. note::

	1. When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
	exceed IOMMU's max capability, better to use 1G guest hugepage.
	2. DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd. In this patch,
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
Test flow: Virtio-user-->Vhost-user-->Testpmd-->Vhost-user-->Virtio-user

General set up
--------------
1. Compile DPDK::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
	# ninja -C <dpdk build dir> -j 110
	For example:
	CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
	ninja -C x86_64-native-linuxapp-gcc -j 110

2. Get the PCI device ID and DMA device ID of DUT, for example, 0000:18:00.0 is PCI device ID, 0000:00:01.0, 0000:00:01.1 is DMA device ID::

	<dpdk dir># ./usertools/dpdk-devbind.py -s

	Network devices using kernel driver
	===================================
	0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci

	DMA devices using kernel driver
	===============================
	0000:00:01.0 'Sky Lake-E CBDMA Registers 2021' drv=ioatdma unused=vfio-pci
	0000:00:01.1 'Sky Lake-E CBDMA Registers 2021' drv=ioatdma unused=vfio-pci

Test case
=========

Common steps
------------
1. Bind 1 NIC port and CBDMA channels to vfio-pci::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DMA device id>

	For example, bind 2 CBDMA channels:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:01.0 0000:00:01.1

Test Case 1: Loopback packed ring inorder mergeable path multi-queues payload check with server mode and cbdma enable
---------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user packed ring
inorder mergeable path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 1 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 -a 0000:00:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.0;txq5@0000:00:01.0;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.0;rxq5@0000:00:01.0;rxq6@0000:00:01.0;rxq7@0000:00:01.0]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte and the payload in receive packets are same in each pcap file.

Test Case 2: Loopback packed ring mergeable path multi-queues payload check with server mode and cbdma enable
-------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user packed ring
mergeable path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 2 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.1;txq5@0000:00:01.1;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.1;rxq5@0000:00:01.1;rxq6@0000:00:01.1;rxq7@0000:00:01.1]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte and the payload in receive packets are same in each pcap file.

Test Case 3: Loopback packed ring inorder non-mergeable path multi-queues payload check with server mode and cbdma enable
-------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user packed ring
inorder non-mergeable path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 4 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 -a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.1;txq3@0000:00:01.1;txq4@0000:00:01.2;txq5@0000:00:01.2;rxq2@0000:00:01.1;rxq3@0000:00:01.1;rxq4@0000:00:01.2;rxq5@0000:00:01.2;rxq6@0000:00:01.3;rxq7@0000:00:01.3]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring inorder non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte and the payload in receive packets are same in each pcap file.

Test Case 4: Loopback packed ring non-mergeable path multi-queues payload check with server mode and cbdma enable
-----------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user packed ring
non-mergeable path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 8 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 -a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.1;txq2@0000:00:04.2;txq3@0000:00:04.3;txq4@0000:00:04.4;txq5@0000:00:04.5;rxq2@0000:00:04.2;rxq3@0000:00:04.3;rxq4@0000:00:04.4;rxq5@0000:00:04.5;rxq6@0000:00:04.6;rxq7@0000:00:04.7]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte and the payload in receive packets are same in each pcap file.

Test Case 5: Loopback packed ring vectorized path multi-queues payload check with server mode and cbdma enable
--------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user packed ring
vectorized path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 2 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.1;txq5@0000:00:01.1;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.1;rxq5@0000:00:01.1;rxq6@0000:00:01.1;rxq7@0000:00:01.1]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring vectorized path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte and the payload in receive packets are same in each pcap file.

Test Case 6: Loopback packed ring vectorized path and ring size is not power of 2 multi-queues payload check with server mode and cbdma enable
----------------------------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user packed ring vectorized path and
ring size is not power of 2, multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 2 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.1;txq5@0000:00:01.1;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.1;rxq5@0000:00:01.1;rxq6@0000:00:01.1;rxq7@0000:00:01.1]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with packed ring vectorized path and ring size is not power of 2::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1025 --rxd=1025
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte and the payload in receive packets are same in each pcap file.

Test Case 7: Loopback split ring inorder mergeable path multi-queues payload check with server mode and cbdma enable
--------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user split ring
inorder mergeable path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 1 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.0;txq5@0000:00:01.0;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.0;rxq5@0000:00:01.0;rxq6@0000:00:01.0;rxq7@0000:00:01.0]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring inorder mergeable path::

	dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	-vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1 \
	- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte and the payload in receive packets are same in each pcap file.

Test Case 8: Loopback split ring mergeable path multi-queues payload check with server mode and cbdma enable
------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user split ring
mergeable path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 2 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.1;txq5@0000:00:01.1;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.1;rxq5@0000:00:01.1;rxq6@0000:00:01.1;rxq7@0000:00:01.1]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring mergeable path::

	dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	-vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1 \
	- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte and the payload in receive packets are same in each pcap file.

Test Case 9: Loopback split ring inorder non-mergeable path multi-queues payload check with server mode and cbdma enable
------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user split ring
inorder non-mergeable path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 2 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.1;txq5@0000:00:01.1;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.1;rxq5@0000:00:01.1;rxq6@0000:00:01.1;rxq7@0000:00:01.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring inorder non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte and the payload in receive packets are same in each pcap file.

Test Case 10: Loopback split ring non-mergeable path multi-queues payload check with server mode and cbdma enable
-----------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user split ring
non-mergeable path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 2 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.1;txq5@0000:00:01.1;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.1;rxq5@0000:00:01.1;rxq6@0000:00:01.1;rxq7@0000:00:01.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring non-mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,server=1 \
	-- -i --enable-hw-vlan-strip --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte and the payload in receive packets are same in each pcap file.

Test Case 11: Loopback split ring vectorized path multi-queues payload check with server mode and cbdma enable
--------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user split ring
vectorized path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 2 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.1;txq5@0000:00:01.1;rxq2@0000:00:01.0;rxq3@0000:00:01.0;rxq4@0000:00:01.1;rxq5@0000:00:01.1;rxq6@0000:00:01.1;rxq7@0000:00:01.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring vectorized path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd mac
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 960 Byte and the payload in receive packets are same in each pcap file.

Test Case 12: Loopback split ring large chain packets stress test with server mode and cbdma enable
---------------------------------------------------------------------------------------------------
This is a stress test case about forwading large chain packets in loopback vhost-user/virtio-user split ring with server mode
when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 1 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 -a 0000:00:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=1,client=1,dmas=[txq0@0000:00:01.0;rxq0@0000:00:01.0]' --iova=va -- -i --nb-cores=1 --mbuf-size=65535

3. Launch virtio-user and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4  --file-prefix=testpmd0 --no-pci  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd> start

4. Send large packets from vhost, check packets can loop normally::

	testpmd> set txpkts 65535,65535
	testpmd> start tx_first 32
	testpmd> show port stats all

Test Case 13: Loopback packed ring large chain packets stress test with server mode and cbdma enable
----------------------------------------------------------------------------------------------------
This is a stress test case about forwading large chain packets in loopback vhost-user/virtio-user
packed ring with server mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 1 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 -a 0000:00:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0@0000:00:01.0;rxq0@0000:00:01.0],client=1' --iova=va -- -i --nb-cores=1 --mbuf-size=65535

3. Launch virtio-user and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4  --file-prefix=testpmd0 --no-pci  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048,server=1 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd> start

4. Send large packets from vhost, check packets can loop normally::

	testpmd> set txpkts 65535,65535
	testpmd> start tx_first 32
	testpmd> show port stats all

Test Case 14: PV split and packed ring test txonly mode with cbdma enable
-------------------------------------------------------------------------
This case tests that vhost pmd can work normally with txonly/rxonly mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 2 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost-user by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.1;txq5@0000:00:01.1;txq6@0000:00:01.1;txq7@0000:00:01.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024

3. Launch virtio-user with split ring inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd> set fwd rxonly
	testpmd> start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large packets from vhost::

	testpmd> set fwd txonly
	testpmd> async_vhost tx poll completed on
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1

6. Check the Rx-pps>0 and each queue can receive packets with 6192 Byte from virtio-user.

7. Quit pdump, check packets with 6192 Byte in each pcap file.

8. Relaunch virtio-user with packed ring vectorized path with ring size is not power of 2::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,packed_vq=1,server=1,queue_size=1025 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1025 --rxd=1025
	testpmd> set fwd rxonly
	testpmd> start

9. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

10. Send packets from vhost::

	testpmd> set fwd txonly
	testpmd> async_vhost tx poll completed on
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1

11. Check each queue can receive packets with 960 Byte from virtio-user.

12. Quit pdump, check packets with 960 Byte in each pcap file.
