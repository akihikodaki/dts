========================================================
Vswitch sample test with vhost async data path test plan
========================================================

Description
===========

Vswitch sample can leverage IOAT to accelerate vhost async data-path from dpdk 20.11. This plan test
vhost DMA operation callbacks for CBDMAV PMD and vhost async data-path in vhost sample. Also compare
the performance between CPU copy, CBDMA copy and Sync copy. 
CPU copy means vhost enqueue w/o cbdma channel; CBDMA copy needs vhost enqueue with cbdma channel
using parameter '-dmas'; Sync copy needs vhost enqueue with cbdma channel, but threshold ( can be
adjusted by change value of f.async_threshold in dpdk code) is larger than forwarding packet length.

CBDMA performance indicator
===========================

(1)CPU copy vs. sync copy delta < 10% for 64B packet size
(2)CBDMA copy vs sync copy delta > 5% for 1518 packet size

Prerequisites
=============

Modify the testpmd code as following::

	--- a/examples/vhost/main.c
	+++ b/examples/vhost/main.c
	@@ -29,7 +29,7 @@
	 #include "main.h"

	 #ifndef MAX_QUEUES
	-#define MAX_QUEUES 128
	+#define MAX_QUEUES 512
	 #endif

	 /* the maximum number of external ports supported */

Test Case1: PVP performance check with CBDMA channel using vhost async driver
=============================================================================

1. Adjust dpdk code as below::

	--- a/examples/vhost/main.c
	+++ b/examples/vhost/main.c
	@@ -1343,7 +1343,7 @@ new_device(int vid)

        if (async_vhost_driver) {
                	f.async_inorder = 1;
	-               f.async_threshold = 256;
	+               f.async_threshold = 1518;
                	return rte_vhost_async_channel_register(vid, VIRTIO_RXQ,
                        	f.intval, &channel_ops);
        }

2. Bind physical port to vfio-pci and CBDMA channel to igb_uio.

3. On host, launch dpdk-vhost by below command::

	./dpdk-vhost -c 0x1c000000 -n 4 -- \
	-p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@00:04.0]

4. Launch virtio-user with testpmd::

	./dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

5. Start pkts from virtio-user side to let vswitch know the mac addr::

	testpmd>set fwd mac #if use io fwd ,ixia can't receive packets
	testpmd>start tx_first
	testpmd>stop
	testpmd>start #start to forward

6. Inject different length pkts (packets length=64,512,1024,1518) seperately with VLAN_id=1000 and dest_mac=virtio_mac_addresss ( specific in above cmd with 00:11:22:33:44:10) to NIC using packet generator, record performance number.

7. Adjust vswitch code as below, re-test step 3-6 and record perfromance of different packet length::

	--- a/examples/vhost/main.c
	+++ b/examples/vhost/main.c
	@@ -1343,7 +1343,7 @@ new_device(int vid)

        if (async_vhost_driver) {
                	f.async_inorder = 1;
	-               f.async_threshold = 256;
	+               f.async_threshold = 0;
                	return rte_vhost_async_channel_register(vid, VIRTIO_RXQ,
                        	f.intval, &channel_ops);
        }

8. Re-test step 3-6 except to launch dpdk-vhost by below command, record perfromance of different packet length::

	./dpdk-vhost -c 0x1c000000 -n 4 -- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 --socket-file /tmp/vhost-net

9. Compare performance, check below two performance indicator::

	(1)CPU copy vs. sync copy delta < 10% for 64B packet size
	(2)CBDMA copy vs sync copy delta > 5% for 1518 packet size

Test Case2: PV test with multiple CBDMA channels using vhost async driver
==========================================================================

1. Bind one physical ports to vfio-pci and two CBDMA channels to igb_uio.

2. On host, launch dpdk-vhost by below command::

	./dpdk-vhost -l 26-28 -n 4 -- \
	-p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat --stats 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 --dmas [txd0@00:04.0,txd1@00:04.1] --client

3. launch two virtio-user ports::

	./dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net0,queues=1,server=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1
	
	./dpdk-testpmd -l 31-32 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:11,path=/tmp/vhost-net1,queues=1,server=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Start pkts from two virtio-user side individually to let vswitch know the mac addr::

	testpmd0>start tx_first
	testpmd1>start tx_first

5. Inject 1518B packets with VLAN_id=1000 and dest_mac=virtio_mac_addresss (00:11:22:33:44:10 and 00:11:22:33:44:11) to NIC using packet generator,check two virtio-user ports can receive according packets.

6. Stop dpdk-vhost side and relaunch it with same cmd as step2.

7.Start pkts from two virtio-user side individually to let vswitch know the mac addr, check two virtio-user ports still can receive according packets and get same throughput as step5::

        testpmd0>stop
        testpmd0>start tx_first
        testpmd1>stop
        testpmd1>start tx_first

Test Case3: VM2VM performance test with two CBDMA channels using vhost async driver
====================================================================================

1.Bind one physical ports to vfio-pci and two CBDMA channels to igb_uio.

2. On host, launch dpdk-vhost by below command::

	./dpdk-vhost -l 27-28 -n 4 -- -p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat \
	--socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 --dmas [txd0@00:04.0,txd1@00:04.1]

3. Launch virtio-user::

	./dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net0,queues=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

	./dpdk-testpmd -l 31-32 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:11,path=/tmp/vhost-net0,queues=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Start pkts from two virtio-user sides, record performance number with txpkts=256 and 2000 from testpmd1 seperately::

	testpmd0>set fwd mac
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>set eth-peer 0 00:11:22:33:44:11
	testpmd0>start

	testpmd1>set fwd mac
	testpmd1>set eth-peer 0 00:11:22:33:44:10
	testpmd1>set txpkts 2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 256
	testpmd1>start tx_first
	testpmd1>show port stats all

5. Re-test step 2-4 except to launch dpdk-vhost by below command, record perfromance::

	./dpdk-vhost -l 27-28 -n 4 -- -p 0x1 --mergeable 1 --vm2vm 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1

6. Compare perfromance number, when txpkts=2000, first test has better performance; while txpkts=256, the second test has better performance.

Test Case4: VM2VM test with 2 vhost device using vhost async driver
=======================================================================

1. Bind one physical ports to vfio-pci and two CBDMA channels to igb_uio.

2. On host, launch dpdk-vhost by below command::

	./dpdk-vhost -l 27-28 -n 4 -- -p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat \
	--socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 --dmas [txd0@00:04.0,txd1@00:04.1]

3. Start VM0::

 	/home/qemu-install/qemu-4.2.1/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
        -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
        -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
        -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
        -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
        -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
        -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
        -chardev socket,id=char0,path=/tmp/vhost-net0 \
        -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
        -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

4. Start VM1::

	/home/qemu-install/qemu-4.2.1/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
        -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
        -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
        -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
        -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
        -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
        -netdev user,id=nttsip1,hostfwd=tcp:10.67.119.61:6003-:22 \
        -chardev socket,id=char0,path=/tmp/vhost-net1 \
        -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
        -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

5. Bind virtio port to vfio-pci in both two VMs::

	modprobe vfio enable_unsafe_noiommu_mode=1
	modprobe vfio-pci
	echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

6. Start testpmd in VMs seperately::

	./dpdk-testpmd -l 1-2 -n 4 -- -i --rxq=1 --txq=1 --nb-cores=1 --txd=1024 --rxd=1024

7. Start pkts from two virtio-pmd, record performance number with txpkts=256 and 2000 from testpmd1 seperately::

	testpmd0>set fwd mac
	testpmd0>start tx_first
	testpmd0>stop
	testpmd0>set eth-peer 0 52:54:00:00:00:02
	testpmd0>start

	testpmd1>set fwd mac
	testpmd1>set eth-peer 0 52:54:00:00:00:01
	testpmd1>set txpkts 2000
	testpmd1>start tx_first
	testpmd1>show port stats all
	testpmd1>stop
	testpmd1>set txpkts 256
	testpmd1>start tx_first
	testpmd1>show port stats all

8. Inject traffic with VLAN_id=1000 and dest_mac=virtio_mac_addresss (52:54:00:00:00:02 and 52:54:00:00:00:02) to NIC using packet generator, check two virtio-pmd can receive according packets.

9. Quit two testpmd in two VMs, bind virtio-pmd port to virtio-pci,then bind port back to vfio-pci, rerun below cmd 50 times::

	./usertools/dpdk-devbind.py -u 00:05.0
	./usertools/dpdk-devbind.py --bind=virtio-pci 00:05.0
	./usertools/dpdk-devbind.py --bind=vfio-pci 00:05.0

10. Rerun step 6-8，check vhost can stable work.
