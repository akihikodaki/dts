.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=====================================================
VM2VM vhost-user/virtio-net with DSA driver test plan
=====================================================

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
DSA driver (kernel IDXD driver and DPDK vfio-pci driver) in VM2VM virtio-net topology.
1. Check Vhost tx offload function by verifing the TSO/cksum in the TCP/IP stack with vm2vm split ring and packed ring 
vhost-user/virtio-net mergeable path.
2.Check the payload of large packet (larger than 1MB) is valid after forwarding packets with vm2vm split ring
and packed ring vhost-user/virtio-net mergeable and non-mergeable path.
3. Multi-queues number dynamic change in vm2vm vhost-user/virtio-net with split ring and packed ring.

IOMMU impact:
If iommu off, idxd can work with iova=pa
If iommu on, kernel dsa driver only can work with iova=va by program IOMMU, can't use iova=pa(fwd not work due to pkts payload wrong).

Note:
1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > 5.1, and packed ring multi-queues not support reconnect in qemu yet.
2.For split virtqueue virtio-net with multi-queues server mode test, better to use qemu version >= 5.2.0, dut to qemu(v4.2.0~v5.1.0) exist split ring multi-queues reconnection issue.
3.When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may
exceed IOMMU's max capability, better to use 1G guest hugepage.
4.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.


Prerequisites
=============

Topology
--------
	Test flow: Virtio-net <-> Vhost-user <-> Testpmd <-> Vhost-user <-> Virtio-net

Software
--------
	iperf
	qemu: https://download.qemu.org/qemu-6.2.0.tar.xz

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
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q <numWq>

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

Test Case 1: VM2VM vhost-user/virtio-net split ring test TSO with dsa dpdk driver
---------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net split ring mergeable path 
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0

2. Launch the Vhost testpmd by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:e7:01.0,max_queues=2 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[txq0@0000:e7:01.0-q0;rxq0@0000:e7:01.0-q0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[txq0@0000:e7:01.0-q1;rxq0@0000:e7:01.0-q1]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	testpmd>start

3. Launch VM1 and VM2 with split ring mergeable path and tso on::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

7. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1519, Port 1 should have rx packets above 1519::

	testpmd>show port xstats all

Test Case 2: VM2VM vhost-user/virtio-net split ring mergeable path 8 queues test with large packet payload with dsa dpdk driver
-------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net split ring mergeable path when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.
The dynamic change of multi-queues number, iova as VA and PA mode also test.

1. Bind 4 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 f6:01.0

2. Launch the Vhost testpmd by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,tso=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q1;txq3@0000:f1:01.0-q1;txq4@0000:f1:01.0-q2;txq5@0000:f1:01.0-q2;txq6@0000:f1:01.0-q3;txq7@0000:f1:01.0-q3;rxq0@0000:f1:01.0-q0;rxq1@0000:f1:01.0-q0;rxq2@0000:f1:01.0-q1;rxq3@0000:f1:01.0-q1;rxq4@0000:f1:01.0-q2;rxq5@0000:f1:01.0-q2;rxq6@0000:f1:01.0-q3;rxq7@0000:f1:01.0-q3]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,client=1,tso=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q1;txq3@0000:f1:01.0-q1;txq4@0000:f1:01.0-q2;txq5@0000:f1:01.0-q2;txq6@0000:f1:01.0-q3;txq7@0000:f1:01.0-q3;rxq0@0000:f1:01.0-q0;rxq1@0000:f1:01.0-q0;rxq2@0000:f1:01.0-q1;rxq3@0000:f1:01.0-q1;rxq4@0000:f1:01.0-q2;rxq5@0000:f1:01.0-q2;rxq6@0000:f1:01.0-q3;rxq7@0000:f1:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

3. Launch VM1 and VM2 using qemu 7.0.0::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 8
	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 8
	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Quit and relaunch vhost w/ diff dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=8  -a 0000: :01.0,max_queues=8 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,legacy-ol-flags=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q0;txq3@0000:f1:01.0-q0;txq4@0000:f1:01.0-q1;txq5@0000:f1:01.0-q2;rxq2@0000:f1:01.0-q3;rxq3@0000:f1:01.0-q4;rxq4@0000:f1:01.0-q5;rxq5@0000:f1:01.0-q5;rxq6@0000:f1:01.0-q5;rxq7@0000:f1:01.0-q5]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,legacy-ol-flags=1,dmas=[txq0@0000:f6:01.0-q0;txq1@0000:f6:01.0-q0;txq2@0000:f6:01.0-q0;txq3@0000:f6:01.0-q0;txq4@0000:f6:01.0-q1;txq5@0000:f6:01.0-q2;rxq2@0000:f6:01.0-q3;rxq3@0000:f6:01.0-q4;rxq4@0000:f6:01.0-q5;rxq5@0000:f6:01.0-q5;rxq6@0000:f6:01.0-q5;rxq7@0000:f6:01.0-q5]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

9. Rerun step 6-7.

10. Quit and relaunch vhost w/ iova=pa::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q0;txq3@0000:f1:01.0-q0;txq4@0000:f1:01.0-q0;txq5@0000:f1:01.0-q0;rxq2@0000:f1:01.0-q1;rxq3@0000:f1:01.0-q1;rxq4@0000:f1:01.0-q1;rxq5@0000:f1:01.0-q1;rxq6@0000:f1:01.0-q1;rxq7@0000:f1:01.0-q1]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,dmas=[txq0@0000:f1:01.0-q2;txq1@0000:f1:01.0-q2;txq2@0000:f1:01.0-q2;txq3@0000:f1:01.0-q2;txq4@0000:f1:01.0-q2;txq5@0000:f1:01.0-q2;rxq2@0000:f1:01.0-q3;rxq3@0000:f1:01.0-q3;rxq4@0000:f1:01.0-q3;rxq5@0000:f1:01.0-q3;rxq6@0000:f1:01.0-q3;rxq7@0000:f1:01.0-q3]' \
	--iova=pa -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

11. Rerun step 6-7.

12. Quit vhost ports and relaunch vhost ports w/o dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --no-pci --vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4
	testpmd>start

13. On VM1, set virtio device::

	<VM1># ethtool -L ens5 combined 4

14. On VM2, set virtio device::

	<VM2># ethtool -L ens5 combined 4

15. Rerun step 6-7.

16. Quit vhost ports and relaunch vhost ports with 1 queues::

	 <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --no-pci --vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=4' \
	 --vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=4'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	 testpmd>start

17. On VM1, set virtio device::

	ethtool -L ens5 combined 1

18. On VM2, set virtio device::

	ethtool -L ens5 combined 1

19. Rerun step 6-7.

Test Case 3: VM2VM vhost-user/virtio-net split ring non-mergeable path 8 queues test with large packet payload with dsa dpdk driver
-----------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net split ring non-mergeable path when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.
The dynamic change of multi-queues number also test.

1. Bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci e7:01.0 ec:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=8 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q0;txq3@0000:f1:01.0-q0;txq4@0000:f1:01.0-q1;txq5@0000:f1:01.0-q1;txq6@0000:f1:01.0-q1;txq7@0000:f1:01.0-q1;rxq0@0000:f1:01.0-q2;rxq1@0000:f1:01.0-q2;rxq2@0000:f1:01.0-q2;rxq3@0000:f1:01.0-q2;rxq4@0000:f1:01.0-q3;rxq5@0000:f1:01.0-q3;rxq6@0000:f1:01.0-q3;rxq7@0000:f1:01.0-q3]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@0000:f1:01.0-q4;txq1@0000:f1:01.0-q4;txq2@0000:f1:01.0-q4;txq3@0000:f1:01.0-q4;txq4@0000:f1:01.0-q5;txq5@0000:f1:01.0-q5;txq6@0000:f1:01.0-q5;txq7@0000:f1:01.0-q5;rxq0@0000:f1:01.0-q6;rxq1@0000:f1:01.0-q6;rxq2@0000:f1:01.0-q6;rxq3@0000:f1:01.0-q6;rxq4@0000:f1:01.0-q7;rxq5@0000:f1:01.0-q7;rxq6@0000:f1:01.0-q7;rxq7@0000:f1:01.0-q7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

3. Launch VM1 and VM2::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Quit vhost ports and relaunch vhost ports w/o dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --no-pci --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

9. Rerun step 6-7.

10. Quit vhost ports and relaunch vhost ports with 1 queues::

	 <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --no-pci --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8' \
	 --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	 testpmd>start

11. On VM1, set virtio device::

	<VM1># ethtool -L ens5 combined 1

12. On VM2, set virtio device::

	<VM2># ethtool -L ens5 combined 1

13. Rerun step 6-7.

Test Case 4: VM2VM vhost-user/virtio-net packed ring test TSO with dsa dpdk driver
----------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net packed ring mergeable path 
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 f6:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=2 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[txq0@0000:f1:01.0-q0;rxq0@0000:f1:01.0-q1]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[txq0@0000:f1:01.0-q0;rxq0@0000:f1:01.0-q1]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

7. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1519, Port 1 should have rx packets above 1519::

	testpmd>show port xstats all

Test Case 5: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with large packet payload with dsa dpdk driver
--------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net packed ring mergeable path when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.
The dynamic change of multi-queues number also test.

1. Bind 2 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 f6:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=4 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q1;txq3@0000:f1:01.0-q1;txq4@0000:f1:01.0-q2;txq5@0000:f1:01.0-q2;txq6@0000:f1:01.0-q3;txq7@0000:f1:01.0-q3;rxq0@0000:f1:01.0-q0;rxq1@0000:f1:01.0-q0;rxq2@0000:f1:01.0-q1;rxq3@0000:f1:01.0-q1;rxq4@0000:f1:01.0-q2;rxq5@0000:f1:01.0-q2;rxq6@0000:f1:01.0-q3;rxq7@0000:f1:01.0-q3]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q1;txq3@0000:f1:01.0-q1;txq4@0000:f1:01.0-q2;txq5@0000:f1:01.0-q2;txq6@0000:f1:01.0-q3;txq7@0000:f1:01.0-q3;rxq0@0000:f1:01.0-q0;rxq1@0000:f1:01.0-q0;rxq2@0000:f1:01.0-q1;rxq3@0000:f1:01.0-q1;rxq4@0000:f1:01.0-q2;rxq5@0000:f1:01.0-q2;rxq6@0000:f1:01.0-q3;rxq7@0000:f1:01.0-q3]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1>: scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.

Test Case 6: VM2VM vhost-user/virtio-net packed ring non-mergeable path 8 queues test with large packet payload with dsa dpdk driver
------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net packed ring non-mergeable path when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.
The dynamic change of multi-queues number also test.

1. Bind 1 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=8 -a 0000:f6:01.0,max_queues=8 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q1;txq2@0000:f1:01.0-q2;txq3@0000:f1:01.0-q3;txq4@0000:f1:01.0-q4;txq5@0000:f1:01.0-q5;rxq2@0000:f1:01.0-q6;rxq3@0000:f1:01.0-q6;rxq4@0000:f1:01.0-q7;rxq5@0000:f1:01.0-q7;rxq6@0000:f1:01.0-q7;rxq7@0000:f1:01.0-q7]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=[txq2@0000:f6:01.0-q0;txq3@0000:f6:01.0-q1;txq4@0000:f6:01.0-q2;txq5@0000:f6:01.0-q3;txq6@0000:f6:01.0-q4;txq7@0000:f6:01.0-q5;rxq0@0000:f6:01.0-q6;rxq1@0000:f6:01.0-q6;rxq2@0000:f6:01.0-q7;rxq3@0000:f6:01.0-q7;rxq4@0000:f6:01.0-q7;rxq5@0000:f6:01.0-q7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=off,guest_tso4=off,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=off,guest_tso4=off,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.

Test Case 7: VM2VM vhost-user/virtio-net packed ring test dma-ring-size with tcp traffic and dsa dpdk driver
------------------------------------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net packed ring mergeable path 
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver
and the dma ring size is small.

1. Bind 2  dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 f6:01.0

2. Launch the Vhost sample with PA mode by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=2 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[txq0@0000:f1:01.0-q0;rxq0@0000:f1:01.0-q0],dma-ring-size=32' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[txq0@0000:f1:01.0-q1;rxq0@0000:f1:01.0-q1],dma-ring-size=32' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

7. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1522, Port 1 should have rx packets above 1522::

	testpmd>show port xstats all

Test Case 8: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with legacy mode with dsa dpdk driver
-----------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net packed ring mergeable path with legacy mode when vhost uses the asynchronous enqueue and dequeue operations with dsa dpdk driver.

1. Bind 1 dsa device to vfio-pci like common step 1::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,legacy-ol-flags=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q0;txq3@0000:f1:01.0-q0;txq4@0000:f1:01.0-q1;txq5@0000:f1:01.0-q1;txq6@0000:f1:01.0-q1;txq7@0000:f1:01.0-q1;rxq0@0000:f1:01.0-q0;rxq1@0000:f1:01.0-q0;rxq2@0000:f1:01.0-q0;rxq3@0000:f1:01.0-q0;rxq4@0000:f1:01.0-q1;rxq5@0000:f1:01.0-q1;rxq6@0000:f1:01.0-q1;rxq7@0000:f1:01.0-q1]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,legacy-ol-flags=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q0;txq3@0000:f1:01.0-q0;txq4@0000:f1:01.0-q1;txq5@0000:f1:01.0-q1;txq6@0000:f1:01.0-q1;txq7@0000:f1:01.0-q1;rxq0@0000:f1:01.0-q0;rxq1@0000:f1:01.0-q0;rxq2@0000:f1:01.0-q0;rxq3@0000:f1:01.0-q0;rxq4@0000:f1:01.0-q1;rxq5@0000:f1:01.0-q1;rxq6@0000:f1:01.0-q1;rxq7@0000:f1:01.0-q1]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
    testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.

Test Case 9: VM2VM vhost-user/virtio-net split ring test TSO with dsa kernel driver
-----------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net split ring mergeable path 
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous operations with dsa kernel driver.

1. Bind 1 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[txq0@wq0.0;rxq0@wq0.0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[txq0@wq0.0;rxq0@wq0.0]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	testpmd>start

3. Launch VM1 and VM2 on socket 1::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM3># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

7. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1519, Port 1 should have rx packets above 1519::

	testpmd>show port xstats all

Test Case 10: VM2VM vhost-user/virtio-net split ring mergeable path 8 queues test with large packet payload with dsa kernel driver
----------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net split ring mergeable path when vhost uses the asynchronous enqueue and dequeue operations with dsa kernel driver.
The dynamic change of multi-queues number also test.

1. Bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;txq6@wq0.6;txq7@wq0.7;rxq0@wq1.0;rxq1@wq1.1;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,dmas=[txq0@wq1.0;txq1@wq1.1;txq2@wq1.2;txq3@wq1.3;txq4@wq1.4;txq5@wq1.5;txq6@wq1.6;txq7@wq1.7;rxq0@wq0.0;rxq1@wq0.1;rxq2@wq0.2;rxq3@wq0.3;rxq4@wq0.4;rxq5@wq0.5;rxq6@wq0.6;rxq7@wq0.7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

3. Launch VM1 and VM2 using qemu::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Quit and relaunch vhost w/ diff dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq0.1;rxq3@wq0.1;rxq4@wq0.2;rxq5@wq0.2;rxq6@wq0.2;rxq7@wq0.2]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,dmas=[txq0@wq0.3;txq1@wq0.3;txq2@wq0.3;txq3@wq0.3;txq4@wq0.4;txq5@wq0.4;rxq2@wq0.4;rxq3@wq0.4;rxq4@wq0.5;rxq5@wq0.5;rxq6@wq0.5;rxq7@wq0.5]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

9. Rerun step 6-7.

10. Quit vhost ports and relaunch vhost ports w/o dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4
	testpmd>start

11. On VM1, set virtio device::

	ethtool -L ens5 combined 4

12. On VM2, set virtio device::

	ethtool -L ens5 combined 4

13. Rerun step 6-7.

14. Quit vhost ports and relaunch vhost ports with 1 queues::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=4' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=4'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	testpmd>start

15. On VM1, set virtio device::

	ethtool -L ens5 combined 1

16. On VM2, set virtio device::

	ethtool -L ens5 combined 1

17. Rerun step 6-7.

Test Case 11: VM2VM vhost-user/virtio-net split ring non-mergeable path 8 queues test with large packet payload with dsa kernel driver
--------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net split ring non-mergeable path when vhost uses the asynchronous enqueue and dequeue operations with dsa kernel driver.
The dynamic change of multi-queues number also test.

1. Bind 1 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 2
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.0;txq3@wq0.0;txq4@wq0.1;txq5@wq0.1;rxq2@wq0.1;rxq3@wq0.1;rxq4@wq0.2;rxq5@wq0.2;rxq6@wq0.2;rxq7@wq0.2]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@wq1.0;txq1@wq1.0;txq2@wq1.0;txq3@wq1.0;txq4@wq1.1;txq5@wq1.1;rxq2@wq1.1;rxq3@wq1.1;rxq4@wq1.2;rxq5@wq1.2;rxq6@wq1.2;rxq7@wq1.2]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

3. Launch VM1 and VM2::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=off,guest_tso4=off,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=off,guest_tso4=off,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Quit vhost ports and relaunch vhost ports w/o dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,legacy-ol-flags=1' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,legacy-ol-flags=1'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

9. Rerun step 6-7.

10. Quit vhost ports and relaunch vhost ports with 1 queues::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	testpmd>start

11. On VM1, set virtio device::

	<VM1># ethtool -L ens5 combined 1

12. On VM2, set virtio device::

	<VM2># ethtool -L ens5 combined 1

13. Rerun step 6-7.

Test Case 12: VM2VM vhost-user/virtio-net packed ring test TSO with dsa kernel driver
-------------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net packed ring mergeable path
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue and dequeue operations with dsa kernel driver.

1. Bind 1 dsa device to idxd::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[txq0@wq0.0;rxq0@wq0.0]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[txq0@wq0.0;rxq0@wq0.0]' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

7. Check that 2VMs can receive and send big packets to each other through vhost log. Port 0 should have tx packets above 1522, Port 1 should have rx packets above 1522::

	testpmd>show port xstats all

Test Case 13: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with large packet payload with dsa kernel driver
-----------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net packed ring mergeable path when vhost uses the asynchronous enqueue and dequeue operations with dsa kernel driver.

1. Bind 2 dsa device to idxd like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=[txq0@wq0.0;txq1@wq0.1;txq2@wq0.2;txq3@wq0.3;txq4@wq0.4;txq5@wq0.5;rxq2@wq0.2;rxq3@wq0.3;rxq4@wq0.4;rxq5@wq0.5;rxq6@wq0.6;rxq7@wq0.7]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=[txq0@wq1.0;txq1@wq1.1;txq2@wq1.2;txq3@wq1.3;txq4@wq1.4;txq5@wq1.5;rxq2@wq1.2;rxq3@wq1.3;rxq4@wq1.4;rxq5@wq1.5;rxq6@wq1.6;rxq7@wq1.7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.

Test Case 14: VM2VM vhost-user/virtio-net packed ring non-mergeable path 8 queues test with large packet payload with dsa kernel driver
---------------------------------------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net packed ring mergeable path when vhost uses the asynchronous enqueue and dequeue operations with dsa kernel driver.
The dynamic change of multi-queues number also test.

1. Bind 2 dsa device to vfio-pci like common step 2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 1
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.1;txq3@wq0.1;txq4@wq0.2;txq5@wq0.2;txq6@wq0.3;txq7@wq0.3;rxq0@wq0.0;rxq1@wq0.0;rxq2@wq0.1;rxq3@wq0.1;rxq4@wq0.2;rxq5@wq0.2;rxq6@wq0.3;rxq7@wq0.3]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=[txq0@wq0.0;txq1@wq0.0;txq2@wq0.1;txq3@wq0.1;txq4@wq0.2;txq5@wq0.2;txq6@wq0.3;txq7@wq0.3;rxq0@wq0.0;rxq1@wq0.0;rxq2@wq0.1;rxq3@wq0.1;rxq4@wq0.2;rxq5@wq0.2;rxq6@wq0.3;rxq7@wq0.3]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 8
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 8
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.

Test Case 15: VM2VM vhost-user/virtio-net split ring non-mergeable 16 queues test with Rx/Tx csum in SW
-------------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net split ring non-mergeable path when vhost uses the asynchronous operations with dsa dpdk
and kernel driver and perform SW checksum in Rx/Tx path.. The dynamic change of multi-queues number also test.

1. Bind 2 dsa device to vfio-pci and 2 dsa device to idxd like common step 1-2::

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

	<dpdk dir># ./usertools/dpdk-devbind.py -u 0000:e7:01.0 0000:ec:01.0 
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:f1:01.0 0000:f6:01.0

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0 -a 0000:f6:01.0  \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16,tso=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q0;txq3@0000:f1:01.0-q0;txq4@0000:f1:01.0-q0;txq5@0000:f1:01.0-q0;txq6@0000:f1:01.0-q0;txq7@0000:f1:01.0-q0;txq8@0000:f1:01.0-q0;txq9@0000:f1:01.0-q0;txq10@0000:f1:01.0-q0;txq11@0000:f1:01.0-q0;txq12@0000:f1:01.0-q0;txq13@0000:f1:01.0-q0;txq14@0000:f1:01.0-q0;txq15@0000:f1:01.0-q0;rxq0@wq0.0;rxq1@wq0.0;rxq2@wq0.0;rxq3@wq0.0;rxq4@wq0.0;rxq5@wq0.0;rxq6@wq0.0;rxq7@wq0.0;rxq8@wq0.0;rxq9@wq0.0;rxq10@wq0.0;rxq11@wq0.0;rxq12@wq0.0;rxq13@wq0.0;rxq14@wq0.0;rxq15@wq0.0]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16,tso=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q1;txq2@0000:f1:01.0-q2;txq3@0000:f1:01.0-q3;txq4@0000:f1:01.0-q4;txq5@0000:f1:01.0-q5;txq6@0000:f1:01.0-q6;txq7@0000:f1:01.0-q7;txq8@0000:f6:01.0-q0;txq9@0000:f6:01.0-q1;txq10@0000:f6:01.0-q2;txq11@0000:f6:01.0-q3;txq12@0000:f6:01.0-q4;txq13@0000:f6:01.0-q5;txq14@0000:f6:01.0-q6;txq15@0000:f6:01.0-q7;rxq0@wq0.0;rxq1@wq0.1;rxq2@wq0.2;rxq3@wq0.3;rxq4@wq0.4;rxq5@wq0.5;rxq6@wq0.6;rxq7@wq0.7;rxq8@wq1.0;rxq9@wq1.1;rxq10@wq1.2;rxq11@wq1.3;rxq12@wq1.4;rxq13@wq1.5;rxq14@wq1.6;rxq15@wq1.7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16
	testpmd>set fwd csum
	testpmd>stop
	testpmd>port stop all
	testpmd>port config 0 tx_offload tcp_cksum on
	testpmd>port config 1 tx_offload tcp_cksum on
	testpmd>port start all
	testpmd>start

3. Launch VM1 and VM2::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=off,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=off,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	<VM1># ethtool -L ens5 combined 16
	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	<VM2># ethtool -L ens5 combined 16
	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Quit vhost ports and relaunch vhost ports w/ diff dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=8 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16,tso=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q0;txq3@0000:f1:01.0-q0;txq4@0000:f1:01.0-q2;txq5@0000:f1:01.0-q3;rxq2@0000:f1:01.0-q4;rxq3@0000:f1:01.0-q5;rxq4@0000:f1:01.0-q6;rxq5@0000:f1:01.0-q6;rxq6@0000:f1:01.0-q6;rxq7@0000:f1:01.0-q6]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16,tso=1,dmas=[txq12@wq1.0;txq13@wq1.0;txq14@wq1.0;txq15@wq1.0;rxq12@wq1.1;rxq13@wq1.1;rxq14@wq1.1;rxq15@wq1.1]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16
	testpmd>set fwd csum
	testpmd>start

9. rerun step 6-7.

10. Quit vhost ports and relaunch vhost ports w/o dsa channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=16' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=16'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16
	testpmd>set fwd csum
	testpmd>start

11. Rerun step 6-7.

12. Quit vhost ports and relaunch vhost ports with 1 queues::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	testpmd>set fwd csum
	testpmd>start

13. On VM1, set virtio device::

	<VM1># ethtool -L ens5 combined 1

14. On VM2, set virtio device::

	<VM2># ethtool -L ens5 combined 1

15. Rerun step 6-7.

Test Case 16: VM2VM vhost-user/virtio-net packed ring mergeable 16 queues test with Rx/Tx csum in SW
----------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net packed ring mergeable path when vhost uses the asynchronous operations with dsa dpdk
and kernel driver and perform SW checksum in Rx/Tx path.. The dynamic change of multi-queues number also test.

1. Bind 2 dsa device to vfio-pci and 2 dsa device to idxd like common step 1-2::

	ls /dev/dsa #check wq configure, reset if exist

	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0 
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0 
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci f1:01.0 f6:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 1
	ls /dev/dsa #check wq configure success

2. Launch the Vhost sample by below commands::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost -a 0000:f1:01.0,max_queues=1 -a 0000:f6:01.0,max_queues=1 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16,tso=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q0;txq2@0000:f1:01.0-q0;txq3@0000:f1:01.0-q0;txq4@0000:f1:01.0-q0;txq5@0000:f1:01.0-q0;txq6@0000:f1:01.0-q0;txq7@0000:f1:01.0-q0;txq8@0000:f1:01.0-q0;txq9@0000:f1:01.0-q0;txq10@0000:f1:01.0-q0;txq11@0000:f1:01.0-q0;txq12@0000:f1:01.0-q0;txq13@0000:f1:01.0-q0;txq14@0000:f1:01.0-q0;txq15@0000:f1:01.0-q0;rxq0@wq0.0;rxq1@wq0.0;rxq2@wq0.0;rxq3@wq0.0;rxq4@wq0.0;rxq5@wq0.0;rxq6@wq0.0;rxq7@wq0.0;rxq8@wq0.0;rxq9@wq0.0;rxq10@wq0.0;rxq11@wq0.0;rxq12@wq0.0;rxq13@wq0.0;rxq14@wq0.0;rxq15@wq0.0]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16,tso=1,dmas=[txq0@0000:f1:01.0-q0;txq1@0000:f1:01.0-q1;txq2@0000:f1:01.0-q2;txq3@0000:f1:01.0-q3;txq4@0000:f1:01.0-q4;txq5@0000:f1:01.0-q5;txq6@0000:f1:01.0-q6;txq7@0000:f1:01.0-q7;txq8@0000:f6:01.0-q0;txq9@0000:f6:01.0-q1;txq10@0000:f6:01.0-q2;txq11@0000:f6:01.0-q3;txq12@0000:f6:01.0-q4;txq13@0000:f6:01.0-q5;txq14@0000:f6:01.0-q6;txq15@0000:f6:01.0-q7;rxq0@wq0.0;rxq1@wq0.1;rxq2@wq0.2;rxq3@wq0.3;rxq4@wq0.4;rxq5@wq0.5;rxq6@wq0.6;rxq7@wq0.7;rxq8@wq1.0;rxq9@wq1.1;rxq10@wq1.2;rxq11@wq1.3;rxq12@wq1.4;rxq13@wq1.5;rxq14@wq1.6;rxq15@wq1.7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16
	testpmd>set fwd csum
	testpmd>stop
	testpmd>port stop all
	testpmd>port config 0 tx_offload tcp_cksum on
	testpmd>port config 1 tx_offload tcp_cksum on
	testpmd>port start all
	testpmd>start

3. Launch VM1 and VM2 with qemu::

	<dpdk dir># taskset -c 7 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=off,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

	<dpdk dir># taskset -c 8 /usr/local/qemu-7.0.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/xingguang/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=off,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 16
	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 16
	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	<VM1># scp <file> root@1.1.1.8:/

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Rerun step 6-7 five times.
