.. Copyright (c) <2021>, Intel Corporation
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

========================================================
Vswitch sample test with vhost async data path test plan
========================================================

Description
===========

Vswitch sample can leverage IOAT to accelerate vhost async data-path from dpdk 20.11. This plan test
vhost DMA operation callbacks for CBDMA PMD and vhost async data-path in vhost sample.
From 20.11 to 21.02, only split ring support cbdma copy with vhost enqueue direction;
from 21.05,packed ring also can support cbdma copy with vhost enqueue direction.

Prerequisites
=============


Test Case1: PVP performance check with CBDMA channel using vhost async driver
=============================================================================

1. Bind physical port to vfio-pci and CBDMA channel to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 31-32 -n 4 -- \
	-p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0] --client --total-num-mbufs 600000

3. Launch virtio-user with packed ring::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,mrg_rxbuf=0,in_order=1,vectorized=1,packed_vq=1,server=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Start pkts from virtio-user side to let vswitch know the mac addr::

	testpmd>set fwd mac
	testpmd>start tx_first

5. Inject pkts (packets length=64...1518) separately with dest_mac=virtio_mac_address (specific in above cmd with 00:11:22:33:44:10) to NIC using packet generator, record pvp (PG>nic>vswitch>virtio-user>vswitch>nic>PG) performance number can get expected.

6. Quit and re-launch virtio-user with packed ring size not power of 2::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,mrg_rxbuf=0,in_order=1,vectorized=1,packed_vq=1,server=1,queue_size=1025 -- -i --rxq=1 --txq=1 --txd=1025 --rxd=1025 --nb-cores=1

7. Re-test step 4-5, record performance of different packet length.

8. Quit and re-launch virtio-user with split ring::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,mrg_rxbuf=0,in_order=1,vectorized=1,server=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

9. Re-test step 4-5, record performance of different packet length.

Test Case2: PVP test with two VM and two CBDMA channels using vhost async driver
=================================================================================

1. Bind one physical ports to vfio-pci and two CBDMA channels to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -- \
	-p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat --stats 1 --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 --dmas [txd0@0000:00:01.0,txd1@0000:00:01.1] --client--total-num-mbufs 600000

3. launch two virtio-user ports::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1
	
	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 31-32 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:11,path=/tmp/vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Start pkts from two virtio-user side individually to let vswitch know the mac addr::

	testpmd0>set fwd mac
	testpmd1>set fwd mac
	testpmd1>start tx_first
	testpmd1>start tx_first

5. Inject IMIX packets (64b...1518b) with dest_mac=virtio_mac_address (00:11:22:33:44:10 and 00:11:22:33:44:11) to NIC using packet generator,record performance number can get expected from Packet generator rx side.

6. Stop dpdk-vhost side and relaunch it with same cmd as step2.

7. Start pkts from two virtio-user side individually to let vswitch know the mac addr::

    testpmd0>stop
    testpmd0>start tx_first
    testpmd1>stop
    testpmd1>start tx_first

8. Inject IMIX packets (64b...1518b) with dest_mac=virtio_mac_address (00:11:22:33:44:10 and 00:11:22:33:44:11) to NIC using packet generator, ensure get same throughput as step5.

Test Case3: VM2VM forwarding test with two CBDMA channels
=========================================================

1.Bind one physical ports to vfio-pci and two CBDMA channels to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -- -p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat \
	--socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 --dmas [txd0@0000:00:04.0,txd1@0000:00:04.1]  --client --total-num-mbufs 600000

3. Launch virtio-user::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-30 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 31-32 -n 4 --no-pci --file-prefix=testpmd1 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:11,path=/tmp/vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1 -- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Loop pkts between two virtio-user sides, record performance number with 64b/2000b/8000b/IMIX pkts can get expected::

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

5. Stop dpdk-vhost side and relaunch it with same cmd as step2.

6. Rerun step 4.

Test Case4: VM2VM test with cbdma channels register/unregister stable check
============================================================================

1. Bind one physical ports to vfio-pci and two CBDMA channels to vfio-pci.

2. On host, launch dpdk-vhost by below command::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -- -p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat \
    --socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 --dmas [txd0@0000:00:04.0,txd1@0000:00:04.1] --client --total-num-mbufs 600000

3. Start VM0 with qemu-5.2.0::

 	qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
        -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
        -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
        -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
        -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
        -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
        -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
        -chardev socket,id=char0,path=/tmp/vhost-net0,server \
        -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
        -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

4. Start VM1 with qemu-5.2.0::

	qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
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

9. Restart vhost, then rerun step 7，check vhost can stable work and get expected throughput.

Test Case5: VM2VM split ring test with iperf and reconnect stable check
=======================================================================

1. Bind one physical ports to vfio-pci and two CBDMA channels to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -- -p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat \
	--socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 --dmas [txd0@0000:00:04.0,txd1@0000:00:04.1] --client --total-num-mbufs 600000

3. Start VM0 with qemu-5.2.0::

 	qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
        -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
        -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
        -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
        -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
        -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
        -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
        -chardev socket,id=char0,path=/tmp/vhost-net0,server \
        -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
        -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

4. Start VM1 with qemu-5.2.0::

	qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
        -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
        -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
        -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
        -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
        -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
        -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
        -chardev socket,id=char0,path=/tmp/vhost-net1,server \
        -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
        -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

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

10. Relaunch vhost-dpdk, then rerun step 7-9 five times.

Test Case6: VM2VM packed ring test with iperf and reconnect stable test
=======================================================================

1. Bind one physical ports to vfio-pci and two CBDMA channels to vfio-pci.

2. On host, launch dpdk-vhost by below command::

	./x86_64-native-linuxapp-gcc/examples/dpdk-vhost -l 26-28 -n 4 -- -p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat \
	--socket-file /tmp/vhost-net0 --socket-file /tmp/vhost-net1 --dmas [txd0@0000:00:04.0,txd1@0000:00:04.1] --total-num-mbufs 600000

3. Start VM0 with qemu-5.2.0::

 	qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
        -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
        -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
        -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
        -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
        -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
        -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
        -chardev socket,id=char0,path=/tmp/vhost-net0 \
        -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
        -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

4. Start VM1 with qemu-5.2.0::

	qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
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
