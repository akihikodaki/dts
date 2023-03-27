.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2023 Intel Corporation

========================================================
Vswitch sample test with vhost async data path test plan
========================================================

Description
===========

Vswitch sample can leverage DMA to accelerate vhost async data-path from dpdk 20.11. This plan test
vhost DMA operation callbacks for DSA PMD and vhost async data-path in vhost sample.

--dmas This parameter is used to specify the assigned DMA device of a vhost device. Async vhost-user
net driver will be used if --dmas is set. For example –dmas [txd0@wq0.0,txd1@wq0.1,rxd0@wq0.2,rxd1@wq0.3]
means use DMA channel wq0.0/wq0.2 for vhost device 0 enqueue/dequeue operation and use DMA channel
wq0.1/wq0.3 for vhost device 1 enqueue/dequeue operation. The index of the device corresponds to
the socket file in order, that means vhost device 0 is created through the first socket file,
vhost device 1 is created through the second socket file, and so on.

For more about vswitch example, please refer to the DPDK docment:
http://doc.dpdk.org/guides/sample_app_ug/vhost.html

Prerequisites
=============

Hardware
--------
Supportted NICs: NIC that supports VMDQ

Software
--------
Trex:http://trex-tgn.cisco.com/trex/release/v2.26.tar.gz

General set up
--------------
1. Compile DPDK and vhost example::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
	# meson configure -Dexamples=vhost x86_64-native-linuxapp-gcc
	# ninja -C x86_64-native-linuxapp-gcc -j 110

2. Get the PCI device of DUT, for example, 0000:29:00.0 is NIC port, 0000:6a:01.0 - 0000:f6:01.0 are DSA devices::

	<dpdk dir># ./usertools/dpdk-devbind.py -s
	
	Network devices using kernel driver
	===================================
	0000:29:00.0 'Ethernet Controller E810-C for QSFP 1592' drv=ice unused=vfio-pci
	
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
1. Bind 1 NIC port to vfio-pci::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <nic_pci>
	
	For example:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0

2. Bind DSA devices to DPDK vfio-pci driver::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <dsa_pci>
	
	For example, bind 2 DSA devices to vfio-pci driver:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:6a:01.0 0000:6f:01.0

.. note::

	One DPDK DSA device can create 8 WQ at most. Below is an example, where DPDK DSA device will create one and
	eight WQ for DSA deivce 0000:6a:01.0 and 0000:6f:01.0. The value of “max_queues” is 1~8:
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:6a:01.0,max_queues=1 -- -i
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:6f:01.0,max_queues=8 -- -i

3. Bind DSA devices to kernel idxd driver, and configure Work Queue (WQ)::

	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd <dsa_pci>
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q <wq_num> <dsa_idx>

.. note::

	Better to reset WQ when need operate DSA devices that bound to idxd drvier:
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py --reset <dsa_idx>
	You can check it by 'ls /dev/dsa'
	dsa_idx: Index of DSA devices, where 0<=dsa_idx<=7, corresponding to 0000:6a:01.0 - 0000:f6:01.0
	wq_num: Number of workqueues per DSA endpoint, where 1<=wq_num<=8
	
	For example, bind 2 DSA devices to idxd driver and configure WQ:
	
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
	<dpdk dir># ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 1
	Check WQ by 'ls /dev/dsa' and can find "wq0.0 wq1.0 wq1.1 wq1.2 wq1.3"

Test Case 1: VM2VM virtio-user forwarding test when vhost async operation using DSA dpdk driver
-----------------------------------------------------------------------------------------------
This case tests that the imix packets can forward normally in VM2VM topology(virtio-user as front-end) when vhost async operation using DSA dpdk drvier, both split ring and packed ring have been covered.

1.Bind 1 NIC port and 1 DSA device to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:3a:00.0 -a 0000:6a:01.0,max_queues=4 \
	-- -p 0x1 --mergeable 1 --vm2vm 1  --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,rxd0@0000:6a:01.0-q1,txd1@0000:6a:01.0-q2,rxd1@0000:6a:01.0-q3]  \
	--client --total-num-mbufs 600000

3. Launch virtio-user::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/root/dpdk/vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1
	
	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 31-32 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:11,path=/root/dpdk/vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Loop packets between two virtio-user sides, record performance number with 64b/2000b/8000b/IMIX pkts can get expected::

	testpmd0>set fwd mac
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>set eth-peer 0 00:11:22:33:44:11
	testpmd0>start
	testpmd1>set fwd mac
	testpmd1>set eth-peer 0 00:11:22:33:44:10
	testpmd1>set txpkts 64
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000,2000,2000,2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 64,256,2000,64,256,2000
	testpmd1>start tx_first
	testpmd1>show port stats all

5. Stop dpdk-vhost side and relaunch it with below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:3a:00.0 -a 0000:6a:01.0,max_queues=4 \
	-- -p 0x1 --mergeable 1 --vm2vm 1  --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,rxd1@0000:6a:01.0-q1]  \
	--client --total-num-mbufs 600000

6. Rerun step 4.

Test Case 2: VM2VM virtio-pmd split ring test with DSA dpdk driver register/unregister stable check
---------------------------------------------------------------------------------------------------
This case checks that the split ring with DSA dpdk driver can work stably when the virtio-pmd port is registed and unregisted for many times.

1. Bind 1 NIC port and 1 DSA device to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:3a:00.0 -a 0000:6a:01.0,max_queues=4 \
	-- -p 0x1 --mergeable 1 --vm2vm 1  --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,rxd0@0000:6a:01.0-q1,txd1@0000:6a:01.0-q2,rxd1@0000:6a:01.0-q3] \
	--client --total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
	-daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net0,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :4 -drive file=/home/image/ubuntu2004.img

4. Start VM1 with qemu::

	qemu-system-x86_64  -name vm1 -enable-kvm -pidfile /tmp/.vm1.pid \
	-daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net1,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 -vnc :5 -drive file=/home/image/ubuntu2004_2.img

5. Bind virtio port to vfio-pci in both two VMs::

	modprobe vfio enable_unsafe_noiommu_mode=1
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

6. Start testpmd in VMs seperately::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -- -i --rxq=1 --txq=1 --nb-cores=1 --txd=1024 --rxd=1024

7. Loop pkts between two virtio-user sides, record performance number with 64b/2000b/8000b/IMIX pkts can get expected::

	testpmd0>set fwd mac
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>set eth-peer 0 52:54:00:00:00:02
	testpmd0>start
	testpmd1>set fwd mac
	testpmd1>set eth-peer 0 52:54:00:00:00:01
	testpmd1>set txpkts 64
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000,2000,2000,2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 64,256,2000,64,256,2000
	testpmd1>start tx_first
	testpmd1>show port stats all

8. Quit two testpmd in two VMs, bind virtio-pmd port to virtio-pci,then bind port back to vfio-pci, rerun below cmd 50 times::

	./usertools/dpdk-devbind.py -u 00:05.0
	./usertools/dpdk-devbind.py --bind=virtio-pci 00:05.0
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

9. Rerun step 6-7, check vhost can stable work and get expected throughput.

10. Quit and relaunch dpdk-vhost with below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:3a:00.0 -a 0000:6a:01.0,max_queues=4 -- -p 0x1 --mergeable 1 --vm2vm 1  \
	--socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,rxd1@0000:6a:01.0-q3] \
	--client --total-num-mbufs 600000

11. Rerun step 6-9, check vhost can stable work and get expected throughput.

Test Case 3: VM2VM virtio-pmd packed ring test with DSA dpdk driver register/unregister stable check
----------------------------------------------------------------------------------------------------
This case checks that the packed ring with DSA dpdk driver can work stably when the virtio-pmd port is registed and unregisted for many times.

1. Bind 1 NIC port and 1 DSA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:3a:00.0 -a 0000:6a:01.0,max_queues=4 -a 0000:6f:01.0,max_queues=4 \
	-- -p 0x1 --mergeable 1 --vm2vm 1  --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,rxd0@0000:6a:01.0-q1,txd1@0000:6f:01.0-q2,rxd1@0000:6f:01.0-q3] \
	--client --total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
	-daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net0,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :4 -drive file=/home/image/ubuntu2004.img

4. Start VM1 with qemu::

	qemu-system-x86_64  -name vm1 -enable-kvm -pidfile /tmp/.vm1.pid \
	-daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net1,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 -vnc :5 -drive file=/home/image/ubuntu2004_2.img

5. Bind virtio port to vfio-pci in both two VMs::

	modprobe vfio enable_unsafe_noiommu_mode=1
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

6. Start testpmd in VMs seperately::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -- -i --rxq=1 --txq=1 --nb-cores=1 --txd=1024 --rxd=1024

7. Loop packets between two virtio-user sides, record performance number with 64b/2000b/8000b/IMIX pkts can get expected::

	testpmd0>set fwd mac
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>set eth-peer 0 52:54:00:00:00:02
	testpmd0>start
	testpmd1>set fwd mac
	testpmd1>set eth-peer 0 52:54:00:00:00:01
	testpmd1>set txpkts 64
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000,2000,2000,2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 64,256,2000,64,256,2000
	testpmd1>start tx_first
	testpmd1>show port stats all

8. Quit two testpmd in two VMs, bind virtio-pmd port to virtio-pci,then bind port back to vfio-pci, rerun below cmd 50 times::

	./usertools/dpdk-devbind.py -u 00:05.0
	./usertools/dpdk-devbind.py --bind=virtio-pci 00:05.0
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

9. Rerun step 6-7，check vhost can stable work and get expected throughput.

10. Quit VMs and rerun step 3-9.   

Test Case 4: VM2VM virtio-net split ring test with DSA dpdk driver and iperf stable check
-----------------------------------------------------------------------------------------
This case tests with split ring with DSA dpdk driver in two VMs, check that iperf/scp and reconnection can work stably between two virito-net.

1. Bind 1 NIC port and 2 DSA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:3a:00.0 -a 0000:6a:01.0,max_queues=2 -a 0000:6f:01.0,max_queues=2 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,rxd0@0000:6a:01.0-q1,txd1@0000:6f:01.0-q0,rxd1@0000:6f:01.0-q1] \
	--client --total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
	-daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net0,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :4 -drive file=/home/image/ubuntu2004.img

4. Start VM1 with qemu::

	qemu-system-x86_64  -name vm1 -enable-kvm -pidfile /tmp/.vm1.pid \
	-daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net1,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 -vnc :5 -drive file=/home/image/ubuntu2004_2.img

5. On VM1, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

6. On VM2, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

8. Check iperf throughput can get x Gbits/sec.

9. Scp 1MB file form VM0 to VM1, check packets can be forwarding success by scp::

	Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

10. Relaunch dpdk-vhost, then rerun step 7-9 five times.

11. Relaunch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:3a:00.0 -a 0000:6a:01.0,max_queues=2 -- -p 0x1 --mergeable 1 --vm2vm 1 \
	--socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,rxd1@0000:6a:01.0-q1] --client

12. rerun step 7-9.

Test Case 5: VM2VM virtio-net packed ring test with DSA dpdk driver and iperf stable check
------------------------------------------------------------------------------------------
This case tests with packed ring with DSA dpdk driver in two VMs, check that iperf/scp and reconnection can work stably between two virito-net.

1. Bind 1 NIC port to vfio-pci and 2 DSA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:3a:00.0 -a 0000:6a:01.0,max_queues=2 -a 0000:6f:01.0,max_queues=2 -- -p 0x1 --mergeable 1 --vm2vm 1 \
	--socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,rxd0@0000:6a:01.0-q1,txd1@0000:6f:01.0-q0,rxd1@0000:6f:01.0-q1] \
	--total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
	-daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net0,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :4 -drive file=/home/image/ubuntu2004.img

4. Start VM1 with qemu::

	qemu-system-x86_64  -name vm1 -enable-kvm -pidfile /tmp/.vm1.pid \
	-daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net1,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 -vnc :5 -drive file=/home/image/ubuntu2004_2.img

5. On VM1, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

6. On VM2, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

8. Check iperf throughput can get x Gbits/sec.

9. Scp 1MB file form VM1 to VM2M, check packets can be forwarding success by scp::

	Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

10. Rerun step 7-9 five times.

11. Relaunch VMs with mrg_rxbuf=on.

12. Rerun step 5-10.

Test Case 6: VM2VM virtio-net packed ring test with 2 DSA WQ with dpdk driver and iperf stable check
----------------------------------------------------------------------------------------------------
This case tests with packed ring with 2 DSA WQ with dpdk driver in two VMs, check that iperf/scp and reconnection can work stably between two virito-net.

1. Bind 1 NIC port to vfio-pci and 2 DSA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:3a:00.0 -a 0000:6a:01.0,max_queues=2 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,rxd1@0000:6a:01.0-q1] --total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
	-daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net0,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :4 -drive file=/home/image/ubuntu2004.img

4. Start VM1 with qemu::

	qemu-system-x86_64  -name vm1 -enable-kvm -pidfile /tmp/.vm1.pid \
	-daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net1,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 -vnc :5 -drive file=/home/image/ubuntu2004_2.img

5. On VM1, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

6. On VM2, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

8. Check iperf throughput can get x Gbits/sec.

9. Scp 1MB file form VM1 to VM2M, check packets can be forwarding success by scp::

	Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

10. Rerun step 7-9 five times.

11. Relaunch VMs with mrg_rxbuf=on.

12. Rerun step 5-10.

Test Case 7: VM2VM virtio-user forwarding test when vhost async operation using DSA kernel driver
-------------------------------------------------------------------------------------------------
This case tests that the imix packets can forward normally in VM2VM topology(virtio-user as front-end) when vhost async operation using DSA kernel drvier, both split ring and packed ring have been covered.

1.Bind 1 NIC port and 1 DSA device to idxd::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0
	
	ls /mnt/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
	ls /mnt/dsa #check wq configure success

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:6a:01.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1  --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@wq0.0,rxd0@wq0.1,txd1@wq0.2,rxd1@wq0.3]  \
	--client --total-num-mbufs 600000

3. Launch virtio-user::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/root/dpdk/vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1
	
	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 31-32 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:11,path=/root/dpdk/vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Loop packets between two virtio-user sides, record performance number with 64b/2000b/8000b/IMIX pkts can get expected::

	testpmd0>set fwd mac
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>set eth-peer 0 00:11:22:33:44:11
	testpmd0>start
	testpmd1>set fwd mac
	testpmd1>set eth-peer 0 00:11:22:33:44:10
	testpmd1>set txpkts 64
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000,2000,2000,2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 64,256,2000,64,256,2000
	testpmd1>start tx_first
	testpmd1>show port stats all

5. Stop dpdk-vhost side and relaunch it with below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:6a:01.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1  --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@wq0.0,rxd1@wq0.1]  \
	--client --total-num-mbufs 600000

6. Rerun step 4.

Test Case 8: VM2VM virtio-pmd split ring test with DSA kernel driver register/unregister stable check
------------------------------------------------------------------------------------------------------
This case checks that the split ring with DSA kernel driver can work stably when the virtio-pmd port is registed and unregisted for many times.

1. Bind 1 NIC port and 1 DSA device to idxd::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0
	
	ls /mnt/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
	ls /mnt/dsa #check wq configure success

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:6a:01.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1  --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@wq0.0,rxd0@wq0.1,txd1@wq0.2,rxd1@wq0.3] \
	--client --total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
	-daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net0,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :4 -drive file=/home/image/ubuntu2004.img

4. Start VM1 with qemu::

	qemu-system-x86_64  -name vm1 -enable-kvm -pidfile /tmp/.vm1.pid \
	-daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net1,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 -vnc :5 -drive file=/home/image/ubuntu2004_2.img

5. Bind virtio port to vfio-pci in both two VMs::

	modprobe vfio enable_unsafe_noiommu_mode=1
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

6. Start testpmd in VMs seperately::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -- -i --rxq=1 --txq=1 --nb-cores=1 --txd=1024 --rxd=1024

7. Loop pkts between two virtio-user sides, record performance number with 64b/2000b/8000b/IMIX pkts can get expected::

	testpmd0>set fwd mac
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>set eth-peer 0 52:54:00:00:00:02
	testpmd0>start
	testpmd1>set fwd mac
	testpmd1>set eth-peer 0 52:54:00:00:00:01
	testpmd1>set txpkts 64
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000,2000,2000,2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 64,256,2000,64,256,2000
	testpmd1>start tx_first
	testpmd1>show port stats all

8. Quit two testpmd in two VMs, bind virtio-pmd port to virtio-pci,then bind port back to vfio-pci, rerun below cmd 50 times::

	./usertools/dpdk-devbind.py -u 00:05.0
	./usertools/dpdk-devbind.py --bind=virtio-pci 00:05.0
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

9. Rerun step 6-7, check vhost can stable work and get expected throughput.

10. Quit and relaunch dpdk-vhost with below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:6a:01.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1  --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@wq0.0,rxd1@wq0.3] \
	--client --total-num-mbufs 600000

11. Rerun step 6-9, check vhost can stable work and get expected throughput.

Test Case 9: VM2VM virtio-pmd packed ring test with DSA kernel driver register/unregister stable check
-------------------------------------------------------------------------------------------------------
This case checks that the packed ring with DSA kernel driver can work stably when the virtio-pmd port is registed and unregisted for many times.

1. Bind 1 NIC port and 2 DSA devices to idxd::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0
	
	ls /mnt/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 1
	ls /mnt/dsa #check wq configure success

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:6a:01.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1  --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@wq0.0,rxd0@wq0.1,txd1@wq1.0,rxd1@wq1.1] \
	--client --total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
	-daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net0,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :4 -drive file=/home/image/ubuntu2004.img

4. Start VM1 with qemu::

	qemu-system-x86_64  -name vm1 -enable-kvm -pidfile /tmp/.vm1.pid \
	-daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net1,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 -vnc :5 -drive file=/home/image/ubuntu2004_2.img

5. Bind virtio port to vfio-pci in both two VMs::

	modprobe vfio enable_unsafe_noiommu_mode=1
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

6. Start testpmd in VMs seperately::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -- -i --rxq=1 --txq=1 --nb-cores=1 --txd=1024 --rxd=1024

7. Loop packets between two virtio-user sides, record performance number with 64b/2000b/8000b/IMIX pkts can get expected::

	testpmd0>set fwd mac
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>set eth-peer 0 52:54:00:00:00:02
	testpmd0>start
	testpmd1>set fwd mac
	testpmd1>set eth-peer 0 52:54:00:00:00:01
	testpmd1>set txpkts 64
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 2000,2000,2000,2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 64,256,2000,64,256,2000
	testpmd1>start tx_first
	testpmd1>show port stats all

8. Quit two testpmd in two VMs, bind virtio-pmd port to virtio-pci,then bind port back to vfio-pci, rerun below cmd 50 times::

	./usertools/dpdk-devbind.py -u 00:05.0
	./usertools/dpdk-devbind.py --bind=virtio-pci 00:05.0
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

9. Rerun step 6-7，check vhost can stable work and get expected throughput.

10. Quit VMs and rerun step 3-9.   

Test Case 10: VM2VM virtio-net split ring test with DSA kernel driver and iperf stable check
--------------------------------------------------------------------------------------------
This case tests with split ring with DSA kenrel driver in two VMs, check that iperf/scp and reconnection can work stably between two virito-net.

1. Bind 1 NIC port and 2 DSA devices to idxd::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0
	
	ls /mnt/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 1
	ls /mnt/dsa #check wq configure success

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:6a:01.0 \
	-- -p 0x1 --tso 1 --vm2vm 1 --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@wq0.0,rxd0@wq0.1,txd1@wq1.0,rxd1@wq1.1] \
	--client --total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
	-daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net0,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :4 -drive file=/home/image/ubuntu2004.img

4. Start VM1 with qemu::

	qemu-system-x86_64  -name vm1 -enable-kvm -pidfile /tmp/.vm1.pid \
	-daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net1,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 -vnc :5 -drive file=/home/image/ubuntu2004_2.img

5. On VM1, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

6. On VM2, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

8. Check iperf throughput can get x Gbits/sec.

9. Scp 1MB file form VM0 to VM1, check packets can be forwarding success by scp::

	Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

10. Relaunch dpdk-vhost, then rerun step 7-9 five times.

11. Relaunch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:6a:01.0 -- -p 0x1 --tso 1 --vm2vm 1 \
	--socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@wq0.0,rxd1@wq0.1] --client --total-num-mbufs 600000

12. rerun step 7-9.

Test Case 11: VM2VM virtio-net packed ring test with DSA kenrel driver and iperf stable check
---------------------------------------------------------------------------------------------
This case tests with packed ring with DSA kernel driver in two VMs, check that iperf/scp and reconnection can work stably between two virito-net.

1. Bind 1 NIC port to vfio-pci and 2 DSA devices to idxd::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0
	
	ls /mnt/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 1
	ls /mnt/dsa #check wq configure success

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:6a:01.0 \
	-- -p 0x1 --mergeable 1 --tso 1 --vm2vm 1 --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@wq0.0,rxd0@wq0.1,txd1@wq1.0,rxd1@wq1.1] \
	--client --total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
	-daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net0,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :4 -drive file=/home/image/ubuntu2004.img

4. Start VM1 with qemu::

	qemu-system-x86_64  -name vm1 -enable-kvm -pidfile /tmp/.vm1.pid \
	-daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net1,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 -vnc :5 -drive file=/home/image/ubuntu2004_2.img

5. On VM1, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

6. On VM2, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

8. Check iperf throughput can get x Gbits/sec.

9. Scp 1MB file form VM1 to VM2M, check packets can be forwarding success by scp::

	Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

10. Rerun step 7-9 five times.

11. Relaunch VMs with mrg_rxbuf=on.

12. Rerun step 5-10.

Test Case 12: VM2VM virtio-net packed ring test with 2 DSA WQ with kernel driver and iperf stable check
-------------------------------------------------------------------------------------------------------
This case tests with packed ring with 2 DSA WQ with dpdk driver in two VMs, check that iperf/scp and reconnection can work stably between two virito-net.

1. Bind 1 NIC port to vfio-pci and 1 DSA device to idxd::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:00.0
	
	ls /mnt/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /mnt/dsa #check wq configure success

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:6a:01.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 \
	--dmas [txd0@wq0.0,rxd1@wq0.1] \
	--client --total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
	-daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net0,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :4 -drive file=/home/image/ubuntu2004.img

4. Start VM1 with qemu::

	qemu-system-x86_64  -name vm1 -enable-kvm -pidfile /tmp/.vm1.pid \
	-daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device e1000,netdev=nttsip1  \
	-chardev socket,id=char0,path=./vhost-net1,server -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 \
	-device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 -vnc :5 -drive file=/home/image/ubuntu2004_2.img

5. On VM1, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

6. On VM2, set virtio device IP and run arp protocal::

	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

8. Check iperf throughput can get x Gbits/sec.

9. Scp 1MB file form VM1 to VM2M, check packets can be forwarding success by scp::

	Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

10. Rerun step 7-9 five times.

11. Relaunch VMs with mrg_rxbuf=on.

12. Rerun step 5-10.
