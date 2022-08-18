.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

========================================================
Vswitch sample test with vhost async data path test plan
========================================================

Description
===========

Vswitch sample can leverage DMA to accelerate vhost async data-path from dpdk 20.11. This plan test
vhost DMA operation callbacks for CBDMA PMD and vhost async data-path in vhost sample.
From 22.07, split and packed ring support cbdma copy with both vhost enqueue and deuque direction.

--dmas This parameter is used to specify the assigned DMA device of a vhost device. Async vhost-user
net driver will be used if --dmas is set. For example –dmas [txd0@00:04.0,txd1@00:04.1,rxd0@00:04.2,rxd1@00:04.3]
means use DMA channel 00:04.0/00:04.2 for vhost device 0 enqueue/dequeue operation and use DMA channel
00:04.1/00:04.3 for vhost device 1 enqueue/dequeue operation. The index of the device corresponds to
the socket file in order, that means vhost device 0 is created through the first socket file,
vhost device 1 is created through the second socket file, and so on.
For more about vswitch example, please refer to the DPDK docment:http://doc.dpdk.org/guides/sample_app_ug/vhost.html

Prerequisites
=============

Hardware
--------
Supportted NICs: nic that supports VMDQ

Software
--------
Trex:http://trex-tgn.cisco.com/trex/release/v2.26.tar.gz

General set up
--------------
1. Compile DPDK and vhost example::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
	# meson configure -Dexamples=vhost x86_64-native-linuxapp-gcc
	# ninja -C x86_64-native-linuxapp-gcc -j 110

Test Case 1: PVP performance check with CBDMA channel using vhost async driver
------------------------------------------------------------------------------
This case tests the basic performance of split ring and packed ring with different packet size when using vhost async drvier.

1. Bind one physical port and 2 CBDMA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 31-32 -n 4 -a 0000:af:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -- \
	-p 0x1 --mergeable 1 --vm2vm 1  --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0,rxd0@0000:00:04.1] --client --total-num-mbufs 600000

3. Launch virtio-user with packed ring::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,mrg_rxbuf=0,in_order=1,vectorized=1,packed_vq=1,server=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Start pkts from virtio-user side to let vswitch know the mac addr::

	testpmd>set fwd mac
	testpmd>start tx_first

5. Inject packets with different packet size[64, 128, 256, 512, 1024, 1280, 1518] and dest_mac=virtio_mac_address (specific in above cmd with 00:11:22:33:44:10) to NIC using packet generator, record pvp (PG>nic>vswitch>virtio-user>vswitch>nic>PG) performance number can get expected.

6. Quit and re-launch virtio-user with split ring::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,mrg_rxbuf=0,in_order=1,vectorized=1,server=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

7. Re-test step 4-5, record performance of different packet length.

Test Case 2: PVP test with two VMs using vhost async driver
-----------------------------------------------------------
This case tests that the imix packets can forward normally with two VMs in PVP topology when using vhost async drvier, both split ring and packed ring have been covered.

1. Bind one physical ports to vfio-pci and 4 CBDMA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:af:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -- \
	-p 0x1 --mergeable 1 --vm2vm 1  --stats 1 --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 --dmas [txd0@0000:00:04.0,rxd0@0000:00:04.1,txd1@0000:00:04.2,rxd1@0000:00:04.3] --client--total-num-mbufs 600000

3. launch two virtio-user ports::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/root/dpdk/vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 31-32 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:11,path=/root/dpdk/vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Start packets from two virtio-user side individually to let vswitch know the mac addr::

	testpmd0>set fwd mac
	testpmd0>start tx_first
	testpmd1>set fwd mac
	testpmd1>start tx_first

5. Inject IMIX packets (64b...1518b) with dest_mac=virtio_mac_address (00:11:22:33:44:10 and 00:11:22:33:44:11) to NIC using packet generator,record performance number can get expected from Packet generator rx side.

6. Quit and relaunch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:af:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3  -- \
	-p 0x1 --mergeable 1 --vm2vm 1  --stats 1 --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 --dmas [txd0@0000:00:01.0,rxd1@0000:00:01.1] --client--total-num-mbufs 600000

7. Start packets from two virtio-user side individually to let vswitch know the mac addr::

	testpmd0>stop
	testpmd0>start tx_first
	testpmd1>stop
	testpmd1>start tx_first

8.Inject IMIX packets (64b...1518b) to NIC using packet generator, ensure get same throughput as step5.

Test Case 3: VM2VM virtio-user forwarding test using vhost async driver
-----------------------------------------------------------------------
This case tests that the imix packets can forward normally in VM2VM topology(virtio-user as front-end) when using vhost async drvier, both split ring and packed ring have been covered.

1.Bind one physical port and 4 CBDMA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:af:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -- -p 0x1 --mergeable 1 --vm2vm 1  \
	--socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 --dmas [txd0@0000:00:04.0,rxd0@0000:00:04.1,txd1@0000:00:04.2,rxd1@0000:00:04.3]  --client --total-num-mbufs 600000

3. Launch virtio-user::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/root/dpdk/vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 31-32 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:11,path=/root/dpdk/vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

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

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:af:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -- -p 0x1 --mergeable 1 --vm2vm 1  \
	--socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 --dmas [txd0@0000:00:04.0,rxd1@0000:00:04.1]  --client --total-num-mbufs 600000

6. Rerun step 4.

Test Case 4: VM2VM virtio-pmd split ring test with cbdma channels register/unregister stable check
--------------------------------------------------------------------------------------------------
This case checks that the split ring with CBDMA channel can work stably when the virtio-pmd port is registed and unregisted for many times.

1. Bind one physical port and 4 CBDMA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:af:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -- -p 0x1 --mergeable 1 --vm2vm 1  \
	--socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 --dmas [txd0@0000:00:04.0,rxd0@0000:00:04.1,txd1@0000:00:01.2,rxd1@0000:00:01.3] --client --total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=/root/dpdk/vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

4. Start VM1 with qemu::

	qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=/root/dpdk/vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

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

9. Quit and relaunch dpdk-vhost with below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:af:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -- -p 0x1 --mergeable 1 --vm2vm 1  \
	--socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 --dmas [txd0@0000:00:04.0,rxd1@0000:00:01.3] --client --total-num-mbufs 600000

10. Rerun step 6-7，check vhost can stable work and get expected throughput.

Test Case 5: VM2VM virtio-pmd packed ring test with cbdma channels register/unregister stable check
---------------------------------------------------------------------------------------------------
This case checks that the packed ring with CBDMA channel can work stably when the virtio-pmd port is registed and unregisted for many times.

1. Bind one physical port and 4 CBDMA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:af:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -- -p 0x1 --mergeable 1 --vm2vm 1  \
	--socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 --dmas [txd0@0000:00:04.0,rxd0@0000:00:04.1,txd1@0000:00:04.2,rxd1@0000:00:04.3] --client --total-num-mbufs 600000

3. Start VM0 with qemu::

	qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=/root/dpdk/vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

4. Start VM1 with qemu::

	qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=/root/dpdk/vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

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

Test Case 6: VM2VM virtio-net split ring test with 4 cbdma channels and iperf stable check
------------------------------------------------------------------------------------------
This case tests with split ring with cbdma channels in two VMs, check that iperf/scp and reconnection can work stably between two virito-net.

1. Bind one physical port and 4 CBDMA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 --dmas [txd0@0000:00:04.0,rxd0@0000:00:04.1,txd1@0000:00:04.2,rxd1@0000:00:04.3] --client

3. Start VM1 with qemu::

	taskset -c 5,6 /usr/local/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=/root/dpdk/vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

4. Start VM2 with qemu::

	taskset -c 7,8 /usr/local/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=/root/dpdk/vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

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

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:af:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 --dmas [txd0@0000:00:04.0,rxd1@0000:00:04.1] --client

12. rerun step 7-9.

Test Case 7: VM2VM virtio-net packed ring test with 4 cbdma channels and iperf stable check
-------------------------------------------------------------------------------------------
This case tests with packed ring with 4 cbdma channels in two VMs, check that iperf/scp and reconnection can work stably between two virito-net.

1. Bind one physical ports to vfio-pci and 4 CBDMA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:af:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -- -p 0x1 --mergeable 1 --vm2vm 1 \
	--socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 --dmas [txd0@0000:00:04.0,rxd0@0000:00:04.1,txd1@0000:00:04.2,rxd1@0000:00:04.3] --total-num-mbufs 600000

3. Start VM1::

	qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=/root/dpdk/vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

4. Start VM2::

	qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=/root/dpdk/vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

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

Test Case 8: VM2VM virtio-net packed ring test with 2 cbdma channels and iperf stable check
-------------------------------------------------------------------------------------------
This case tests with packed ring with 2 cbdma channels in two VMs, check that iperf/scp and reconnection can work stably between two virito-net.

1. Bind one physical ports to vfio-pci and 2 CBDMA devices to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:af:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -- -p 0x1 --mergeable 1 --vm2vm 1 \
	--socket-file /root/dpdk/vhost-net0 --socket-file /root/dpdk/vhost-net1 --dmas [txd0@0000:00:04.0,rxd1@0000:00:04.1] --total-num-mbufs 600000

3. Start VM1::

	qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=/root/dpdk/vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

4. Start VM2::

	qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=/root/dpdk/vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

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
