.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

===========================================================
Loopback vhost/virtio-user server mode with CBDMA test plan
===========================================================

Description
===========

Vhost asynchronous data path leverages DMA devices to offload memory copies from the CPU and it is implemented in an asynchronous way.
In addition, vhost supports M:N mapping between vrings and DMA virtual channels. Specifically, one vring can use multiple different DMA
channels and one DMA channel can be shared by multiple vrings at the same time. From DPDK22.07, Vhost enqueue and dequeue operation with
CBDMA channels is supported in both split and packed ring.

This document provides the test plan for testing the following features when Vhost-user using asynchronous data path with
CBDMA channels in loopback vhost-user/virtio-user topology.
1. Virtio-user server mode is a feature to enable virtio-user as the server, vhost as the client, thus after vhost-user is killed then relaunched,
virtio-user can reconnect back to vhost-user again; at another hand, virtio-user also can reconnect back to vhost-user after virtio-user is killed.
This feature test need cover different rx/tx paths with virtio 1.0 and virtio 1.1, includes split ring mergeable, non-mergeable, inorder mergeable,
inorder non-mergeable, vector_rx path and packed ring mergeable, non-mergeable, inorder non-mergeable, inorder mergeable, vectorized path.
2. Check payload valid after packets forwarding many times.
3. Stress test with large chain packets.

Note:
1. When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
exceed IOMMU's max capability, better to use 1G guest hugepage.
2. DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

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

    For example, bind 2 CBDMA channels:
    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:04.0,0000:00:04.1

Test Case 1: Loopback packed ring all path multi-queues payload check with server mode and cbdma enable
-------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user packed ring
all path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Bind 8 CBDMA channel to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore12@0000:00:04.2,lcore12@0000:00:04.3,lcore13@0000:00:04.4,lcore13@0000:00:04.5,lcore14@0000:00:04.6,lcore14@0000:00:04.7]

3. Launch virtio-user with packed ring mergeable inorder path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
    --pdump 'device_id=net_virtio_user1,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
    --pdump 'device_id=net_virtio_user1,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large pkts from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd csum
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte and the payload in receive packets are same in each pcap file.

7. Quit and relaunch vhost and rerun step 4-6.

8. Quit and relaunch virtio with packed ring mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Rerun steps 4-7.

10. Quit and relaunch virtio with packed ring non-mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

11. Rerun step 4.

12. Send pkts from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd csum
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> stop

13. Quit pdump, check all the packets length are 960 Byte and the payload in receive packets are same in each pcap file.

14. Quit and relaunch vhost and rerun step 11-13.

15. Quit and relaunch virtio with packed ring inorder non-mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

16. Rerun step 11-14.

17. Quit and relaunch virtio with packed ring vectorized path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

18. Rerun step 11-14.

19. Quit and relaunch virtio with packed ring vectorized path and ring size is not power of 2 as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025,server=1 \
	-- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1025 --rxd=1025
	testpmd>set fwd csum
	testpmd>start

20. Rerun step 11-14.

21. Quit and relaunch vhost w/ iova=pa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-14 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=pa -- -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore12@0000:00:04.2,lcore12@0000:00:04.3,lcore13@0000:00:04.4,lcore13@0000:00:04.5,lcore14@0000:00:04.6,lcore14@0000:00:04.7]

22. Rerun steps 3-6.

Test Case 2: Loopback split ring all path multi-queues payload check with server mode and cbdma enable
------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user split ring
all path multi-queues with server mode when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Bind 3 CBDMA channel to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.1,lcore14@0000:00:04.2,lcore15@0000:00:04.1,lcore15@0000:00:04.2]

3. Launch virtio-user with split ring mergeable inorder path::

	dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	-vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1 \
	- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

    <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
    --pdump 'device_id=net_virtio_user1,queue=0,rx-dev=./pdump-virtio-rx-q0.pcap,mbuf-size=8000' \
    --pdump 'device_id=net_virtio_user1,queue=1,rx-dev=./pdump-virtio-rx-q1.pcap,mbuf-size=8000'

5. Send large pkts from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd csum
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte and the payload in receive packets are same in each pcap file.

7. Quit and relaunch vhost and rerun step 4-6.

8. Quit and relaunch virtio with split ring mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Rerun steps 4-7.

10. Quit and relaunch virtio with split ring non-mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,server=1 \
	-- -i --enable-hw-vlan-strip --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

11. Rerun step 4.

12. Send pkts from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd csum
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> stop

13. Quit pdump, check all the packets length are 960 Byte and the payload in receive packets are same in each pcap file.

14. Quit and relaunch vhost and rerun step 11-13.

15. Quit and relaunch virtio with split ring inorder non-mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

16. Rerun step 11-14.

17. Quit and relaunch virtio with split ring vectorized path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

18. Rerun step 11-14.

19. Quit and relaunch vhost w/ iova=pa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]' \
	--iova=pa -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.1,lcore14@0000:00:04.2,lcore15@0000:00:04.1,lcore15@0000:00:04.2]

20. Rerun steps 3-6.

Test Case 3: Loopback split ring large chain packets stress test with server mode and cbdma enable
--------------------------------------------------------------------------------------------------
This is a stress test case about forwading large chain packets in loopback vhost-user/virtio-user split ring with server mode 
when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Bind 1 CBDMA channel to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 -a 0000:00:04.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=1,client=1,dmas=[txq0;rxq0]' --iova=va -- -i --nb-cores=1 --mbuf-size=65535 --lcore-dma=[lcore3@0000:00:04.0]

3. Launch virtio and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4  --file-prefix=testpmd0 --no-pci  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd>start

4. Send large packets from vhost, check virtio can receive packets::

	testpmd> set txpkts 65535,65535,65535,65535,65535
	testpmd> start tx_first 32
	testpmd> show port stats all

5. Stop and quit vhost testpmd and relaunch vhost with iova=pa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 -a 0000:00:04.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=1,client=1,dmas=[txq0;rxq0]' --iova=pa -- -i --nb-cores=1 --mbuf-size=65535 --lcore-dma=[lcore3@0000:00:04.0]

6. Rerun steps 4.

Test Case 4: Loopback packed ring large chain packets stress test with server mode and cbdma enable
---------------------------------------------------------------------------------------------------
This is a stress test case about forwading large chain packets in loopback vhost-user/virtio-user packed ring with server mode 
when vhost uses the asynchronous operations with dsa dpdk driver. Both iova as VA and PA mode test.

1. Bind 1 CBDMA channel to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 -a 0000:00:04.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0;rxq0],client=1' --iova=va -- -i --nb-cores=1 --mbuf-size=65535 --lcore-dma=[lcore3@0000:00:04.0]

3. Launch virtio and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4  --file-prefix=testpmd0 --no-pci  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048,server=1 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd>start

4. Send large packets from vhost, check virtio can receive packets::

	testpmd> set txpkts 65535,65535,65535,65535,65535
	testpmd> start tx_first 32
	testpmd> show port stats all

5. Stop and quit vhost testpmd and relaunch vhost with iova=pa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 -a 0000:00:04.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0],client=1' --iova=pa -- -i --nb-cores=1 --mbuf-size=65535 --lcore-dma=[lcore3@0000:00:04.0]

6. Rerun steps 4.
