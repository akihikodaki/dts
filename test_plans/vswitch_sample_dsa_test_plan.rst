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

====================================================================
Vswitch sample test vhost async operation with DSA driver test plan
====================================================================

Vswitch sample can leverage DMA to accelerate vhost async data-path from dpdk 20.11. This plan test
vhost async operation with dsa driver (kernel IDXD driver and DPDK vfio-pci driver) in vhost sample.
For more about vswitch example, please refer to the DPDK docment:http://doc.dpdk.org/guides/sample_app_ug/vhost.html

Note:
1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > v5.1, and packed ring multi-queues not support reconnect in qemu yet.
2.For split virtqueue virtio-net with multi-queues server mode test, need qemu version >= 5.2.0, dut to old qemu exist reconnect issue when multi-queues test.
3.The suite has not yet been automated.

Prerequisites
=============

Software
--------
Trex:http://trex-tgn.cisco.com/trex/release/v2.26.tar.gz
qemu: https://download.qemu.org/qemu-6.2.0.tar.xz
iperf

General set up
--------------
1. Compile DPDK and vhost example::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=<dpdk build dir>
	# meson configure -Dexamples=vhost <dpdk build dir>
	# ninja -C <dpdk build dir> -j 110
	For example,
	CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=x86_64-native-linuxapp-gcc
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
1. Bind 1 NIC port to vfio-pci::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
	For example:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:4f.1

2.Bind DSA devices to DPDK vfio-pci driver::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DSA device id>
	For example, bind 2 DMA devices to vfio-pci driver:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:e7:01.0 0000:ec:01.0

.. note::

	One DPDK DSA device can create 8 WQ at most. Below is an example, where DPDK DSA device will create one and
	eight WQ for DSA deivce 0000:e7:01.0 and 0000:ec:01.0. The value of “max_queues” is 1~8:
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:e7:01.0,max_queues=1 -- -i
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4 -n 4 -a 0000:ec:01.0,max_queues=8 -- -i

3. Bind DSA devices to kernel idxd driver, and configure Work Queue (WQ)::

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

Test Case 1: PVP performance vhost async enqueue operation with dsa dpdk channel
---------------------------------------------------------------------------------
This case uses vhost example to test performance of split and packed ring when vhost uses the asynchronous enqueue operations 
with dsa dpdk driver in PVP topology environment.

1. Bind one physical port(4f:00.1) and one dsa device(6a:01.0) to vfio-pci like common step 1-2.

2. On host, launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:4f:00.0 -a 0000:6a:01.0,max_queues=1 -- \
	-p 0x1 --mergeable 1 --vm2vm 1  --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:6a:01.0-q0] --client

3. Launch virtio-user with packed ring::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=virtio-user \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Start pkts from virtio-user side to let vswitch know the mac addr::

	testpmd>set fwd mac
	testpmd>start tx_first
	testpmd>stop
	testpmd>start

5. Inject pkts (packets length=64...1518) separately with dest_mac=virtio_mac_addresss (specific in above cmd with 00:11:22:33:44:10) to NIC using packet generator, record pvp (PG>nic>vswitch>virtio-user>vswitch>nic>PG) performance number can get expected.

6. Quit and re-launch virtio-user with packed ring size not power of 2::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1,queue_size=1025 -- -i --rxq=1 --txq=1 --txd=1025 --rxd=1025 --nb-cores=1

7. Re-test step 4-5, record performance of different packet length.

8. Quit and re-launch virtio-user with split ring::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,mrg_rxbuf=0,in_order=1,server=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

9. Re-test step 4-5, record performance of different packet length.

Test Case 2: PVP vhost async enqueue operation with two VM and 2 dsa channels
------------------------------------------------------------------------------
This case uses vhost example to test split and packed ring when vhost uses the asynchronous enqueue operations 
with dsa dpdk driver in PVP topology environment with 2 VM and 2 queues.

1. Bind one physical port and 2 dsa devices to vfio-pci like common step 1-2.

2. On host, launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:6a:01.0,max_queues=2 -a 0000:6f:01.0,max_queues=1 -- \
	-p 0x1 --mergeable 1 --vm2vm 1  --stats 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 --dmas [txd0@0000:6a:01.0-q1,txd1@0000:6f:01.0-q0] --client

3. launch two virtio-user ports::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-8 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user1,mac=00:11:22:33:44:11,path=/tmp/vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Start pkts from two virtio-user side individually to let vswitch know the mac addr::

	testpmd0>set fwd mac
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>start
	testpmd1>set fwd mac
	testpmd1>start tx_first
	testpmd1>stop
	testpmd1>start

5. Inject IMIX packets (64b...1518b) with dest_mac=virtio_mac_addresss (00:11:22:33:44:10 and 00:11:22:33:44:11) to NIC using packet generator,record performance number can get expected from Packet generator rx side.

6. Stop dpdk-vhost side and relaunch it with same cmd as step2.

7. Start pkts from two virtio-user side individually to let vswitch know the mac addr::

	testpmd0>stop
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>start
	testpmd1>stop
	testpmd1>start tx_first
	testpmd1>stop
	testpmd1>start

8. Inject IMIX packets (64b...1518b) with dest_mac=virtio_mac_addresss (00:11:22:33:44:10 and 00:11:22:33:44:11) to NIC using packet generator, ensure get same throughput as step5.

Test Case 3: VM2VM virtio-user forwarding test with 2 dsa dpdk channels
-------------------------------------------------------------------------
This case uses vhost example to test that split and packed ring can forwarding packets normally when vhost uses the
asynchronous enqueue operations with dsa dpdk driver in VM2VM virtio-user topology environment with 2 queues.

1.Bind one physical ports and 1 dsa devices to vfio-pci like common step 1-2.

2. On host, launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:6a:01.0,max_queues=2 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,txd1@0000:6a:01.0-q1]  --client

3. Launch virtio-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-8 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user1,mac=00:11:22:33:44:11,path=/tmp/vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

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

5. Stop and quit dpdk-vhost side and relaunch it with same cmd as step2.

6. Rerun step 4.

Test Case 4: VM2VM virtio-pmd test with 2 dsa channels register/unregister stable check
-------------------------------------------------------------------------------------------------
This case checks vhost can work stably after registering and unregistering the virtio port many times when vhost uses 
the asynchronous enqueue operations with dsa dpdk driver in VM2VM topology environment with 2 queues.

1. Bind one physical port and one dsa device to vfio-pci like common step 1-2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1 
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0

2. On host, launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:4f:00.1 -a 0000:6a:01.0,max_queues=2 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,txd1@0000:6a:01.0-q1] --client

3. Start VM1 with qemu::

	taskset -c 5,6 /usr/local/qemu-6.1.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

4. Start VM2 with qemu::

	taskset -c 7,8 /usr/local/qemu-6.1.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

5. Bind virtio port to vfio-pci in both two VMs::

	modprobe vfio enable_unsafe_noiommu_mode=1
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

6. Start testpmd in VMs seperately::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -- -i --rxq=1 --txq=1 --nb-cores=1 --txd=1024 --rxd=1024

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

9. Restart vhost, then rerun step 6-7，check vhost can stable work and get expected throughput.

Test Case 5: VM2VM split ring with 2 enqueue dsa dpdk channels test with iperf and reconnect stable check
-----------------------------------------------------------------------------------------------------------
This case checks vhost can work stably after reconnecting when vhost uses the asynchronous enqueue operations with
dsa dpdk driver in VM2VM topology environment with 2 queues.

1. Bind one physical port and 1 dsa device to vfio-pci like common step 1-2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1 
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0

2. On host, launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:4f:00.1 -a 0000:6a:01.0,max_queues=2  \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,txd1@0000:6a:01.0-q1] --client

3. Start VM1 with qemu::

	taskset -c 5,6 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

4. Start VM2 with qemu::

	taskset -c 7,8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

5. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

6. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Check iperf throughput can get x Gbits/sec.

9. Scp 1MB file form VM0 to VM1, check packets can be forwarding success by scp::

	<VM1># scp <file> root@1.1.1.8:/

10. Relaunch dpdk-vhost, then rerun step 7-9 five times.

11. Relaunch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:4f:00.1 -a 0000:6a:01.0,max_queues=2 -a 0000:6f:01.0,max_queues=2 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q0,txd1@0000:6f:01.0-q1] --client

12. Rerun step 7-9 five times.

Test Case 6: VM2VM packed ring with 2 dsa dpdk channels stable test with iperf
-------------------------------------------------------------------------------
This case checks vhost can work stably  when vhost uses the asynchronous enqueue operations with dsa dpdk driver in
VM2VM topology environment with 2 queues.

1. Bind one physical port and 1 dsa device to vfio-pci like common step 1-2::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0 

2. Launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:4f:00.1 -a 0000:6a:01.0,max_queues=2 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 \
	--dmas [txd0@0000:6a:01.0-q1,txd1@0000:6a:01.0-q0]

3. Start VM1 with qemu::

	taskset -c 5,6 /usr/local/qemu-6.1.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

4. Start VM2 with qemu::

	taskset -c 7,8 /usr/local/qemu-6.1.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

5. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

6. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Check iperf throughput can get x Gbits/sec.

9. Scp 1MB file form VM1 to VM2M, check packets can be forwarding success by scp::

	<VM1># scp <file> root@1.1.1.8:/

10. Rerun step 7-9 five times.

Test Case 7: PVP performance vhost async enqueue with dsa kernel channel
-------------------------------------------------------------------------
This case uses vhost example to test performance of split and packed ring when vhost uses the asynchronous enqueue operations
with dsa kernel driver in PVP topology environment.

1. Bind one physical port(4f:00.1) to vfio-pci and one dsa device(6a:01.0) to idxd like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1
	
	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /dev/dsa #check wq configure success

2. On host, launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:4f:00.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1  --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@wq0.0] --client

3. Launch virtio-user with packed ring::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=virtio-user \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Start pkts from virtio-user side to let vswitch know the mac addr::

	testpmd>set fwd mac
	testpmd>start tx_first
	testpmd>stop
	testpmd>start

5. Inject pkts (packets length=64...1518) separately with dest_mac=virtio_mac_addresss (specific in above cmd with 00:11:22:33:44:10) to NIC using packet generator, record pvp (PG>nic>vswitch>virtio-user>vswitch>nic>PG) performance number can get expected.

6. Quit and re-launch virtio-user with packed ring size not power of 2::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1,queue_size=1025 -- -i --rxq=1 --txq=1 --txd=1025 --rxd=1025 --nb-cores=1

7. Re-test step 4-5, record performance of different packet length.

8. Quit and re-launch virtio-user with split ring::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,mrg_rxbuf=0,in_order=1,server=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

9. Re-test step 4-5, record performance of different packet length.

Test Case 8: PVP vhost async enqueue operation with two VM and 2 dsa kernel channels
---------------------------------------------------------------------------------------
This case uses vhost example to test split and packed ring when vhost uses the asynchronous enqueue operations
with dsa kernel driver in PVP topology environment with 2 VM and 2 queues.

1. Bind one physical port to vfio-pci and 1 dsa device to idxd like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /dev/dsa #check wq configure success

2. On host, launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:4f:00.1 \
	-- -p 0x1 --mergeable 1 --vm2vm 1  --stats 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 \
	--dmas [txd0@wq0.0,txd1@wq0.1] --client

3. launch two virtio-user ports::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-8 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user1,mac=00:11:22:33:44:11,path=/tmp/vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Start pkts from two virtio-user side individually to let vswitch know the mac addr::

	testpmd0>set fwd mac
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>start
	testpmd1>set fwd mac
	testpmd1>start tx_first
	testpmd1>stop
	testpmd1>start

5. Inject IMIX packets (64b...1518b) with dest_mac=virtio_mac_addresss (00:11:22:33:44:10 and 00:11:22:33:44:11) to NIC using packet generator,record performance number can get expected from Packet generator rx side.

6. Stop dpdk-vhost side and relaunch it with same cmd as step2.

7. Start pkts from two virtio-user side individually to let vswitch know the mac addr::

	testpmd0>stop
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>start
	testpmd1>stop
	testpmd1>start tx_first
	testpmd1>stop
	testpmd1>start

8. Inject IMIX packets (64b...1518b) with dest_mac=virtio_mac_addresss (00:11:22:33:44:10 and 00:11:22:33:44:11) to NIC using packet generator, ensure get same throughput as step5.

Test Case 9: VM2VM virtio-user forwarding test with 2 dsa kernel channels
---------------------------------------------------------------------------------
This case uses vhost example to test split and packed ring when vhost uses the asynchronous enqueue operations
with dsa kernel driver in VM2VM topology environment with 2 queues.

1.Bind one physical port to vfio-pci and 2 dsa device to idxd like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 2
	ls /dev/dsa #check wq configure success

2. On host, launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:4f:01.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 \
	--dmas [txd0@wq0.0,txd1@wq2.1]  --client

3. Launch virtio-user::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-8 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user1,mac=00:11:22:33:44:11,path=/tmp/vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

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

5. Stop and quit dpdk-vhost side and relaunch it with same cmd as step2.

6. Rerun step 4.

Test Case 10: VM2VM virtio-pmd test with 2 dsa kernel channels register/unregister stable check
-------------------------------------------------------------------------------------------------
This case checks vhost can work stably after unregistering and registering the virtio port many times when vhost uses
the asynchronous enqueue operations with dsa kernel driver in VM2VM topology environment with 2 queues.

1. Bind one physical port to vfio-pci and one dsa device to idxd like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1

	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /dev/dsa #check wq configure success

2. On host, launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:4f:00.1 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 \
	--dmas [txd0@wq0.0,txd1@wq0.1] --client

3. Start VM1 with qemu::

	taskset -c 5,6 /usr/local/qemu-6.1.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

4. Start VM2 with qemu::

	taskset -c 7,8 /usr/local/qemu-6.1.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

5. Bind virtio port to vfio-pci in both two VMs::

	modprobe vfio enable_unsafe_noiommu_mode=1
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

6. Start testpmd in VMs seperately::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 -- -i --rxq=1 --txq=1 --nb-cores=1 --txd=1024 --rxd=1024

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

9. Restart vhost, then rerun step 6-7，check vhost can stable work and get expected throughput.

Test Case 11: VM2VM split ring with 2 enqueue dsa kernel channels test with iperf and reconnect stable check
-------------------------------------------------------------------------------------------------------------
This case checks vhost can work stably after reconnecting when vhost uses the asynchronous enqueue operations with
dsa kernel driver in VM2VM topology environment with 2 queues.

1. Bind one physical port to vfio-pci and 2 dsa device to idxd like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1
	
	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0 6f:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 6f:01.0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 2
	ls /dev/dsa #check wq configure success

2. On host, launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:4f:00.1 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 \
	--dmas [txd0@wq0.0,txd1@wq0.1] --client

3. Start VM1 with qemu::

	taskset -c 5,6 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

4. Start VM2 with qemu::

	taskset -c 7,8 /root/xingguang/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge1G1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/root/xingguang/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net1,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

5. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

6. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Check iperf throughput can get x Gbits/sec.

9. Scp 1MB file form VM0 to VM1, check packets can be forwarding success by scp::

	<VM1># scp <file> root@1.1.1.8:/

10. Relaunch dpdk-vhost, then rerun step 7-9 five times.

11. Relaunch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:4f:00.1 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 \
	--dmas [txd0@wq0.0,txd1@wq2.1] --client
	
12. Rerun step 7-9 five times.	

Test Case 12: VM2VM packed ring with 2 dsa kernel channels stable test with iperf
----------------------------------------------------------------------------------
This case checks vhost can work stably  when vhost uses the asynchronous enqueue operations with dsa kernel driver in
VM2VM topology environment with 2 queues.

1. Bind one physical port to vfio-pci and 1 dsa device to idxd like common step 1 and 3::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 4f:00.1
	
	ls /dev/dsa #check wq configure, reset if exist
	<dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
	<dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0 
	<dpdk dir># ./<dpdk build dir>drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
	ls /dev/dsa #check wq configure success

2. Launch dpdk-vhost by below command::

	<dpdk dir># ./<dpdk build dir>/examples/dpdk-vhost -l 26-28 -n 4 -a 0000:4f:00.1 -a 0000:6a:01.0,max_queues=2 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 \
	--dmas [txd0@wq0.0,txd1@wq0.1]

3. Start VM1 with qemu::

	taskset -c 5,6 /usr/local/qemu-6.1.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

4. Start VM2 with qemu::

	taskset -c 7,8 /usr/local/qemu-6.1.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
	-chardev socket,id=char0,path=/tmp/vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

5. On VM1, set virtio device IP and run arp protocal::

	<VM1># ifconfig ens5 1.1.1.2
	<VM1># arp -s 1.1.1.8 52:54:00:00:00:02

6. On VM2, set virtio device IP and run arp protocal::

	<VM2># ifconfig ens5 1.1.1.8
	<VM2># arp -s 1.1.1.2 52:54:00:00:00:01

7. Check the iperf performance between two VMs by below commands::

	<VM1># iperf -s -i 1
	<VM2># iperf -c 1.1.1.2 -i 1 -t 60

8. Check iperf throughput can get x Gbits/sec.

9. Scp 1MB file form VM1 to VM2M, check packets can be forwarding success by scp::

	<VM1># scp <file> root@1.1.1.8:/

10. Rerun step 7-9 five times.