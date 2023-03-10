.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=================================================
VM2VM vhost-user/virtio-net with CBDMA test plan
=================================================

Description
===========

CBDMA is a kind of DMA engine, Vhost asynchronous data path leverages DMA devices
to offload memory copies from the CPU and it is implemented in an asynchronous way.
As a result, large packet copy can be accelerated by the DMA engine, and vhost can
free CPU cycles for higher level functions. In addition, vhost supports M:N mapping
between vrings and DMA virtual channels. Specifically, one vring can use multiple
different DMA channels and one DMA channel can be shared by multiple vrings at the
same time. From DPDK22.07, Vhost enqueue and dequeue operation with CBDMA channels
is supported in both split and packed ring.

This document provides the test plan for testing the following features when Vhost-user using asynchronous data path with
CBDMA in VM2VM virtio-net topology.
1.Check Vhost tx offload（TSO） function by verifing the TSO/cksum in the TCP/IP stack with vm2vm split ring and packed ring
vhost-user/virtio-net mergeable path.
2.Check the payload of large packet (larger than 1MB) is valid after forwarding packets with vm2vm split ring
and packed ring vhost-user/virtio-net mergeable and non-mergeable path.
3.Multi-queues number dynamic change in vm2vm vhost-user/virtio-net with split ring and packed ring.
4. Rx/Tx csum in SW and legacy mode.

.. note::

   1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > 5.1, and packed ring multi-queues not support reconnect in qemu yet.
   2.For split virtqueue virtio-net with multi-queues server mode test, better to use qemu version >= 5.2.0, dut to qemu(v4.2.0~v5.1.0) exist split ring multi-queues reconnection issue.
   3.When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
   exceed IOMMU's max capability, better to use 1G guest hugepage.
   4.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd. In this patch,
   we enable asynchronous data path for vhostpmd. Asynchronous data path is enabled per tx/rx queue, and users need to specify
   the DMA device used by the tx/rx queue. Each tx/rx queue only supports to use one DMA device (This is limited by the
   implementation of vhostpmd), but one DMA device can be shared among multiple tx/rx queues of different vhost PMD ports.

   Two PMD parameters are added:
   - dmas: specify the used DMA device for a tx/rx queue.(Default: no queues enable asynchronous data path)
   - dma-ring-size: DMA ring size.(Default: 4096).

   Here is an example:
   --vdev 'eth_vhost0,iface=./s0,dmas=[txq0@0000:00.01.0;rxq0@0000:00.01.1],dma-ring-size=2048'

   For more about dpdk-testpmd sample, please refer to the DPDK docments:
   https://doc.dpdk.org/guides/testpmd_app_ug/run_app.html
   For more about qemu, you can refer to the qemu doc: https://qemu-project.gitlab.io/qemu/system/invocation.html

Prerequisites
=============

Topology
--------
	Test flow: Virtio-net-->Vhost-user-->Testpmd-->Vhost-user-->Virtio-net

Software
--------
	iperf
	qemu: https://download.qemu.org/qemu-7.1.0.tar.xz

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
1. Bind 2 CBDMA channels to vfio-pci::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DMA device id>

	For example, Bind 1 NIC port and 2 CBDMA channels:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:04.0 0000:00:04.1

Test Case 1: VM2VM virtio-net split ring CBDMA enable test with tcp traffic
---------------------------------------------------------------------------
This case test the function of Vhost TSO in the topology of vhost-user/virtio-net split ring mergeable path
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 2 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --file-prefix=vhost -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[txq0@0000:00:01.0;rxq0@0000:00:01.0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[txq0@0000:00:01.1;rxq0@0000:00:01.1]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --txq=1 --rxq=1
	testpmd>start

3. Launch VM1 and VM2::

	taskset -c 32 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

	taskset -c 33 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

7. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1518, Port 1 should have rx packets above 1518::

	testpmd>show port xstats all

Test Case 2: VM2VM virtio-net split ring mergeable 8 queues CBDMA enable test with large packet payload valid check
-------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net split ring mergeable path when vhost uses the asynchronous operations with CBDMA channels.
The dynamic change of multi-queues number and iova as VA and PA mode also test.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	-a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 -a 0000:00:01.4 -a 0000:00:01.5 -a 0000:00:01.6 -a 0000:00:01.7 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.1;txq3@0000:00:01.1;txq4@0000:00:01.2;txq5@0000:00:01.2;txq6@0000:00:01.3;txq7@0000:00:01.3;rxq0@0000:00:01.4;rxq1@0000:00:01.4;rxq2@0000:00:01.5;rxq3@0000:00:01.5;rxq4@0000:00:01.6;rxq5@0000:00:01.6;rxq6@0000:00:01.7;rxq7@0000:00:01.7]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.1;txq3@0000:00:01.1;txq4@0000:00:01.2;txq5@0000:00:01.2;txq6@0000:00:01.3;txq7@0000:00:01.3;rxq0@0000:00:01.4;rxq1@0000:00:01.4;rxq2@0000:00:01.5;rxq3@0000:00:01.5;rxq4@0000:00:01.6;rxq5@0000:00:01.6;rxq6@0000:00:01.7;rxq7@0000:00:01.7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>start

3. Launch VM1 and VM2 using qemu::

	taskset -c 32 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 40 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

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

8. Quit and relaunch vhost w/ diff CBDMA channels and legacy mode::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:00:01.0 -a 0000:00:01.1 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,legacy-ol-flags=1,queues=8,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.0;txq2@0000:00:01.0;txq3@0000:00:01.0;txq4@0000:00:01.0;txq5@0000:00:01.0;txq6@0000:00:01.0]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,legacy-ol-flags=1,queues=8,dmas=[txq1@0000:00:01.1;txq2@0000:00:01.1;txq3@0000:00:01.1;txq4@0000:00:01.1;txq5@0000:00:01.1;txq6@0000:00:01.1;txq7@0000:00:01.1]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>start

9. Rerun step 6-7.

10. Quit and relaunch vhost w/ iova=pa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	-a 0000:00:01.0 -a 0000:00:01.1 -a 0000:00:01.2 -a 0000:00:01.3 -a 0000:00:01.4 -a 0000:00:01.5 -a 0000:00:01.6 -a 0000:00:01.7 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8,dmas=[txq0@0000:00:01.0;txq1@0000:00:01.1;txq2@0000:00:01.0;txq3@0000:00:01.1;txq4@0000:00:01.0;txq5@0000:00:01.1;txq6@0000:00:01.2]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8,dmas=[rxq0@0000:00:01.2;rxq1@0000:00:01.3;rxq2@0000:00:01.2;rxq3@0000:00:01.3;rxq4@0000:00:01.2;rxq5@0000:00:01.3;rxq6@0000:00:01.4]' \
	--iova=pa -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>start

11. Rerun step 6-7.

12. Quit and relaunch vhost w/o CBDMA channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=4' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=4' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=4 --rxq=4
	testpmd>start

13. On VM1, set virtio device::

	ethtool -L ens5 combined 4

14. On VM2, set virtio device::

	ethtool -L ens5 combined 4

15. Scp 1MB file form VM1 to VM2::

	Under VM1, run: `scp <xxx> root@1.1.1.8:/`   <xxx> is the file name

16. Check the iperf performance and compare with CBDMA enable performance, ensure CMDMA enable performance is higher::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

17. Quit and relaunch vhost with 1 queues::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=4' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=4' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=1 --rxq=1
	testpmd>start

18. On VM1, set virtio device::

	ethtool -L ens5 combined 1

19. On VM2, set virtio device::

	ethtool -L ens5 combined 1

20. Scp 1MB file form VM1 to VM2M, check packets can be forwarding success by scp::

	Under VM1, run: `scp <xxx> root@1.1.1.8:/`   <xxx> is the file name

21. Check the iperf performance, ensure queue0 can work from vhost side::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

Test Case 3: VM2VM virtio-net split ring non-mergeable 8 queues CBDMA enable test with large packet payload valid check
-----------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net split ring non-mergeable path when vhost uses the asynchronous operations with CBDMA channels. 
The dynamic change of multi-queues number and the reconnection also test.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1;txq2@0000:00:04.2;txq3@0000:00:04.3;txq4@0000:00:04.4;txq5@0000:00:04.5;txq6@0000:00:04.6;txq7@0000:00:04.7;rxq0@0000:00:04.0;rxq1@0000:00:04.1;rxq2@0000:00:04.2;rxq3@0000:00:04.3;rxq4@0000:00:04.4;rxq5@0000:00:04.5;rxq6@0000:00:04.6;rxq7@0000:00:04.7],dma-ring-size=1024' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1;txq2@0000:80:04.2;txq3@0000:80:04.3;txq4@0000:80:04.4;txq5@0000:80:04.5;txq6@0000:80:04.6;txq7@0000:80:04.7;rxq0@0000:80:04.0;rxq1@0000:80:04.1;rxq2@0000:80:04.2;rxq3@0000:80:04.3;rxq4@0000:80:04.4;rxq5@0000:80:04.5;rxq6@0000:80:04.6;rxq7@0000:80:04.7],dma-ring-size=1024' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>start

3. Launch VM1 and VM2::

	taskset -c 32 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 40 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

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

8. Quit and relaunch vhost w/ diff CBDMA channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1;txq2@0000:00:04.2;txq3@0000:00:04.3;txq4@0000:00:04.4;txq5@0000:00:04.5]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8,dmas=[rxq2@0000:00:04.2;rxq30000:00:04.3;rxq4@0000:00:04.4;rxq5@0000:00:04.5;rxq6@0000:00:04.6;rxq7@0000:00:04.7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>start

9. Rerun step 6-7 five times.

10. Quit and relaunch vhost ports w/o CBDMA channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8' --vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>start

11. Scp 1MB file form VM1 to VM2::

	Under VM1, run: `scp <xxx> root@1.1.1.8:/`   <xxx> is the file name

12. Check the iperf performance and compare with CBDMA enable performance, ensure CMDMA enable performance is higher::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

13. Quit and relaunch vhost ports with 1 queues::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8' --vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=1 --rxq=1
	testpmd>start

14. On VM1, set virtio device::

	ethtool -L ens5 combined 1

15. On VM2, set virtio device::

	ethtool -L ens5 combined 1

16. Scp 1MB file form VM1 to VM2M, check packets can be forwarding success by scp::

	Under VM1, run: `scp <xxx> root@1.1.1.8:/`   <xxx> is the file name

17. Check the iperf performance, ensure queue0 can work from vhost side::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

Test Case 4: VM2VM virtio-net split ring mergeable 16 queues CBDMA enable test with Rx/Tx csum in SW
----------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net split ring mergeable path and 16 queues when vhost uses the asynchronous operations with CBDMA channels
and perform SW checksum in Rx/Tx path.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-9 -n 4 --file-prefix=vhost \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=16,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.1;txq3@0000:00:04.1;txq4@0000:00:04.2;txq5@0000:00:04.2;txq6@0000:00:04.3;txq7@0000:00:04.3;txq8@0000:00:04.4;txq9@0000:00:04.4;txq10@0000:00:04.5;txq11@0000:00:04.5;txq12@0000:00:04.6;txq13@0000:00:04.6;txq14@0000:00:04.7;txq15@0000:00:04.7;rxq0@0000:80:04.0;rxq1@0000:80:04.0;rxq2@0000:80:04.1;rxq3@0000:80:04.1;rxq4@0000:80:04.2;rxq5@0000:80:04.2;rxq6@0000:80:04.3;rxq7@0000:80:04.3;rxq8@0000:80:04.4;rxq9@0000:80:04.4;rxq10@0000:80:04.5;rxq11@0000:80:04.5;rxq12@0000:80:04.6;rxq13@0000:80:04.6;rxq14@0000:80:04.7;rxq15@0000:80:04.7]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=16,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1;txq2@0000:00:04.2;txq3@0000:00:04.3;txq4@0000:00:04.4;txq5@0000:00:04.5;txq6@0000:00:04.6;txq7@0000:00:04.7;txq8@0000:80:04.0;txq9@0000:80:04.1;txq10@0000:80:04.2;txq11@0000:80:04.3;txq12@0000:80:04.4;txq13@0000:80:04.5;txq14@0000:80:04.6;txq15@0000:80:04.7;rxq0@0000:00:04.0;rxq1@0000:00:04.1;rxq2@0000:00:04.2;rxq3@0000:00:04.3;rxq4@0000:00:04.4;rxq5@0000:00:04.5;rxq6@0000:00:04.6;rxq7@0000:00:04.7;rxq8@0000:80:04.0;rxq9@0000:80:04.1;rxq10@0000:80:04.2;rxq11@0000:80:04.3;rxq12@0000:80:04.4;rxq13@0000:80:04.5;rxq14@0000:80:04.6;rxq15@0000:80:04.7]' \
	--iova=va -- -i --nb-cores=8 --txd=1024 --rxd=1024 --txq=16 --rxq=16
	testpmd>set fwd csum
	testpmd>csum mac-swap off 0
	testpmd>csum mac-swap off 1
	testpmd>stop
	testpmd>port stop all
	testpmd>port config 0 tx_offload tcp_cksum on
	testpmd>port config 1 tx_offload tcp_cksum on
	testpmd>port start all
	testpmd>start

3. Launch VM1 and VM2 using qemu::

	taskset -c 32 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=off,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 40 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=off,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 16
	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 16
	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	Under VM1, run: `scp <xxx> root@1.1.1.8:/`   <xxx> is the file name

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

Test Case 5: VM2VM virtio-net packed ring CBDMA enable test with tcp traffic
----------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net packed ring mergeable path
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 2 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --file-prefix=vhost -a 0000:00:04.0 -a 0000:00:04.1 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[txq0@0000:00:04.0;rxq0@0000:00:04.0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[txq0@0000:00:04.1;rxq0@0000:00:04.1]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --txq=1 --rxq=1
	testpmd>start

3. Launch VM1 and VM2 on socket 1 with qemu::

	taskset -c 32 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,\
	csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

	taskset -c 33 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,\
	csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

7. Check 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1518, Port 1 should have rx packets above 1518::

	testpmd>show port xstats all

Test Case 6: VM2VM virtio-net packed ring mergeable 8 queues CBDMA enable test with large packet payload valid check
--------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net packed ring mergeable path and 8 queues when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.1;txq3@0000:00:04.1;txq4@0000:00:04.2;txq5@0000:00:04.2;txq6@0000:00:04.3;txq7@0000:00:04.3;rxq0@0000:00:04.4;rxq1@0000:00:04.4;rxq2@0000:00:04.5;rxq3@0000:00:04.5;rxq4@0000:00:04.6;rxq5@0000:00:04.6;rxq6@0000:00:04.7;rxq7@0000:00:04.7]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.1;txq3@0000:00:04.1;txq4@0000:00:04.2;txq5@0000:00:04.2;txq6@0000:00:04.3;txq7@0000:00:04.3;rxq0@0000:00:04.4;rxq1@0000:00:04.4;rxq2@0000:00:04.5;rxq3@0000:00:04.5;rxq4@0000:00:04.6;rxq5@0000:00:04.6;rxq6@0000:00:04.7;rxq7@0000:00:04.7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	taskset -c 32 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	taskset -c 40 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

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

8. Rerun step 6-7 five times.

Test Case 7: VM2VM virtio-net packed ring non-mergeable 8 queues CBDMA enable test with large packet payload valid check
------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net packed ring non-mergeable path and 8 queues when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.1;txq3@0000:00:04.1;txq4@0000:00:04.2;txq5@0000:00:04.2;rxq2@0000:00:04.3;rxq3@0000:00:04.3;rxq4@0000:00:04.4;rxq5@0000:00:04.4;rxq6@0000:00:04.5;rxq7@0000:00:04.5],dma-ring-size=1024' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=[txq2@0000:80:04.0;txq3@0000:80:04.0;txq4@0000:80:04.1;txq5@0000:80:04.1;txq6@0000:80:04.2;txq7@0000:80:04.2;rxq0@0000:80:04.3;rxq1@0000:80:04.3;rxq2@0000:80:04.4;rxq3@0000:80:04.4;rxq4@0000:80:04.5;rxq5@0000:80:04.5],dma-ring-size=1024' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>start

3. Launch VM1 and VM2::

	taskset -c 32 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	taskset -c 40 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

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

8. Rerun step 6-7 five times.

Test Case 8: VM2VM virtio-net packed ring mergeable 16 queues CBDMA enabled test with Rx/Tx csum in SW
------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net packed ring mergeable path and 16 queues when vhost uses the asynchronous operations with CBDMA channels
and perform SW checksum in Rx/Tx path.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-9 -n 4 --file-prefix=vhost \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=16,tso=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.1;txq3@0000:00:04.1;txq4@0000:00:04.2;txq5@0000:00:04.2;txq6@0000:00:04.3;txq7@0000:00:04.3;txq8@0000:00:04.4;txq9@0000:00:04.4;txq10@0000:00:04.5;txq11@0000:00:04.5;txq12@0000:00:04.6;txq13@0000:00:04.6;txq14@0000:00:04.7;txq15@0000:00:04.7;rxq0@0000:80:04.0;rxq1@0000:80:04.0;rxq2@0000:80:04.1;rxq3@0000:80:04.1;rxq4@0000:80:04.2;rxq5@0000:80:04.2;rxq6@0000:80:04.3;rxq7@0000:80:04.3;rxq8@0000:80:04.4;rxq9@0000:80:04.4;rxq10@0000:80:04.5;rxq11@0000:80:04.5;rxq12@0000:80:04.6;rxq13@0000:80:04.6;rxq14@0000:80:04.7;rxq15@0000:80:04.7]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=16,tso=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1;txq2@0000:00:04.2;txq3@0000:00:04.3;txq4@0000:00:04.4;txq5@0000:00:04.5;txq6@0000:00:04.6;txq7@0000:00:04.7;txq8@0000:80:04.0;txq9@0000:80:04.1;txq10@0000:80:04.2;txq11@0000:80:04.3;txq12@0000:80:04.4;txq13@0000:80:04.5;txq14@0000:80:04.6;txq15@0000:80:04.7;rxq0@0000:00:04.0;rxq1@0000:00:04.1;rxq2@0000:00:04.2;rxq3@0000:00:04.3;rxq4@0000:00:04.4;rxq5@0000:00:04.5;rxq6@0000:00:04.6;rxq7@0000:00:04.7;rxq8@0000:80:04.0;rxq9@0000:80:04.1;rxq10@0000:80:04.2;rxq11@0000:80:04.3;rxq12@0000:80:04.4;rxq13@0000:80:04.5;rxq14@0000:80:04.6;rxq15@0000:80:04.7]' \
	--iova=va -- -i --nb-cores=8 --txd=1024 --rxd=1024 --txq=16 --rxq=16
	testpmd>set fwd csum
	testpmd>csum mac-swap off 0
	testpmd>csum mac-swap off 1
	testpmd>stop
	testpmd>port stop all
	testpmd>port config 0 tx_offload tcp_cksum on
	testpmd>port config 1 tx_offload tcp_cksum on
	testpmd>port start all
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	taskset -c 32 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,\
	mq=on,vectors=40,csum=on,guest_csum=off,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	taskset -c 40 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,\
	mq=on,vectors=40,csum=on,guest_csum=off,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 16
	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 16
	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	Under VM1, run: `scp <xxx> root@1.1.1.8:/`   <xxx> is the file name

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

8. Rerun step 6-7 five times.

Test Case 9: VM2VM virtio-net packed ring CBDMA enable test dma-ring-size with tcp traffic
------------------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net packed ring mergeable path
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue operations with CBDMA channels
and the dma ring size is small.

1. Bind 2 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --file-prefix=vhost \
	-a 0000:00:04.0 -a 0000:00:04.1 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[txq0@0000:00:04.0;rxq0@0000:00:04.0],dma-ring-size=256' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[txq0@0000:00:04.1;rxq0@0000:00:04.1],dma-ring-size=256' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --txq=1 --rxq=1
	testpmd>start

3. Launch VM1 and VM2 on socket 1 with qemu::

	taskset -c 32 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,\
	csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

	taskset -c 33 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,\
	csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	Under VM1, run: `scp <xxx> root@1.1.1.8:/`   <xxx> is the file name

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

8. Rerun step 6-7 five times.

Test Case 10: VM2VM virtio-net packed ring 8 queues CBDMA enable test with legacy mode
--------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net packed ring mergeable path and 8 queues  with legacy mode when vhost uses the asynchronous operations with CBDMA channels.

1. Bind 16 CBDMA channels to vfio-pci, as common step 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	-a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,legacy-ol-flags=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.1;txq3@0000:00:04.1;txq4@0000:00:04.2;txq5@0000:00:04.2;rxq2@0000:00:04.3;rxq3@0000:00:04.3;rxq4@0000:00:04.4;rxq5@0000:00:04.4;rxq6@0000:00:04.5;rxq7@0000:00:04.5]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,legacy-ol-flags=1,dmas=[txq2@0000:80:04.0;txq3@0000:80:04.0;txq4@0000:80:04.1;txq5@0000:80:04.1;txq6@0000:80:04.2;txq7@0000:80:04.2;rxq0@0000:80:04.3;rxq1@0000:80:04.3;rxq2@0000:80:04.4;rxq3@0000:80:04.4;rxq4@0000:80:04.5;rxq5@0000:80:04.5]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	taskset -c 32 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	taskset -c 40 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,\
	mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

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

8. Rerun step 6-7 five times.
