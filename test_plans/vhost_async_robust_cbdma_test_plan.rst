.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2023 Intel Corporation

=================================================
vhost async data-path robust with cbdma test plan
=================================================

Description
===========

This document provides the test plan for testing Vhost asynchronous
data path robust with CBDMA driver.

CBDMA is a kind of DMA engine, Vhost asynchronous data path leverages DMA devices
to offload memory copies from the CPU and it is implemented in an asynchronous way.
As a result, large packet copy can be accelerated by the DMA engine, and vhost can
free CPU cycles for higher level functions.

Asynchronous data path is enabled per tx/rx queue, and users need
to specify the DMA device used by the tx/rx queue. Each tx/rx queue
only supports to use one DMA device, but one DMA device can be shared
among multiple tx/rx queues of different vhostpmd ports.

Two PMD parameters are added:
- dmas:	specify the used DMA device for a tx/rx queue
(Default: no queues enable asynchronous data path)
- dma-ring-size: DMA ring size.
(Default: 4096).

Here is an example:
--vdev 'eth_vhost0,iface=./s0,dmas=[txq0@0000:00.01.0;rxq0@0000:00.01.1],dma-ring-size=4096'

Test case
=========

Common steps
------------
1. Bind 1 NIC port and CBDMA devices to vfio-pci::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DMA device id>

    For example, Bind 1 NIC port and 2 CBDMA devices::
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:18.0
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:04.0,0000:00:04.1

2. Send imix packets [64,1518] to NIC by traffic generator::

    The TCP imix packets include packet size [64, 128, 256, 512, 1024, 1518], and the format of packet is as follows.
    +-------------+-------------+-------------+-------------+
    | MAC         | MAC         | IPV4        | IPV4        |
    | Src address | Dst address | Src address | Dst address |
    |-------------|-------------|-------------|-------------|
    | Random MAC  | Virtio mac  | Random IP   | Random IP   |
    +-------------+-------------+-------------+-------------+
    All the packets in this test plan use the Virtio mac: 00:11:22:33:44:10.

Test Case 1: PVP virtio-user quit test
--------------------------------------
This case is designed to test if virtio-user can quit normally regardless of whether the back-end stop sending packets.

1. Bind 1 NIC port and 1 CBDMA devices to vfio-pci as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
	-a 0000:18:00.1 -a 0000:00:04.0 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=1,dmas=[txq0@0000:00:04.0;rxq0@0000:00:04.0]' \
	--iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=1,queues=1 \
	-- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Send TCP imix packets [64,1518] from packet generator as common step2.

5. Quit virtio-user and relaunch virtio-user as step 3 while sending packets from packet generator.

6. Stop vhost port, then quit virtio-user and reluanch virtio-user as step 3 while sending packets from packet generator.

7. Stop sending packets from packet generator, then quit virtio-user and vhost.

Test Case 2: PVP vhost-user quit test
-------------------------------------
This case is designed to test if vhost-user can quit normally regardless of whether the back-end stop sending packets.

1. Bind 1 NIC port and 1 CBDMA devices to vfio-pci as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
	-a 0000:18:00.1 -a 0000:00:04.0 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=1,client=1,dmas=[txq0@0000:00:04.0;rxq0@0000:00:04.0]' \
	--iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=1,queues=1,server=1 \
	-- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Send TCP imix packets [64,1518] from packet generator as common step2.

5. Quit vhost-user and relaunch vhost-user as step 2 while sending packets from packet generator.

6. Stop sending packets from packet generator, then quit vhost-user and virtio-user.

Test Case 3: PVP vhost async test with redundant device parameters
------------------------------------------------------------------
This case is designed to test if vhostpmd can work normally when binding and using redundant device parameters.

1. Bind 1 NIC port and 4 CBDMA devices to vfio-pci as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
	-a 0000:18:00.1 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=1,client=1,dmas=[txq0@0000:00:04.1;rxq0@0000:00:04.1]' \
	--iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd> set fwd mac
	testpmd> start

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=1,queues=1,server=1 \
	-- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, check the throughput.

Test Case 4: Loopback vhost async test with each queue using 2 DMA devices
--------------------------------------------------------------------------
Since each tx/rx queue only supports to use one DMA device, this case is designed to test if vhostpmd can work normally when each queue using 2 DMA devices.

1. Bind 3 CBDMA devices to vfio-pci as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq0@0000:00:04.1;rxq0@0000:00:04.1;rxq0@0000:00:04.2]' \
	--iova=va -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd mac

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=1,queues=2,server=1 \
	-- -i --nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Send packets from vhost-user testpmd, check the throughput::

	testpmd>set txpkts 1024
	testpmd>start tx_first 32
	testpmd>show port stats all

Test Case 5: Loopback vhost async test with dmas parameters out of order
------------------------------------------------------------------------
This case is designed to test if vhostpmd can work normally when dmas parameters out of order.

1. Bind 2 CBDMA devices to vfio-pci as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
	-a 0000:00:04.0 -a 0000:00:04.1 \
	--vdev 'net_vhost0,iface=./vhost_net0,queues=4,client=1,dmas=[rxq3@0000:00:04.1;txq0@0000:00:04.0;rxq1@0000:00:04.0;txq2@0000:00:04.1]' \
	--iova=va -- -i --nb-cores=1 --txq=4 --rxq=4 --txd=1024 --rxd=1024
	testpmd> set fwd mac

3. Launch virtio-user with inorder mergeable path::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-6 --no-pci --file-prefix=virtio \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost_net0,mrg_rxbuf=1,in_order=1,queues=4,server=1 \
	-- -i --nb-cores=1 --txq=4 --rxq=4 --txd=1024 --rxd=1024
	testpmd> set fwd csum
	testpmd> start

4. Send packets from vhost-user testpmd, check the throughput::

	testpmd>set txpkts 1024
	testpmd>start tx_first 32
	testpmd>show port stats all

Test Case 6: VM2VM split and packed ring mergeable path with cbdma enable and server mode
-----------------------------------------------------------------------------------------
This case tests split and packed ring with cbdma can work normally when the front-end change from virtio-net to virtio-pmd.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch the testpmd with 2 vhost ports below commands::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1;txq2@0000:00:04.2;txq3@0000:00:04.3;txq4@0000:00:04.4;txq5@0000:00:04.1;rxq2@0000:00:04.2;rxq3@0000:00:04.3;rxq4@0000:00:04.4;rxq5@0000:00:04.5;rxq6@0000:00:04.6;rxq7@0000:00:04.7]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1;txq2@0000:80:04.2;txq3@0000:80:04.3;txq4@0000:80:04.4;txq5@0000:80:04.1;rxq2@0000:80:04.2;rxq3@0000:80:04.3;rxq4@0000:80:04.4;rxq5@0000:80:04.5;rxq6@0000:80:04.6;rxq7@0000:80:04.7]' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd> start

3. Launch VM1 and VM2::

	taskset -c 6-16 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 17-27 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 8
	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 8
	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	Under VM1, run: `scp <xxx> root@1.1.1.8:/`   <xxx> is the file name

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

8. On VM1 and VM2, bind virtio device with vfio-pci driver::

	modprobe vfio
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

9. Launch testpmd in VM1::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set mac fwd
	testpmd> start

10. Launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024
	testpmd> set mac fwd
	testpmd> set txpkts 64,256,512
	testpmd> start tx_first 32
	testpmd> show port stats all

11. Rerun step 4-10.