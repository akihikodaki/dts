.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation


==================================================
VM2VM vhost-user/virtio-user with CBDMA test plan
==================================================

Description
===========

Vhost asynchronous data path leverages DMA devices to offload memory copies from the CPU and it is implemented in an asynchronous way.
In addition, vhost supports M:N mapping between vrings and DMA virtual channels. Specifically, one vring can use multiple different DMA
channels and one DMA channel can be shared by multiple vrings at the same time. From DPDK22.07, Vhost enqueue and dequeue operation with
CBDMA channels is supported in both split and packed ring.

This document provides the test plan for testing the following features when Vhost-user using asynchronous data path with
CBDMA channels in VM2VM virtio-user topology.
1. Split virtqueue vm2vm in-order mergeable, in-order non-mergeable, mergeable, non-mergeable, vector_rx path test and payload check.
2. Packed virtqueue vm2vm in-order mergeable, in-order non-mergeable, mergeable, non-mergeable, vectorized path (ringsize not powerof 2) test and payload check.
3. Test indirect descriptor feature.
For example, the split ring mergeable inorder path use non-indirect descriptor, the 2000,2000,2000,2000 chain packets will need 4 consequent ring,
still need one ring put header.
The split ring mergeable path use indirect descriptor, the 2000,2000,2000,2000 chain packets will only occupy one ring.

Note:
1.When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
exceed IOMMU's max capability, better to use 1G guest hugepage.
2.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

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

    For example, 2 CBDMA channels:
    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:04.0 0000:00:04.1

Test Case 1: VM2VM split ring non-mergeable path multi-queues payload check with cbdma enable
---------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user split ring non-mergeable path
and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:04.0 -a 0000:00:04.1 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
    -- -i --enable-hw-vlan-strip --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
    -- -i --enable-hw-vlan-strip --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
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

5. Start vhost testpmd, check virtio-user1 RX-packets is 566 and RX-bytes is 486016, 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:04.0 -a 0000:00:04.1 \
	--vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
	--iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
	--lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1]

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

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

10. Rerun step 5.

Test Case 2: VM2VM split ring inorder non-mergeable path multi-queues payload check with cbdma enable
-----------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user split ring inorder non-mergeable path
and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 1
    testpmd>set txpkts 64
	testpmd>start tx_first 27
	testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 64,256,2000,64,256,2000
	testpmd>start tx_first 1
    testpmd>stop

5. Start vhost testpmd, check 502 packets and 32128 bytes received by virtio-user1 and 502 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4]

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 1
	testpmd>start tx_first 27
	testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 64,256,2000,64,256,2000
	testpmd>start tx_first 1
    testpmd>stop

10. Rerun step 5.

Test Case 3: VM2VM split ring vectorized path multi-queues payload check with cbdma enable
------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user split ring vectorized path
and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,,vectorized=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

5. Start vhost testpmd, check 448 packets and 28672 bytes received by virtio-user1 and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

10. Rerun step 5.

Test Case 4: VM2VM split ring inorder mergeable path test non-indirect descriptor with cbdma enable
---------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and non-indirect descriptor after packets forwarding in vhost-user/virtio-user
split ring inorder mergeable path and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both
iova as VA and PA mode test.

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets(include 251 small packets and 32 8K packets)::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>set txpkts 64
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1
    testpmd>stop

5. Start vhost, then quit pdump and three testpmd, about split virtqueue inorder mergeable path, it use the non-direct descriptors, the 8k length pkt will occupies 5 ring:2000,2000,2000,2000 will need 4 consequent ring,
still need one ring put header. So check 504 packets and 48128 bytes received by virtio-user1 and 502 packets with 64 length and 2 packets with 8K length in pdump-virtio-rx.pcap.

6. Relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3]

7. Rerun step 2-5.

Test Case 5: VM2VM split ring mergeable path test indirect descriptor with cbdma enable
---------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and indirect descriptor after packets forwarding in vhost-user/virtio-user
split ring mergeable path and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets(include 251 small packets and 32 8K packets)::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>set txpkts 64
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1
    testpmd>stop

5. Start vhost, then quit pdump and three testpmd, about split virtqueue mergeable path, it use the indirect descriptors, the 8k length pkt will just occupies one ring.
So check 512 packets and 112128 bytes received by virtio-user1 and 502 packets with 64 length and 10 packets with 8K length in pdump-virtio-rx.pcap.

6. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0;rxq1]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;txq1;rxq0;rxq1]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3]

7. Rerun step 2-5.

Test Case 6: VM2VM packed ring non-mergeable path multi-queues payload check with cbdma enable
----------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring non-mergeable path
and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:04.0 -a 0000:00:04.1 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0;rxq1]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;txq1;rxq0;rxq1]' \
    --iova=va -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

5. Start vhost testpmd, check virtio-user1 RX-packets is 448 and RX-bytes is 28672, 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:04.0 -a 0000:00:04.1 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
    --iova=pa -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1]

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

10. Rerun step 5.

Test Case 7: VM2VM packed ring mergeable path multi-queues payload check with cbdma enable
------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring mergeable path
and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:04.0 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
    --iova=va -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

5. Start vhost testpmd, then quit pdump, check 502 packets and 279232 bytes received by virtio-user1 and 54 packets with 4640 length and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:04.0 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0;rxq1]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;txq1;rxq0;rxq1]' \
    --iova=pa -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0]

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

10. Rerun step 5.

Test Case 8: VM2VM packed ring inorder mergeable path multi-queues payload check with cbdma enable
--------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring inorder mergeable path
and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

5. Start vhost testpmd, then quit pdump, check 502 packets and 279232 bytes received by virtio-user1 and 54 packets with 4640 length and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;rxq0;rxq1]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;txq1;rxq0]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4]

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

10. Rerun step 5.

Test Case 9: VM2VM packed ring inorder non-mergeable path multi-queues payload check with cbdma enable
------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring inorder non-mergeable path
and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq1;rxq1]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

5. Start vhost testpmd, then quit pdump, check 448 packets and 28672 bytes received by virtio-user1 and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq1;rxq1]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

10. Rerun step 5.

Test Case 10: VM2VM packed ring vectorized-rx path multi-queues payload check with cbdma enable
-----------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring vectorized-rx path
and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq1;rxq1]' \
    --iova=va -- -i --nb-cores=2 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore12@0000:00:04.4,lcore12@0000:00:04.5,lcore12@0000:00:04.6,lcore12@0000:00:04.7]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

5. Start vhost testpmd, then quit pdump, check 448 packets and 28672 bytes received by virtio-user1 and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq1;rxq1]' \
    --iova=pa -- -i --nb-cores=2 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore12@0000:00:04.4,lcore12@0000:00:04.5,lcore12@0000:00:04.6,lcore12@0000:00:04.7]

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

10. Rerun step 5.

Test Case 11: VM2VM packed ring vectorized path multi-queues payload check test with ring size is not power of 2 with cbdma enable
----------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid after packets forwarding in vhost-user/virtio-user packed ring vectorized path with ring size is not power of 2
and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[txq0;txq1;rxq0;rxq1]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;txq1;rxq0;rxq1]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --force-max-simd-bitwidth=512  --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

5. Start vhost testpmd, then quit pdump, check 448 packets and 28672 bytes received by virtio-user1 and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq1]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore12@0000:00:04.3,lcore12@0000:00:04.4,lcore12@0000:00:04.5,lcore12@0000:00:04.6,lcore12@0000:00:04.7]

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

10. Rerun step 5.

Test Case 12: VM2VM packed ring vectorized-tx path multi-queues test indirect descriptor and payload check with cbdma enable
----------------------------------------------------------------------------------------------------------------------------
This case uses testpmd to test the payload is valid and indirect descriptor after packets forwarding in vhost-user/virtio-user
packed ring vectorized-tx path and multi-queues when vhost uses the asynchronous operations with CBDMA channels. Both iova as VA and PA mode test.

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq1]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256

    testpmd>set burst 1
    testpmd>set txpkts 64
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1
    testpmd>stop

5. Start vhost, then quit pdump and three testpmd, about packed virtqueue vectorized-tx path, it use the indirect descriptors, the 8k length pkt will just occupies one ring.
So check 512 packets and 112128 bytes received by virtio-user1 and 502 packets with 64 length and 10 packets with 8K length in pdump-virtio-rx.pcap.

6. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=2,client=1,dmas=[rxq0;rxq1]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=2,client=1,dmas=[txq0;txq1]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]

7. Rerun step 2-5.

Test Case 13: VM2VM packed ring vectorized-tx path test batch processing with cbdma enable
------------------------------------------------------------------------------------------
This case uses testpmd to test that one packet can forwarding in vhost-user/virtio-user packed ring vectorized-tx path
when vhost uses the asynchronous operations with CBDMA channels.

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 10-18 -n 4 \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
    --vdev 'eth_vhost0,iface=/root/dpdk/vhost-net0,queues=1,client=1,dmas=[txq0;rxq0]' \
	--vdev 'eth_vhost1,iface=/root/dpdk/vhost-net1,queues=1,client=1,dmas=[txq0;rxq0]' \
    --iova=va -- -i --nb-cores=1 --txd=256 --rxd=256 --no-flush-rx \
    --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net1,queues=1,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 1 packet::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/root/dpdk/vhost-net0,queues=1,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 1
    testpmd>stop

5. Start vhost, then quit pdump and three testpmd, check 1 packet and 64 bytes received by virtio-user1 and 1 packet with 64 length in pdump-virtio-rx.pcap.
