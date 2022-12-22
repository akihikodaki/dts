.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

======================================================
VM2VM vhost-user/virtio-user with DSA driver test plan
======================================================

Description
===========

Vhost asynchronous data path leverages DMA devices to offload memory copies from the CPU and it is implemented in an asynchronous way.
Asynchronous data path is enabled per tx/rx queue, and users need to specify the DMA device used by the tx/rx queue. Each tx/rx queue
only supports to use one DMA device, but one DMA device can be shared among multiple tx/rx queues of different vhostpmd ports.

Two PMD parameters are added:
- dmas:	specify the used DMA device for a tx/rx queue(Default: no queues enable asynchronous data path)
- dma-ring-size: DMA ring size.(Default: 4096).

Here is an example:
--vdev 'eth_vhost0,iface=./s0,dmas=[txq0@0000:00.01.0;rxq0@0000:00.01.1],dma-ring-size=4096'

This document provides the test plan for testing the following features when Vhost-user using asynchronous data path with
DSA driver (kernel IDXD driver and DPDK vfio-pci driver) in VM2VM virtio-user topology.
1. Split virtqueue vm2vm in-order mergeable, in-order non-mergeable, mergeable, non-mergeable, vector_rx path test and payload check.
2. Packed virtqueue vm2vm in-order mergeable, in-order non-mergeable, mergeable, non-mergeable, vectorized path (ringsize not powerof 2) test and payload check.
3. Test indirect descriptor feature. For example, the split ring mergeable inorder path use non-indirect descriptor, the 2000,2000,2000,2000 chain packets will need 4 consequent ring, still need one ring put header.
the split ring mergeable path use indirect descriptor, the 2000,2000,2000,2000 chain packets will only occupy one ring.

IOMMU impact:
If iommu off, idxd can work with iova=va
If iommu on, kernel dsa driver only can work with iova=va by program IOMMU, can't use iova=va(fwd not work due to pkts payload wrong).

Note:
1.When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
exceed IOMMU's max capability, better to use 1G guest hugepage.
2.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

Prerequisites
=============

Topology
--------
	Test flow: Virtio-user -> Vhost-user -> Testpmd -> Vhost-user -> Virtio-user

General set up
--------------
1. Compile DPDK::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
	# ninja -C <dpdk build dir> -j 110
	For example,
	CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
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

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <dsa_pci>

	For example, bind 2 DMA devices to vfio-pci driver:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:e7:01.0 0000:ec:01.0

.. note::

	One DPDK DSA device can create 8 WQ at most. Below is an example, where DPDK DSA device will create one and
	eight WQ for DSA deivce 0000:e7:01.0 and 0000:ec:01.0. The value of “max_queues” is 1~8:
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:e7:01.0,max_queues=1 -- -i
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:ec:01.0,max_queues=8 -- -i

2. Bind DSA devices to kernel idxd driver, and configure Work Queue (WQ)::

	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd <dsa_pci>
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q <wq_num> <dsa_idx>

.. note::

	Better to reset WQ when need operate DSA devices that bound to idxd drvier:
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py --reset <dsa_idx>
	You can check it by 'ls /dev/dsa'
	dsa_idx: number of devices, where 0<=dsa_idx<=7, corresponding to 0000:6a:01.0 - 0000:f6:01.0
	wq_num: Number of workqueues per DSA endpoint, where 1<=wq_num<=8

	For example, bind 2 DMA devices to idxd driver and configure WQ:

	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 1
	Check WQ by 'ls /dev/dsa' and can find "wq0.0 wq1.0 wq1.1 wq1.2 wq1.3"

Test Case 1: VM2VM split ring non-mergeable path and multi-queues payload check with dsa dpdk driver
----------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user split ring non-mergeable path
and multi-queues when vhost uses the asynchronous operations with dsa dpdk driver.

1. bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=2 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q0]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q1;rxq1@0000:e7:01.0-q1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost testpmd, quit pdump and check virtio-user1 RX-packets is 566 and RX-bytes is 486016 and 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

7. Clear virtio-user1 port stats::

	testpmd>stop
	testpmd>clear port stats all
	testpmd>start

8. Relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=4 -a 0000:ec:01.0,max_queues=4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q1;rxq0@0000:e7:01.0-q2;rxq1@0000:e7:01.0-q3]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:ec:01.0-q0;txq1@0000:ec:01.0-q1;rxq0@0000:ec:01.0-q2;rxq1@0000:ec:01.0-q3]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

9. Rerun step 4.

10. Virtio-user0 and send packets again::

	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

11. Rerun step 6.

Test Case 2: VM2VM split ring inorder non-mergeable path and multi-queues payload check with dsa dpdk driver
------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user split ring inorder
non-mergeable path and multi-queues when vhost uses the asynchronous operations with dsa dpdk driver.

1. bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q2;rxq1@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost testpmd, quit pdump and check virtio-user1 RX-packets is 566 and RX-bytes is 486016 and 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

7. Clear virtio-user1 port stats::

	testpmd>stop
	testpmd>clear port stats all
	testpmd>start

8. Relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=2 -a 0000:ec:01.0,max_queues=2 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q1;rxq1@0000:e7:01.0-q1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:ec:01.0-q0;txq1@0000:ec:01.0-q0;rxq0@0000:ec:01.0-q1;rxq1@0000:ec:01.0-q1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

9. Rerun step 4.

10. Virtio-user0 and send packets again::

	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

11. Rerun step 6.

Test Case 3: VM2VM split ring inorder mergeable path and multi-queues test non-indirect descriptor and payload check with dsa dpdk driver
-----------------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and non-indirect descriptor after packets forwarding in vhost-user/virtio-user
split ring inorder mergeable path and multi-queues when vhost uses the asynchronous operations with dsa dpdk driver.

1. bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=2 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=256 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=256 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
	testpmd>set burst 1
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 2000,2000,2000,2000
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost, then quit pdump and three testpmd, about split virtqueue inorder mergeable path, it use the non-indirect descriptors, the 8k length pkt will occupies 5 ring:2000,2000,2000,2000 will need 4 consequent ring,
still need one ring put header. So check 504 packets and 48128 bytes received by virtio-user1 and 502 packets with 64 length and 2 packets with 8K length in pdump-virtio-rx.pcap.

7. Relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=4 -a 0000:ec:01.0,max_queues=4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q1;rxq0@0000:e7:01.0-q2;rxq1@0000:e7:01.0-q3]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:ec:01.0-q0;txq1@0000:ec:01.0-q1;rxq0@0000:ec:01.0-q2;rxq1@0000:ec:01.0-q3]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx

8. Rerun step 3-6.

Test Case 4: VM2VM split ring mergeable path and multi-queues test indirect descriptor and payload check with dsa dpdk driver
-----------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and indirect descriptor after packets forwarding in vhost-user/virtio-user
split ring mergeable path and multi-queues when vhost uses the asynchronous operations with dsa dpdk driver.

1. bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q0]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q0]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
	testpmd>set burst 1
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 2000,2000,2000,2000
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost, then quit pdump and three testpmd, about split virtqueue inorder mergeable path, it use the indirect descriptors, the 8k length pkt will just occupies one ring.
So check 512 packets and 112128 bytes received by virtio-user1 and 502 packets with 64 length and 10 packets with 8K length in pdump-virtio-rx.pcap.

7. Relaunch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=4 -a 0000:ec:01.0,max_queues=2 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q1;rxq0@0000:e7:01.0-q2;rxq1@0000:e7:01.0-q3]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:ec:01.0-q0;txq1@0000:ec:01.0-q1;rxq0@0000:ec:01.0-q2;rxq1@0000:ec:01.0-q3]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx

8. Rerun step 3-6.

Test Case 5: VM2VM split ring vectorized path and multi-queues payload check with vhost async operation and dsa dpdk driver
---------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user split ring vectorized path
and multi-queues when vhost uses the asynchronous operations with dsa dpdk driver.

1. bind 2 dsa ports to vfio-pci::

    ls /dev/dsa #check wq configure, reset if exist
    <dpdk dir># ./usertools/dpdk-devbind.py -u e7:01.0 ec:01.0
    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch vhost by below command::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0 -a 0000:ec:01.0 \
    --vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q0]' \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q1;txq1@0000:e7:01.0-q1;rxq1@0000:e7:01.0-q1]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 1
    testpmd>set txpkts 64,128,256,512
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 64
    testpmd>start tx_first 1
    testpmd>stop

6. Start vhost testpmd, quit pdump and check virtio-user1 RX-packets is 566 and RX-bytes is 486016 and 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

7. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

8. Relaunch vhost by below command::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0 -a 0000:ec:01.0 \
    --vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q3;txq1@0000:e7:01.0-q3;rxq0@0000:ec:01.0-q1;rxq1@0000:ec:01.0-q1]' \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:ec:01.0-q1;txq1@0000:ec:01.0-q1;rxq0@0000:e7:01.0-q3;rxq1@0000:e7:01.0-q3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

9. Rerun step 4.

10. Virtio-user0 and send packets again::

	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

11. Rerun step 6.

Test Case 6: VM2VM packed ring non-mergeable path and multi-queues payload check with dsa dpdk driver
-----------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring
non-mergeable path and multi-queues when vhost uses the asynchronous operations with dsa dpdk driver.

1. bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0 f1:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0 -a 0000:ec:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q1;rxq1@0000:e7:01.0-q1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:ec:01.0-q1;rxq1@0000:ec:01.0-q1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost testpmd,  quit pdump and check virtio-user1 RX-packets is 566 and RX-bytes is 486016 and 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

7. Clear virtio-user1 port stats::

	testpmd>stop
	testpmd>clear port stats all
	testpmd>start

8. Relaunch vhost with iova=va by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q1;rxq1@0000:e7:01.0-q1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q2;txq1@0000:e7:01.0-q2;rxq0@0000:e7:01.0-q3;rxq1@0000:e7:01.0-q3]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

9. Rerun step 4.

10. Virtio-user0 and send packets again::

	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

11. Rerun step 6.

Test Case 7: VM2VM packed ring inorder non-mergeable path and multi-queues payload check with dsa dpdk driver
-------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring inorder
non-mergeable path and multi-queues when vhost uses the asynchronous operations with dsa dpdk driver.

1. bind 4 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 f1:01.0 f6:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=2 -a 0000:ec:01.0,max_queues=2 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:ec:01.0-q0;rxq1@0000:ec:01.0-q1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost testpmd, quit pdump and check virtio-user1 RX-packets is 566 and RX-bytes is 486016 and 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

7. Clear virtio-user1 port stats::

	testpmd>stop
	testpmd>clear port stats all
	testpmd>start

8. Relaunch vhost with iova=va by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0 -a 0000:ec:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q5;txq1@0000:e7:01.0-q6;rxq0@0000:e7:01.0-q5;rxq1@0000:e7:01.0-q6]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:ec:01.0-q5;txq1@0000:ec:01.0-q6;rxq0@0000:ec:01.0-q5;rxq1@0000:ec:01.0-q6]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

9. Rerun step 4.

10. Virtio-user0 and send packets again::

	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

11. Rerun step 6.

Test Case 8: VM2VM packed ring mergeable path and multi-queues payload check with dsa dpdk driver
-------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring
mergeable path and multi-queues when vhost uses the asynchronous operations with dsa dpdk driver.

1. bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q0]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q0]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
	--no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,256,2000,64,256,2000
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>set txpkts 64
	testpmd>start tx_first 7
	testpmd>stop

6. Start vhost testpmd,  quit pdump and check virtio-user1 check 502 packets and 279232 bytes and 54 packets with 4640 length and 448 packets with 64 length in pdump-virtio-rx.pcap.

7. Clear virtio-user1 port stats::

	testpmd>stop
	testpmd>clear port stats all
	testpmd>start

8. Relaunch vhost with iova=va by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q1;rxq0@0000:e7:01.0-q2;rxq1@0000:e7:01.0-q3]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q4;txq1@0000:e7:01.0-q5;rxq0@0000:e7:01.0-q6;rxq1@0000:e7:01.0-q7]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

9. Rerun step 4.

10. Virtio-user0 and send packets again::

	testpmd>set burst 1
	testpmd>set txpkts 64,256,2000,64,256,2000
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>set txpkts 64
	testpmd>start tx_first 7
	testpmd>stop

11. Rerun step 6.

Test Case 9: VM2VM packed ring inorder mergeable path and multi-queues payload check with dsa dpdk driver
---------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring inorder
mergeable path and multi-queues when vhost uses the asynchronous operations with dsa dpdk driver.

1. bind 4 dsa device to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0 f1:01.0 f6:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0 -a 0000:ec:01.0 -a 0000:f1:01.0 -a 0000:f6:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q0]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q1;txq1@0000:e7:01.0-q1;rxq1@0000:e7:01.0-q1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,256,2000,64,256,2000
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>set txpkts 64
	testpmd>start tx_first 7
	testpmd>stop

6. Start vhost testpmd, quit pdump and check virtio-user1 RX-packets is 502 packets and 279232 bytes and 54 packets with 4640 length and 448 packets with 64 length in pdump-virtio-rx.pcap.

7. Clear virtio-user1 port stats::

	testpmd>stop
	testpmd>clear port stats all
	testpmd>start

8. Relaunch vhost with iova=va by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0 -a 0000:ec:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q1;rxq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:ec:01.0-q0;txq1@0000:ec:01.0-q1;rxq0@0000:ec:01.0-q0;rxq1@0000:ec:01.0-q1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

9. Rerun step 4.

10. Virtio-user0 and send packets again::

	testpmd>set burst 1
	testpmd>set txpkts 64,256,2000,64,256,2000
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>set txpkts 64
	testpmd>start tx_first 7
	testpmd>stop

11. Rerun step 6.

Test Case 10: VM2VM packed ring vectorized-tx path and multi-queues test indirect descriptor and payload check with dsa dpdk driver
-----------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and indirect descriptor after packets forwarding in vhost-user/virtio-user
packed ring vectorized-tx path and multi-queues when vhost uses the asynchronous operations with dsa dpdk driver.

1. bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0 

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=2 \
	--vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q0;rxq1@0000:e7:01.0-q0]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q1;txq1@0000:e7:01.0-q1;rxq0@0000:e7:01.0-q1;rxq1@0000:e7:01.0-q1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send 8k length packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
	testpmd>set burst 1
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 2000,2000,2000,2000
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost, then quit pdump and three testpmd, about packed virtqueue vectorized-tx path, it use the indirect descriptors, the 8k length pkt will just occupies one ring.
So check 512 packets and 112128 bytes received by virtio-user1 and 502 packets with 64 length and 10 packets with 8K length in pdump-virtio-rx.pcap.

7.Relaunch vhost with iova=va by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=4 -a 0000:ec:01.0,max_queues=2 \
	--vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q1;rxq0@0000:e7:01.0-q2;rxq1@0000:e7:01.0-q3]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:ec:01.0-q0;txq1@0000:ec:01.0-q1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx

8. Rerun step 3-6.

Test Case 11: VM2VM packed ring vectorized path and payload check test with dsa dpdk driver
-------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and indirect descriptor after packets forwarding in vhost-user/virtio-user
packed ring vectorized path and multi-queues when vhost uses the asynchronous operations with dsa dpdk driver.

1. Bind 2 dsa device to vfio-pci like common step 2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=2 \
	--vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q1;rxq1@0000:e7:01.0-q1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q1;rxq1@0000:e7:01.0-q1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send 8k length packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

6. Start vhost,then quit pdump, check 448 packets and 28672 bytes received by virtio-user1 and 448 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 12: VM2VM packed ring vectorized path payload check test with ring size is not power of 2 with dsa dpdk driver
------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and indirect descriptor after packets forwarding in vhost-user/virtio-user
packed ring vectorized path and multi-queues with ring size is not power of 2 when vhost uses the asynchronous operations with dsa dpdk driver.

1. Bind 2 dsa device to vfio-pci like common step 2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:e7:01.0,max_queues=2 \
	--vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q1;rxq1@0000:e7:01.0-q1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:e7:01.0-q0;txq1@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q1;rxq1@0000:e7:01.0-q1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send 8k length packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097
	testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

6. Start vhost,then quit pdump, check 448 packets and 28672 bytes received by virtio-user1 and 448 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 13: VM2VM split ring non-mergeable path and multi-queues payload check with dsa kernel driver
-------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user split ring
non-mergeable path and multi-queues when vhost uses the asynchronous operations with dsa kernel driver.

1. bind 1 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py --reset xx
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@wq0.0;rxq1@wq0.0]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq0.1;rxq1@wq0.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	 <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost testpmd, quit pdump and check virtio-user1 RX-packets is 566 and RX-bytes is 486016 and 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 14: VM2VM split ring inorder non-mergeable path and multi-queues payload check with dsa kernel driver
---------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user split ring inorder
non-mergeable path and multi-queues when vhost uses the asynchronous operations with dsa kernel driver.

1. bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@wq0.0;rxq1@wq0.1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq0.2;rxq1@wq0.3]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost testpmd, quit pdump and check virtio-user1 RX-packets is 566 and RX-bytes is 486016 and 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 15: VM2VM split ring inorder mergeable path and multi-queues test non-indirect descriptor and payload check with dsa kernel driver
--------------------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and non-indirect descriptor after packets forwarding in vhost-user/virtio-user
split ring inorder mergeable path and multi-queues when vhost uses the asynchronous operations with dsa kernel driver.

1. bind 1 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@wq0.0;rxq1@wq0.1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq0.0;rxq1@wq0.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=256 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
	testpmd>set burst 1
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 2000,2000,2000,2000
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost, then quit pdump and three testpmd, about split virtqueue inorder mergeable path, it use the direct descriptors, the 8k length pkt will occupies 5 ring:2000,2000,2000,2000 will need 4 consequent ring,
still need one ring put header. So check 504 packets and 48128 bytes received by virtio-user1 and 502 packets with 64 length and 2 packets with 8K length in pdump-virtio-rx.pcap.

Test Case 16: VM2VM split ring mergeable path and multi-queues test indirect descriptor and payload check with dsa kernel driver
--------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and indirect descriptor after packets forwarding in vhost-user/virtio-user
split ring mergeable path and multi-queues when vhost uses the asynchronous operations with dsa kernel driver.

1. bind 1 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /dev/dsa #check wq configure success
2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;rxq0@wq0.0;rxq1@wq0.0]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq0.1;txq1@wq0.1;rxq0@wq0.1;rxq1@wq0.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
	testpmd>set burst 1
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 2000,2000,2000,2000
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost, then quit pdump and three testpmd, about split virtqueue inorder mergeable path, it use the indirect descriptors, the 8k length pkt will just occupies one ring.
So check 512 packets and 112128 bytes received by virtio-user1 and 502 packets with 64 length and 10 packets with 8K length in pdump-virtio-rx.pcap.

Test Case 17: VM2VM split ring vectorized path and multi-queues payload check with vhost async operation and dsa kernel driver
------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user split ring
vectorized path and multi-queues when vhost uses the asynchronous operations with dsa kernel driver.

1. bind 1 dsa ports to idxd::

    ls /dev/dsa #check wq configure, reset if exist
    <dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
    <dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
    <dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
    ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

    <dpdk dir>#./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;rxq0@wq0.0;rxq1@wq0.0]' \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;rxq0@wq0.0;rxq1@wq0.0]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

    <dpdk dir>#./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

    <dpdk dir>#./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

    <dpdk dir>#./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 1
    testpmd>set txpkts 64,128,256,512
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 64
    testpmd>start tx_first 1
    testpmd>stop

6. Start vhost testpmd, quit pdump and check virtio-user1 RX-packets is 566 and RX-bytes is 486016 and 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 18: VM2VM packed ring non-mergeable path and multi-queues payload check with dsa kernel driver
--------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring
non-mergeable path and multi-queues when vhost uses the asynchronous operations with dsa kernel driver.

1. bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@wq0.0;rxq1@wq0.0]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq0.1;rxq1@wq0.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
	--no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost testpmd,  quit pdump and check virtio-user1 RX-packets is 566 and RX-bytes is 486016 and 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 19: VM2VM packed ring inorder non-mergeable path and multi-queues payload check with dsa kernel driver
----------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring inorder
non-mergeable path and multi-queues when vhost uses the asynchronous operations with dsa kernel driver.

1. bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 2
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@wq0.0;rxq1@wq0.1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq1.0;rxq1@wq1.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,128,256,512
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 64
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost testpmd, quit pdump and check virtio-user1 RX-packets is 566 and RX-bytes is 486016 and 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 20: VM2VM packed ring mergeable path and multi-queues payload check with dsa kernel driver
----------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring
mergeable path and multi-queues when vhost uses the asynchronous operations with dsa kernel driver.

1. bind 1 dsa device to idxd::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;rxq0@wq0.1;rxq1@wq0.1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq0.1;txq1@wq0.1;rxq0@wq0.0;rxq1@wq0.0]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,256,2000,64,256,2000
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>set txpkts 64
	testpmd>start tx_first 7
	testpmd>stop

6. Start vhost testpmd,  quit pdump and check virtio-user1 check 502 packets and 279232 bytes and 54 packets with 4640 length and 448 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 21: VM2VM packed ring inorder mergeable path and multi-queues payload check with dsa kernel driver
------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring inorder
mergeable path and multi-queues when vhost uses the asynchronous operations with dsa kernel driver.

1. bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 2
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@wq0.0;rxq0@wq0.0;rxq1@wq0.0]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq1.0;txq1@wq1.0;rxq1@wq1.0]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,256,2000,64,256,2000
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>set txpkts 64
	testpmd>start tx_first 7
	testpmd>stop

6. Start vhost testpmd, quit pdump and check virtio-user1 RX-packets is 502 packets and 279232 bytes and 54 packets with 4640 length and 448 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 22: VM2VM packed ring vectorized-tx path and multi-queues test indirect descriptor and payload check with dsa kernel driver
-------------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and indirect descriptor after packets forwarding in vhost-user/virtio-user
packed ring vectorized-tx path and multi-queues when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 2
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;rxq0@wq0.1;rxq1@wq0.1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq1.0;txq1@wq1.0;rxq0@wq1.1;rxq1@wq1.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send 8k length packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256

	testpmd>set burst 1
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 2000,2000,2000,2000
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost, then quit pdump and three testpmd, about packed virtqueue vectorized-tx path, it use the indirect descriptors, the 8k length pkt will just occupies one ring.
So check 512 packets and 112128 bytes received by virtio-user1 and 502 packets with 64 length and 10 packets with 8K length in pdump-virtio-rx.pcap.

Test Case 23: VM2VM packed ring vectorized path and multi-queues test indirect descriptor and payload check with dsa kernel driver
----------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and indirect descriptor after packets forwarding in vhost-user/virtio-user
packed ring vectorized-tx path and multi-queues when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 2
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;rxq0@wq0.1;rxq1@wq0.1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq1.0;txq1@wq1.0;rxq0@wq1.1;rxq1@wq1.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send 8k length packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096

	testpmd>set burst 1
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 2000,2000,2000,2000
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost,then quit pdump, check 502 packets and 32128 bytes received by virtio-user1 and 502 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 24: VM2VM packed ring vectorized path payload check test with ring size is not power of 2 with dsa kernel driver
--------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and indirect descriptor after packets forwarding in vhost-user/virtio-user
packed ring vectorized path and multi-queues with ring size is not power of 2 when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 2
	ls /dev/dsa #check wq configure success

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 --no-pci \
	--vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@wq0.0;txq1@wq0.0;rxq0@wq0.1;rxq1@wq0.1]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq1.0;txq1@wq1.0;rxq0@wq1.1;rxq1@wq1.1]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=txd=4096 --rxd=txd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send 8k length packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097

	testpmd>set burst 1
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>start tx_first 7
	testpmd>stop
	testpmd>set txpkts 2000,2000,2000,2000
	testpmd>start tx_first 1
	testpmd>stop

6. Start vhost,then quit pdump, check 502 packets and 32128 bytes received by virtio-user1 and 502 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 25: VM2VM split ring mergeable path and multi-queues test indirect descriptor with dsa dpdk and kernel driver
-----------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and indirect descriptor after packets forwarding in vhost-user/virtio-user
split ring mergeable path and multi-queues when vhost uses the asynchronous operations with dsa dpdk and kernel driver.

1. bind 1 dsa ports to idxd and 1 dsa ports to vfio-pci::

    ls /dev/dsa #check wq configure, reset if exist
    <dpdk dir># ./usertools/dpdk-devbind.py -u e7:01.0 f1:01.0
    <dpdk dir># ./usertools/dpdk-devbind.py -b idxd e7:01.0
    <dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
    ls /dev/dsa #check wq configure success
    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:f1:01.0,max_queues=1 -a 0000:f6:01.0,max_queues=1 \
    --vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@wq0.0;rxq0@wq0.0;rxq1@wq0.0]' \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;rxq1@0000:f1:01.0-q0]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx

3. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1
    testpmd>stop

6. Start vhost, then quit pdump and three testpmd, about split virtqueue inorder mergeable path, it use the indirect descriptors, the 8k length pkt will just occupies one ring.
So check 512 packets and 112128 bytes received by virtio-user1 and 502 packets with 64 length and 10 packets with 8K length in pdump-virtio-rx.pcap.

Test Case 26: VM2VM packed ring inorder mergeable path and multi-queues payload check with dsa dpdk and kernel driver
---------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring inorder
mergeable path and multi-queues when vhost uses the asynchronous operations with dsa dpdk and kernel driver.

1. bind 1 dsa device to vfio-pci and 1 dsa port to idxd like common step 1-2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u e7:01.0 f1:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd e7:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /dev/dsa #check wq configure success
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:f1:01.0,max_queues=1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:f1:01.0-q0;txq1@wq0.0;rxq0@0000:f1:01.0-q0;rxq1@wq0.0]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq0.0;txq1@0000:f1:01.0-q0;rxq0@wq0.0;rxq1@0000:f1:01.0-q0]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
	--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set fwd rxonly
	testpmd>start

4. Attach pdump secondary process to primary process of virtio-user1 by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/tmp/pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send packets::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096 \
	-- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
	testpmd>set burst 1
	testpmd>set txpkts 64,256,2000,64,256,2000
	testpmd>start tx_first 27
	testpmd>stop
	testpmd>set burst 32
	testpmd>set txpkts 64
	testpmd>start tx_first 7
	testpmd>stop

6. Start vhost testpmd, quit pdump and check virtio-user1 RX-packets is 502 packets and 279232 bytes and 54 packets with 4640 length and 448 packets with 64 length in pdump-virtio-rx.pcap.

Test Case 27: VM2VM packed ring vectorized-tx path test batch processing with dsa dpdk and kernel driver
--------------------------------------------------------------------------------------------------------
This case uses testpmd to test that one packet can forwarding in vhost-user/virtio-user packed ring vectorized-tx path
when vhost uses the asynchronous operations with dsa dpdk and kernel driver.

1. bind 1 dsa device to vfio-pci and 1 dsa port to idxd like common step 1-2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u e7:01.0 f1:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd e7:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /dev/dsa #check wq configure success
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -a 0000:f1:01.0,max_queues=1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0@0000:f1:01.0-q0;txq1@wq0.0;rxq0@0000:f1:01.0-q0;rxq1@wq0.0]' \
	--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@wq0.0;txq1@0000:f1:01.0-q0;rxq0@wq0.0;rxq1@0000:f1:01.0-q0]' \
	--iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx

3. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

5. Launch virtio-user0 and send 1 packet::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 1
    testpmd>stop

6. Start vhost, then quit pdump and three testpmd, check 2 packet and 128 bytes received by virtio-user1 and 2 packet with 64 length in pdump-virtio-rx.pcap.