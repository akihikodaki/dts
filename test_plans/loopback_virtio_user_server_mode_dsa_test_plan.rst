.. Copyright (c) <2022>, Intel Corporation
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

   - Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.

   - Neither the name of Intel Corporation nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.

=======================================================================
Loopback vhost-user/virtio-user server mode with DSA driver test plan
=======================================================================

Description
===========

Vhost asynchronous data path leverages DMA devices to offload memory copies from the CPU and it is implemented in an asynchronous way.
In addition, vhost supports M:N mapping between vrings and DMA virtual channels. Specifically, one vring can use multiple different DMA
channels and one DMA channel can be shared by multiple vrings at the same time. Vhost enqueue operation with CBDMA channels is supported
in both split and packed ring.

This document provides the test plan for testing the following features when Vhost-user using asynchronous data path with
DSA driver (kernel IDXD driver and DPDK vfio-pci driver) in loopback virtio-user topology.
1. Virtio-user server mode is a feature to enable virtio-user as the server, vhost as the client, thus after vhost-user is killed then relaunched,
virtio-user can reconnect back to vhost-user again; at another hand, virtio-user also can reconnect back to vhost-user after virtio-user is killed.
This feature test need cover different rx/tx paths with virtio 1.0 and virtio 1.1, includes split ring mergeable, non-mergeable, inorder mergeable,
inorder non-mergeable, vector_rx path and packed ring mergeable, non-mergeable, inorder non-mergeable, inorder mergeable, vectorized path.
2. Check payload valid after packets forwarding many times.
3. Stress test with large chain packets.

IOMMU impact:
If iommu off, idxd can work with iova=pa
If iommu on, kernel dsa driver only can work with iova=va by program IOMMU, can't use iova=pa(fwd not work due to pkts payload wrong).

Note:
1. When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
exceed IOMMU's max capability, better to use 1G guest hugepage.
2. DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd, and the suite has not yet been automated.

Topology
--------
	Test flow: Vhost-user <-> Virtio-user

General set up
--------------
1. Compile DPDK::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=<dpdk build dir>
	# ninja -C <dpdk build dir> -j 110

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

Test Case 1: loopback split ring server mode large chain packets stress test with dsa dpdk driver
---------------------------------------------------------------------------------------------------
This is a stress test case about forwading large chain packets in loopback vhost-user/virtio-user split ring with server mode 
when vhost uses the asynchronous enqueue operations with dsa dpdk driver. Both iova as VA and PA mode test.

1. Bind 1 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f6:01.0

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost -a 0000:f6:01.0,max_queues=1 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0],client=1' \
	--iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --mbuf-size=45535 --lcore-dma=[lcore3@0000:f6:01.0-q0]

3. launch virtio and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4  --file-prefix=testpmd0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048,server=1 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd>start

4. Send large pkts from vhost and check the stats::

	testpmd>set txpkts 45535,45535,45535,45535,45535
	testpmd>start tx_first 32
	testpmd>show port stats all

5. Stop and quit vhost testpmd and relaunch vhost with pa mode by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost -a 0000:f6:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0],client=1' \
	--iova=pa -- -i --nb-cores=1 --txd=1024 --rxd=1024 --mbuf-size=45535 --lcore-dma=[lcore3@0000:f6:01.0-q0]

6. rerun step 4.

Test Case 2: loopback packed ring server mode large chain packets stress test with dsa dpdk driver
----------------------------------------------------------------------------------------------------
This is a stress test case about forwading large chain packets in loopback vhost-user/virtio-user packed ring with server mode
when vhost uses the asynchronous enqueue operations with dsa dpdk driver. Both iova as VA and PA mode test.

1. Bind 1 dsa port to vfio-pci as common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f6:01.0

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 -a 0000:6f:01.0,max_queues=1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0],client=1' \
	--iova=va -- -i --nb-cores=1 --mbuf-size=45535 --lcore-dma=[lcore3@0000:6f:01.0-q0]

3. launch virtio and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4  --file-prefix=testpmd0 --no-pci  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048,server=1 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd>start

4. Send large pkts from vhost and check the stats::

	testpmd>set txpkts 45535,45535,45535,45535,45535
	testpmd>start tx_first 32
	testpmd>show port stats all

5. Stop and quit vhost testpmd and relaunch vhost with pa mode by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 -a 0000:6f:01.0,max_queues=1 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0],client=1' \
	--iova=va -- -i --nb-cores=1 --mbuf-size=45535 --lcore-dma=[lcore3@0000:6f:01.0-q0]

6. rerun step 3.

Test Case 3: loopback split ring all path server mode and multi-queues payload check with dsa dpdk driver
-----------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user split ring
all path multi-queues with server mode when vhost uses the asynchronous enqueue operations with dsa dpdk driver. Both iova as VA and PA mode test.

1. bind 3 dsa port to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0
	./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0 6f:01.0 74:01.0

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:6a:01.0,max_queues=4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:6a:01.0-q0,lcore12@0000:6a:01.0-q0,lcore13@0000:6a:01.0-q1,lcore13@0000:6a:01.0-q2,lcore14@0000:6a:01.0-q1,lcore14@0000:6a:01.0-q2,lcore15@0000:6a:01.0-q1,lcore15@0000:6a:01.0-q2]

3. Launch virtio-user with split ring mergeable inorder path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large pkts from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd csum
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

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
	testpmd> show port stats all
	testpmd> stop

13. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

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

19. Quit and relaunch vhost with diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:6a:01.0 -a 0000:6f:01.0 -a 0000:74:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:6a:01.0-q0,lcore12@0000:6a:01.0-q0,lcore13@0000:6f:01.0-q1,lcore13@0000:74:01.0-q2,lcore14@0000:6f:01.0-q1,lcore14@0000:74:01.0-q2,lcore15@0000:6f:01.0-q1,lcore15@0000:74:01.0-q2]

20. Rerun steps 11-14.

21. Quit and relaunch vhost w/ iova=pa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:6a:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=pa -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:6a:01.0-q0,lcore12@0000:6a:01.0-q0,lcore13@0000:6a:01.0-q1,lcore13@0000:6a:01.0-q2,lcore14@0000:6a:01.0-q1,lcore14@0000:6a:01.0-q2,lcore15@0000:6a:01.0-q1,lcore15@0000:6a:01.0-q2]

22. Rerun steps 11-14.

Test Case 4: loopback packed ring all path server mode and multi-queues payload check with dsa dpdk driver
------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user packed ring
all path multi-queues with server mode when vhost uses the asynchronous enqueue operations with dsa dpdk driver. Both iova as VA and PA mode test.

1. bind 8 dsa port to vfio-pci like common step 1::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:6a:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq6;txq7]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:6a:01.0-q0,lcore11@0000:6a:01.0-q7,lcore12@0000:6a:01.0-q1,lcore12@0000:6a:01.0-q2,lcore12@0000:6a:01.0-q3,lcore13@0000:6a:01.0-q2,lcore13@0000:6a:01.0-q3,lcore13@0000:6a:01.0-q4,lcore14@0000:6a:01.0-q2,lcore14@0000:6a:01.0-q3,lcore14@0000:6a:01.0-q4,lcore14@0000:6a:01.0-q5,lcore15@0000:6a:01.0-q0,lcore15@0000:6a:01.0-q1,lcore15@0000:6a:01.0-q2,lcore15@0000:6a:01.0-q3,lcore15@0000:6a:01.0-q4,lcore15@0000:6a:01.0-q5,lcore15@0000:6a:01.0-q6,lcore15@0000:6a:01.0-q7]

3. Launch virtio-user with packed ring mergeable inorder path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large pkts from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd csum
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost and rerun step 4-6.

8. Quit and relaunch virtio with packed ring mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Rerun steps 4-7.

10. Quit and relaunch virtio with packed ring non-mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

11. Rerun step 4.

12. Send pkts from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd csum
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> show port stats all
	testpmd> stop

13. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

14. Quit and relaunch vhost and rerun step 11-13.

15. Quit and relaunch virtio with packed ring inorder non-mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

16. Rerun step 11-14.

17. Quit and relaunch virtio with packed ring vectorized path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

18. Rerun step 11-14.

19. Quit and relaunch virtio with packed ring vectorized path and ring size is not power of 2 as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1025 --rxd=1025
	testpmd>set fwd csum
	testpmd>start

20. Rerun step 11-14.

21. Quit and relaunch vhost with diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:6a:01.0 -a 0000:6f:01.0 -a 0000:74:01.0 -a 0000:79:01.0 -a 0000:e7:01.0 -a 0000:ec:01.0 -a 0000:f1:01.0 -a 0000:f6:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq6;txq7]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:6a:01.0-q0,lcore11@0000:f6:01.0-q7,lcore12@0000:6f:01.0-q1,lcore12@0000:74:01.0-q2,lcore12@0000:79:01.0-q3,lcore13@0000:74:01.0-q2,lcore13@0000:79:01.0-q3,lcore13@0000:e7:01.0-q4,lcore14@0000:74:01.0-q2,lcore14@0000:79:01.0-q3,lcore14@0000:e7:01.0-q4,lcore14@0000:ec:01.0-q5,lcore15@0000:6a:01.0-q0,lcore15@0000:6f:01.0-q1,lcore15@0000:74:01.0-q2,lcore15@0000:79:01.0-q3,lcore15@0000:e7:01.0-q4,lcore15@0000:ec:01.0-q5,lcore15@0000:f1:01.0-q6,lcore15@0000:f6:01.0-q7]

22. Rerun steps 11-14.

23. Quit and relaunch vhost w/ iova=pa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:6a:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq6;txq7]' \
	--iova=pa -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@0000:6a:01.0-q0,lcore11@0000:6a:01.0-q7,lcore12@0000:6a:01.0-q1,lcore12@0000:6a:01.0-q2,lcore12@0000:6a:01.0-q3,lcore13@0000:6a:01.0-q2,lcore13@0000:6a:01.0-q3,lcore13@0000:6a:01.0-q4,lcore14@0000:6a:01.0-q2,lcore14@0000:6a:01.0-q3,lcore14@0000:6a:01.0-q4,lcore14@0000:6a:01.0-q5,lcore15@0000:6a:01.0-q0,lcore15@0000:6a:01.0-q1,lcore15@0000:6a:01.0-q2,lcore15@0000:6a:01.0-q3,lcore15@0000:6a:01.0-q4,lcore15@0000:6a:01.0-q5,lcore15@0000:6a:01.0-q6,lcore15@0000:6a:01.0-q7]

24. Rerun steps 3-6.

Test Case 5: loopback split ring server mode large chain packets stress test with dsa kernel driver
---------------------------------------------------------------------------------------------------
This is a stress test case about forwading large chain packets in loopback vhost-user/virtio-user split ring with server mode
when vhost uses the asynchronous enqueue operations with dsa kernel driver.

1. Bind 1 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
	ls /dev/dsa #check wq configure success

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0],client=1' \
	--iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --mbuf-size=45535 --lcore-dma=[lcore3@wq0.2]

3. launch virtio and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4  --file-prefix=testpmd0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048,server=1 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd>start

4. Send large pkts from vhost::

	testpmd>set txpkts 45535,45535,45535,45535,45535
	testpmd>start tx_first 32
	testpmd>show port stats all

Test Case 6: loopback packed ring server mode large chain packets stress test with dsa kernel driver
-----------------------------------------------------------------------------------------------------
This is a stress test case about forwading large chain packets in loopback vhost-user/virtio-user packed ring with server mode
when vhost uses the asynchronous enqueue operations with dsa kernel driver.

1. Bind 1 dsa port to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	ls /dev/dsa #check wq configure success

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0],client=1' \
	--iova=va -- -i --nb-cores=1 --mbuf-size=45535 --lcore-dma=[lcore3@wq0.0]

3. launch virtio and start testpmd::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4  --file-prefix=testpmd0 --no-pci  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048,server=1 \
	-- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
	testpmd>start

4. Send large pkts from vhost and check the stats::

	testpmd>set txpkts 45535,45535,45535,45535,45535
	testpmd>start tx_first 32
	testpmd>show port stats all

Test Case 7: loopback split ring all path server mode and multi-queues payload check with dsa kernel driver
-------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user split ring
all path multi-queues with server mode when vhost uses the asynchronous enqueue operations with dsa kernel driver.

1. bind 3 dsa port to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 4
	ls /dev/dsa #check wq configure success

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.0,lcore13@wq0.1,lcore13@wq0.2,lcore14@wq0.1,lcore14@wq0.2,lcore15@wq0.1,lcore15@wq0.2]

3. Launch virtio-user with split ring mergeable inorder path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	 testpmd>set fwd csum
	 testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large pkts from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd csum
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost and rerun step 4-6.

8. Quit and relaunch virtio with split ring mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Rerun steps 4-7.

10. Quit and relaunch virtio with split ring non-mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
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

13. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

14. Quit and relaunch vhost and rerun step 11-13.

15. Quit and relaunch virtio with split ring inorder non-mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

16. Rerun step 11-14.

17. Quit and relaunch virtio with split ring vectorized path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

18. Rerun step 11-14.

19. Quit and relaunch vhost with diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:6a:01.0 -a 0000:6f:01.0 -a 0000:74:01.0 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore12@wq0.0,lcore13@wq2.1,lcore13@wq4.2,lcore14@wq2.1,lcore14@wq4.2,lcore15@wq2.1,lcore15@wq4.2]

20. Rerun steps 11-14.

Test Case 8: loopback packed ring all path server mode and multi-queues payload check with dsa kernel driver
-------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user packed ring
all path multi-queues with server mode when vhost uses the asynchronous enqueue operations with dsa kernel driver.

1. bind 8 dsa port to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0 79:01.0 e7:01.0 ec:01.0 f1:01.0 f6:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 4
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 6
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 8
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 10
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 12
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 14
	ls /dev/dsa #check wq configure success

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq6;txq7]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore11@wq0.7,lcore12@wq0.1,lcore12@wq0.2,lcore12@wq0.3,lcore13@wq0.2,lcore13@wq0.3,lcore13@wq0.4,lcore14@wq0.2,lcore14@wq0.3,lcore14@wq0.4,lcore14@wq0.5,lcore15@wq0.0,lcore15@wq0.1,lcore15@wq0.2,lcore15@wq0.3,lcore15@wq0.4,lcore15@wq0.5,lcore15@wq0.6,lcore15@wq0.7]

3. Launch virtio-user with packed ring mergeable inorder path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=./pdump-virtio-rx-0.pcap,mbuf-size=8000' \
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large pkts from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd csum
	testpmd> set txpkts 64,64,64,2000,2000,2000
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> stop

6. Quit pdump, check all the packets length are 6192 Byte in the pcap file and the payload in receive packets are same.

7. Quit and relaunch vhost and rerun step 4-6.

8. Quit and relaunch virtio with packed ring mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Rerun steps 4-7.

10. Quit and relaunch virtio with packed ring non-mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

11. Rerun step 4.

12. Send pkts from vhost, check loopback performance can get expected and each queue can receive packets::

	testpmd> set fwd csum
	testpmd> set txpkts 64,128,256,512
	testpmd> set burst 1
	testpmd> start tx_first 1
	testpmd> stop

13. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

14. Quit and relaunch vhost and rerun step 11-13.

15. Quit and relaunch virtio with packed ring inorder non-mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

16. Rerun step 11-14.

17. Quit and relaunch virtio with packed ring vectorized path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

18. Rerun step 11-14.

19. Quit and relaunch virtio with packed ring vectorized path and ring size is not power of 2 as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1025 --rxd=1025
	testpmd>set fwd csum
	testpmd>start

20. Rerun step 11-14.

21. Quit and relaunch vhost with diff channel::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq6;txq7]' \
	--iova=va -- -i --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore11@wq0.0,lcore11@wq14.7,lcore12@wq2.1,lcore12@wq4.2,lcore12@wq6.3,lcore13@wq4.2,lcore13@wq6.3,lcore13@wq8.4,lcore14@wq4.2,lcore14@wq6.3,lcore14@wq8.4,lcore14@wq10.5,lcore15@wq0.0,lcore15@wq2.1,lcore15@wq4.2,lcore15@wq6.3,lcore15@wq8.4,lcore15@wq10.5,lcore15@wq12.6,lcore15@wq14.7]

22. Rerun steps 3-6.

Test Case 9: loopback split and packed ring server mode multi-queues and mergeable path payload check with dsa dpdk and kernel driver
--------------------------------------------------------------------------------------------------------------------------------------
This case tests the payload is valid after forwading large chain packets in loopback vhost-user/virtio-user split and packed ring
multi-queues with server mode when vhost uses the asynchronous enqueue operations with dsa kernel driver.

1. bind 4 dsa device to idxd and 2 dsa device to vfio-pci like common step 1-2::

	ls /dev/dsa #check wq configure, reset if exist
	./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 74:01.0 79:01.0
	./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 74:01.0 79:01.0
	./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 2
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 4
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 6
	ls /dev/dsa #check wq configure success

2. Launch vhost::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 --file-prefix=vhost -a 0000:e7:01.0,max_queues=4 -a 0000:ec:01.0,max_queues=4 \
	--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--iova=va -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024 \
	--lcore-dma=[lcore3@wq0.0,lcore3@wq2.0,lcore3@wq4.0,lcore3@wq6.0,lcore3@0000:e7:01.0-q0,lcore3@0000:e7:01.0-q2,lcore3@0000:ec:01.0-q3]

3. Launch virtio-user with split ring mergeable inorder path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4-5 -n 4 --file-prefix=virtio-user --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

4. Attach pdump secondary process to primary process by same file-prefix::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user -- \
	--pdump 'device_id=net_virtio_user0,queue=0,rx-dev=/tmp/pdump-virtio-rx-0.pcap,mbuf-size=8000'
	--pdump 'device_id=net_virtio_user0,queue=3,rx-dev=./pdump-virtio-rx-3.pcap,mbuf-size=8000'

5. Send large pkts from vhost, check loopback performance can get expected and each queue can receive packets::

	 testpmd>set fwd csum
	 testpmd>set txpkts 64,64,64,2000,2000,2000
	 testpmd>set burst 1
	 testpmd>start tx_first 1

6. Quit pdump and chcek all the packets length is 6192 and the payload of all packets are same in the pcap file.

7. Quit and relaunch vhost and rerun step 4-6.

8. Quit and relaunch virtio with split ring mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4-5 -n 4 --file-prefix=virtio-user --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

9. Stop vhost and rerun step 4-7.

10. Quit and relaunch virtio with packed ring mergeable inorder path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4-5 -n 4 --file-prefix=virtio-user --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

11. Stop vhost and rerun step 4-7.

12. Quit and relaunch virtio with packed ring mergeable path as below::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4-5 -n 4 --file-prefix=virtio-user --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1 \
	-- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
	testpmd>set fwd csum
	testpmd>start

13. Stop vhost and rerun step 4-7.