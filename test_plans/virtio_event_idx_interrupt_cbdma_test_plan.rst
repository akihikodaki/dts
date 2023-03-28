.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

====================================================
Virtio event idx interrupt mode with cbdma test plan
====================================================

Description
===========

This feature is to suppress interrupts for performance improvement, need compare
interrupt times with and without virtio event idx enabled. This test plan test
virtio event idx interrupt with cbdma enable. Also need cover driver reload test.

.. note::

   1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > 5.1, and packed ring multi-queues not support reconnect in qemu yet.
   2.For split virtqueue virtio-net with multi-queues server mode test, need qemu version >= 5.2.0, dut to old qemu exist reconnect issue when multi-queues test.
   3.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

Prerequisites
=============
Topology
--------
Test flow:TG --> NIC --> Vhost-user --> Virtio-net

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

Test Case 1: Split ring virtio-pci driver reload test with CBDMA enable
-----------------------------------------------------------------------
This case tests split ring event idx interrupt mode workable after reload
virtio-pci driver several times when vhost uses the asynchronous
operations with CBDMA channels.

1. Bind one nic port and one cbdma channel to vfio-pci, then launch the vhost sample by below commands::

	rm -rf vhost-net*
	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost,iface=vhost-net,queues=1,dmas=[txq0@0000:00:04.0;rxq0@0000:00:04.0]' \
	-- -i --nb-cores=1 --txd=1024 --rxd=1024
	testpmd> start

2. Launch VM::

	taskset -c 32-33 qemu-system-x86_64 -name vm1 \
	-cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
	-smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu2004.img \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait \
	-device e1000,netdev=nttsip1 -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 \
	-chardev socket,id=char1,path=./vhost-net \
	-netdev type=vhost-user,id=mynet1,chardev=char1,vhostforce \
	-device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on  \
	-vnc :11 -daemonize

3. On VM1, set virtio device IP, send 10M packets from packet generator to nic then check virtio device can receive packets::

	ifconfig [ens3] 1.1.1.2      # [ens3] is the name of virtio-net
	tcpdump -i [ens3]

4. Reload virtio-net driver by below cmds::

	ifconfig [ens3] down
	./usertools/dpdk-devbind.py -u [00:03.0]   # [00:03.0] is the pci addr of virtio-net
	./usertools/dpdk-devbind.py -b virtio-pci [00:03.0]

5. Check virtio device can receive packets again::

	ifconfig [ens3] 1.1.1.2
	tcpdump -i [ens3]

6. Rerun step4 and step5 10 times to check event idx workable after driver reload.

Test Case 2: Split ring 16 queues virtio-net event idx interrupt mode test with cbdma enable
--------------------------------------------------------------------------------------------
This case tests the split ring virtio-net event idx interrupt with 16 queues and when
vhost uses the asynchronous operations with CBDMA channels.

1. Bind one nic port and 4 cbdma channels to vfio-pci, then launch the vhost sample by below commands::

	rm -rf vhost-net*
	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-17 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost,iface=vhost-net,queues=16,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.0;txq3@0000:00:04.0;txq4@0000:00:04.0;txq5@0000:00:04.0;txq6@0000:00:04.0;txq7@0000:00:04.0;txq8@0000:00:04.1;txq9@0000:00:04.1;txq10@0000:00:04.1;txq11@0000:00:04.1;txq12@0000:00:04.1;txq13@0000:00:04.1;txq14@0000:00:04.1;txq15@0000:00:04.1;rxq0@0000:00:04.2;rxq1@0000:00:04.2;rxq2@0000:00:04.2;rxq3@0000:00:04.2;rxq4@0000:00:04.2;rxq5@0000:00:04.2;rxq6@0000:00:04.2;rxq7@0000:00:04.2;rxq8@0000:00:04.3;rxq9@0000:00:04.3;rxq10@0000:00:04.3;rxq11@0000:00:04.3;rxq12@0000:00:04.3;rxq13@0000:00:04.3;rxq14@0000:00:04.3;rxq15@0000:00:04.3]' \
	-- -i --nb-cores=16 --txd=1024 --rxd=1024 --rxq=16 --txq=16
	testpmd> start

2. Launch VM::

	taskset -c 32-33 qemu-system-x86_64 -name us-vhost-vm1 \
	-cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
	-smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu2004.img \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait \
	-device e1000,netdev=nttsip1 -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 \
	-chardev socket,id=char1,path=./vhost-net,server \
	-netdev type=vhost-user,id=mynet1,chardev=char1,vhostforce,queues=16 \
	-device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
	-vnc :11 -daemonize

3. On VM1, give virtio device IP and enable vitio-net with 16 quques::

	ifconfig [ens3] 1.1.1.2           # [ens3] is the name of virtio-net
	ethtool -L [ens3] combined 16

4. Send 10M different IP packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

	cat /proc/interrupts

5. Stop testpmd, check each queue has new packets coming, then start testpmd and check each queue has new packets coming::

	testpmd> stop
	testpmd> start
	testpmd> stop

Test Case 3: Packed ring virtio-pci driver reload test with CBDMA enable
------------------------------------------------------------------------
This case tests packed ring event idx interrupt mode workable after reload
virtio-pci driver several times when uses the asynchronous operations
with CBDMA channels.

1. Bind one nic port and one cbdma channel to vfio-pci, then launch the vhost sample by below commands::

	rm -rf vhost-net*
	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost,iface=vhost-net,queues=1,dmas=[txq0@0000:00:04.0;rxq0@0000:00:04.0]' \
	-- -i --nb-cores=1 --txd=1024 --rxd=1024
	testpmd> start

2. Launch VM::

	taskset -c 32-33 qemu-system-x86_64 -name vm1 \
	-cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
	-smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu2004.img \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait \
	-device e1000,netdev=nttsip1 -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 \
	-chardev socket,id=char1,path=./vhost-net \
	-netdev type=vhost-user,id=mynet1,chardev=char1,vhostforce \
	-device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
	-vnc :11 -daemonize

3. On VM1, set virtio device IP, send 10M packets from packet generator to nic then check virtio device can receive packets::

	ifconfig [ens3] 1.1.1.2      # [ens3] is the name of virtio-net
	tcpdump -i [ens3]

4. Reload virtio-net driver by below cmds::

	ifconfig [ens3] down
	./usertools/dpdk-devbind.py -u [00:03.0]   # [00:03.0] is the pci addr of virtio-net
	./usertools/dpdk-devbind.py -b virtio-pci [00:03.0]

5. Check virtio device can receive packets again::

	ifconfig [ens3] 1.1.1.2
	tcpdump -i [ens3]

6. Rerun step4 and step5 10 times to check event idx workable after driver reload.

Test Case 4: Packed ring 16 queues virtio-net event idx interrupt mode test with cbdma enable
---------------------------------------------------------------------------------------------
This case tests the packed ring virtio-net event idx interrupt with 16 queues and when vhost
uses the asynchronous operations with CBDMA channels.

1. Bind one nic port and 4 cbdma channels to vfio-pci, then launch the vhost sample by below commands::

	rm -rf vhost-net*
	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-17 -n 4 --file-prefix=vhost \
	--vdev 'net_vhost,iface=vhost-net,queues=16,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;txq2@0000:00:04.0;txq3@0000:00:04.0;txq4@0000:00:04.0;txq5@0000:00:04.0;txq6@0000:00:04.0;txq7@0000:00:04.0;txq8@0000:00:04.1;txq9@0000:00:04.1;txq10@0000:00:04.1;txq11@0000:00:04.1;txq12@0000:00:04.1;txq13@0000:00:04.1;txq14@0000:00:04.1;txq15@0000:00:04.1;rxq0@0000:00:04.2;rxq1@0000:00:04.2;rxq2@0000:00:04.2;rxq3@0000:00:04.2;rxq4@0000:00:04.2;rxq5@0000:00:04.2;rxq6@0000:00:04.2;rxq7@0000:00:04.2;rxq8@0000:00:04.3;rxq9@0000:00:04.3;rxq10@0000:00:04.3;rxq11@0000:00:04.3;rxq12@0000:00:04.3;rxq13@0000:00:04.3;rxq14@0000:00:04.3;rxq15@0000:00:04.3]' \
	-- -i --nb-cores=16 --txd=1024 --rxd=1024 --rxq=16 --txq=16
	testpmd> start

2. Launch VM::

	taskset -c 32-33 qemu-system-x86_64 -name vm1 \
	-cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
	-smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu2004.img \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait \
	-device e1000,netdev=nttsip1 -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 \
	-chardev socket,id=char1,path=./vhost-net,server \
	-netdev type=vhost-user,id=mynet1,chardev=char1,vhostforce,queues=16 \
	-device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
	-vnc :11 -daemonize

3. On VM1, configure virtio device IP and enable vitio-net with 16 quques::

	ifconfig [ens3] 1.1.1.2           # [ens3] is the name of virtio-net
	ethtool -L [ens3] combined 16

4. Send 10M different IP packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

	cat /proc/interrupts

5. Stop testpmd, check each queue has new packets coming, then start testpmd and check each queue has new packets coming::

	testpmd> stop
	testpmd> start
	testpmd> stop
