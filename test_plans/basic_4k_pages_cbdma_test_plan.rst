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

===========================================
Basic test with CBDMA in 4K-pages test plan
===========================================

DPDK 19.02 add support for using virtio-user without hugepages. The --no-huge mode was augmented to use memfd-backed memory 
(on systems that support memfd), to allow using virtio-user-based NICs without hugepages.

Vhost asynchronous data path leverages DMA devices to offload memory copies from the CPU and it is implemented in an asynchronous way.
In addition, vhost supports M:N mapping between vrings and DMA virtual channels. Specifically, one vring can use multiple different DMA 
channels and one DMA channel can be shared by multiple vrings at the same time. Vhost enqueue operation with CBDMA channels is supported
in both split and packed ring.

This document provides the test plan for testing some basic functions with CBDMA device in 4K-pages memory environment.
1. Test split and packed ring virtio path in the PVP topology environmet.
2. Check Vhost tx offload function by verifing the TSO/cksum in the TCP/IP stack with vm2vm split ring and packed ring
vhost-user/virtio-net mergeable path.
3.Check the payload of large packet (larger than 1MB) is valid after forwarding packets with vm2vm split ring and packed ring 
vhost-user/virtio-net mergeable path.
4. Vhost-user using 1G hugepges and virtio-user using 4k-pages.

.. note:

   1. When CBDMA channels are bound to vfio driver, VA mode is the default and recommended.
   For PA mode, page by page mapping may exceed IOMMU's max capability, better to use 1G guest hugepage.
   2. DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd. And case 4-5 have not yet been automated.

For more about dpdk-testpmd sample, please refer to the DPDK docments:
https://doc.dpdk.org/guides/testpmd_app_ug/run_app.html
For virtio-user vdev parameter, you can refer to the DPDK docments:
https://doc.dpdk.org/guides/nics/virtio.html#virtio-paths-selection-and-usage.

Prerequisites
=============

Software
--------
Trex:http://trex-tgn.cisco.com/trex/release/v2.26.tar.gz

General set up
--------------
1. Turn off transparent hugepage in grub by adding GRUB_CMDLINE_LINUX="transparent_hugepage=never".
   
2. Compile DPDK::

	# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=<dpdk build dir>
	# ninja -C <dpdk build dir> -j 110
    For example:
    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

3. Get the PCI device ID and DMA device ID of DUT, for example, 0000:18:00.0 is PCI device ID, 0000:00:04.0, 0000:00:04.1 is DMA device ID::

	<dpdk dir># ./usertools/dpdk-devbind.py -s

	Network devices using kernel driver
	===================================
	0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci

	DMA devices using kernel driver
	===============================
	0000:00:04.0 'Sky Lake-E CBDMA Registers 2021' drv=ioatdma unused=vfio-pci
	0000:00:04.1 'Sky Lake-E CBDMA Registers 2021' drv=ioatdma unused=vfio-pci

4. Prepare tmpfs with 4K-pages::

    mkdir /mnt/tmpfs_nohuge0
    mkdir /mnt/tmpfs_nohuge1
    mount tmpfs /mnt/tmpfs_nohuge0 -t tmpfs -o size=4G
    mount tmpfs /mnt/tmpfs_nohuge1 -t tmpfs -o size=4G

Test case
=========

Common steps
------------
1. Bind 1 NIC port and CBDMA channels to vfio-pci::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DMA device id>

	For example, bind 1 NIC port and 1 CBDMA channels:
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:af:00.0,0000:80:04.0

Test Case 1: Basic test vhost/virtio-user split ring with 4K-pages and cbdma enable
-----------------------------------------------------------------------------------
This case uses testpmd Traffic Generator(For example, Trex) to test split ring when vhost uses the asynchronous enqueue operations with CBDMA channels
in 4k-pages environment. And the mapping between vrings and dsa virtual channels is 1:1.

1. Bind 1 NIC port and 1 CBDMA channel to vfio-pci, as common steps 1.

2. Launch vhost by below command::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 31-32 -n 4 --no-huge -m 1024 --file-prefix=vhost -a 0000:af:00.0 -a 0000:80:04.0 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net,queues=1,dmas=[txq0]' -- -i --no-numa --socket-num=1 --lcore-dma=[lcore32@0000:80:04.0]
	testpmd> start

3. Launch virtio-user with 4K-pages::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 33-34 -n 4 --no-huge -m 1024 --file-prefix=virtio-user --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1 -- -i
	testpmd> set fwd mac
	testpmd> start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

	testpmd> show port stats all

Test Case 2: Basic test vhost/virtio-user packed ring with 4K-pages and cbdma enable
------------------------------------------------------------------------------------
This case uses testpmd Traffic Generator(For example, Trex) to test packed ring when vhost uses the asynchronous enqueue operations with CBDMA channels
in 4k-pages environment. And the mapping between vrings and dsa virtual channels is 1:1.

1. Bind 1 NIC port and 1 CBDMA channel to vfio-pci, as common steps 1.

2. Launch vhost by below command::

	./usertools/dpdk-devbind.py --bind=vfio-pci 0000:af:00.0 0000:80:04.0
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 31-32 -n 4 --no-huge -m 1024 --file-prefix=vhost -a 0000:af:00.0 -a 0000:80:04.0 \
	--vdev 'net_vhost0,iface=/tmp/vhost-net,queues=1,dmas=[txq0]' -- -i --no-numa --socket-num=1 --lcore-dma=[lcore32@0000:80:04.0]
	testpmd> start

3. Launch virtio-user with 4K-pages::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 33-34 -n 4 --no-huge -m 1024 --file-prefix=virtio-user --no-pci \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,packed_vq=1,queues=1 -- -i
	testpmd> set fwd mac
	testpmd> start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

	testpmd> show port stats all

Test Case 3: VM2VM split ring vhost-user/virtio-net 4K-pages and CBDMA enable test with tcp traffic
---------------------------------------------------------------------------------------------------
This case test the function of Vhost tx offload in the topology of vhost-user/virtio-net split ring mergeable path
by verifing the TSO/cksum in the TCP/IP stack when vhost uses the asynchronous enqueue operations with CBDMA channels
in 4k-pages environment.

1. Bind 2 CBDMA channels to vfio-pci, as common steps 1.

2. Launch vhost by below command::

	./usertools/dpdk-devbind.py --bind=vfio-pci 0000:80:04.0 0000:80:04.1
	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30-32 -n 4 --no-huge -m 1024 --file-prefix=vhost -a 0000:80:04.0 -a 0000:80:04.1 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[txq0],dma_ring_size=2048' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas=[txq0],dma_ring_size=2048' \
	--iova=va -- -i --nb-cores=2 --txd=1024 --rxd=1024 --lcore-dma=[lcore31@0000:80:04.0,lcore32@0000:80:04.1]
	testpmd> start

3. Launch VM1 and VM2::

	taskset -c 20,21,22,23,24,25,26,27 /home/QEMU/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_nohuge0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/image/ubuntu2004.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:10.239.251.220:6000-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

	taskset -c 48,49,50,51,52,53,54,55 /home/QEMU/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_nohuge1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/image/ubuntu2004_2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:10.239.251.220:6001-:22 \
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

7. Check 2VMs can receive and send big packets to each other::

	testpmd>  show port xstats all
	Port 0 should have tx packets above 1522
	Port 1 should have rx packets above 1522

Test Case 4: vm2vm vhost/virtio-net split ring multi queues with 4K-pages and cbdma enable
-------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in
vm2vm vhost-user/virtio-net split ring mergeable path when vhost uses the asynchronous enqueue operations with CBDMA channel.
The dynamic change of multi-queues number also test.

1. Bind 16 CBDMA channels to vfio-pci, as common steps 1.

2. Launch vhost by below command::

	./usertools/dpdk-devbind.py --bind=vfio-pci 0000:80:04.0 0000:80:04.1 0000:80:04.2 0000:80:04.3 0000:80:04.4 0000:80:04.5 0000:80:04.6 0000:80:04.7 \
	0000:00:04.0 0000:00:04.1 0000:00:04.2 0000:00:04.3 0000:00:04.4 0000:00:04.5 0000:00:04.6 0000:00:04.7

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-33 -n 4 --no-huge -m 1024 --file-prefix=vhost \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore30@0000:80:04.0,lcore30@0000:80:04.1,lcore30@0000:00:04.2,lcore30@0000:00:04.3,lcore30@0000:00:04.4,lcore30@0000:00:04.5,lcore31@0000:00:04.6,lcore31@0000:00:04.7,lcore32@0000:80:04.0,lcore32@0000:80:04.1,lcore32@0000:80:04.2,lcore32@0000:80:04.3,lcore32@0000:80:04.4,lcore32@0000:80:04.5,lcore32@0000:80:04.6,lcore33@0000:80:04.7]

	testpmd> start


3. Launch VM qemu::

	taskset -c 20,21,22,23,24,25,26,27 /home/QEMU/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/image/ubuntu2004.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:10.239.251.220:6000-:22 \
	-chardev socket,id=char0,path=./vhost-net0,server \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 48,49,50,51,52,53,54,55 /home/QEMU/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_yinan1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/image/ubuntu2004_2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:10.239.251.220:6001-:22 \
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

	Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

8. Quit and relaunch vhost w/ diff CBDMA channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-33 -n 4 --no-huge -m 1024 --file-prefix=vhost \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
	--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore30@0000:80:04.0,lcore30@0000:80:04.1,lcore30@0000:00:04.2,lcore30@0000:00:04.3,lcore31@0000:80:04.0,lcore31@0000:00:04.2,lcore31@0000:00:04.4,lcore31@0000:00:04.5,lcore31@0000:00:04.6,lcore31@0000:00:04.7,lcore32@0000:80:04.1,lcore32@0000:00:04.3,lcore32@0000:80:04.0,lcore32@0000:80:04.1,lcore32@0000:80:04.2,lcore32@0000:80:04.3,lcore32@0000:80:04.4,lcore32@0000:80:04.5,lcore32@0000:80:04.6,lcore33@0000:80:04.7]
	testpmd> start

9. Rerun step 6-7.

10. Quit and relaunch vhost w/o CBDMA channels::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-33 -n 4 --no-huge -m 1024 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=4' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=4' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4
	testpmd> start

11. On VM1, set virtio device::

	ethtool -L ens5 combined 4

12. On VM2, set virtio device::

	ethtool -L ens5 combined 4

13. Scp 1MB file form VM1 to VM2::

	Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

14. Check the iperf performance and compare with CBDMA enable performance, ensure CMDMA enable performance is higher::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

15. Quit and relaunch vhost with 1 queues::

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-33 -n 4 --no-huge -m 1024 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=4' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=4' \
	-- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1
	testpmd> start

16. On VM1, set virtio device::

	ethtool -L ens5 combined 1

17. On VM2, set virtio device::

	ethtool -L ens5 combined 1

18. Scp 1MB file form VM1 to VM2M, check packets can be forwarding success by scp::

	Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

19. Check the iperf performance, ensure queue0 can work from vhost side::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

Test Case 5: vm2vm vhost/virtio-net split packed ring multi queues with 1G/4k-pages and cbdma enable
----------------------------------------------------------------------------------------------------
This case uses iperf and scp to test the payload of large packet (larger than 1MB) is valid after packets forwarding in 
vm2vm vhost-user/virtio-net multi-queues mergeable path when vhost uses the asynchronous enqueue operations with CBDMA
channels. And one virtio-net is split ring, the other is packed ring. The vhost run in 1G hugepages and the virtio-user run in 4k-pages environment.

1. Bind 16 CBDMA channel to vfio-pci, as common steps 1.

2. Launch vhost by below command::

	./usertools/dpdk-devbind.py --bind=vfio-pci 0000:80:04.0 0000:80:04.1 0000:80:04.2 0000:80:04.3 0000:80:04.4 0000:80:04.5 0000:80:04.6 0000:80:04.7 \
	0000:00:04.0 0000:00:04.1 0000:00:04.2 0000:00:04.3 0000:00:04.4 0000:00:04.5 0000:00:04.6 0000:00:04.7

	<dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-33 -n 4 -m 1024 --file-prefix=vhost \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
	-a 0000:80:04.0 -a 0000:80:04.1 -a 0000:80:04.2 -a 0000:80:04.3 -a 0000:80:04.4 -a 0000:80:04.5 -a 0000:80:04.6 -a 0000:80:04.7 \
	--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[txq0;txq1;txq2;txq3;]' \
	--vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[txq0;txq1;txq2;txq3;]' \
	--iova=va -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8 \
	--lcore-dma=[lcore30@0000:80:04.0,lcore30@0000:80:04.1,lcore30@0000:00:04.2,lcore30@0000:00:04.3,lcore31@0000:00:04.4,lcore31@0000:00:04.5,lcore31@0000:00:04.6,lcore31@0000:00:04.7,lcore32@0000:80:04.0,lcore32@0000:80:04.1,lcore32@0000:80:04.2,lcore32@0000:80:04.3,lcore33@0000:80:04.4,lcore33@0000:80:04.5,lcore33@0000:80:04.6,lcore33@0000:80:04.7]
	testpmd> start

3. Launch VM qemu::

	taskset -c 20,21,22,23,24,25,26,27 /home/QEMU/qemu-6.2.0/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_nohuge0,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/image/ubuntu2004.img  \
	-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm1_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:10.239.251.220:6000-:22 \
	-chardev socket,id=char0,path=./vhost-net0 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

	taskset -c 48,49,50,51,52,53,54,55 /home/QEMU/qemu-6.2.0/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 8 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/tmpfs_nohuge1,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/image/ubuntu2004_2.img  \
	-chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
	-monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
	-netdev user,id=nttsip1,hostfwd=tcp:10.239.251.220:6001-:22 \
	-chardev socket,id=char0,path=./vhost-net1 \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,packed=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

4. On VM1, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 8
	ifconfig ens5 1.1.1.2
	arp -s 1.1.1.8 52:54:00:00:00:02

5. On VM2, set virtio device IP and run arp protocal::

	ethtool -L ens5 combined 8
	ifconfig ens5 1.1.1.8
	arp -s 1.1.1.2 52:54:00:00:00:01

6. Scp 1MB file form VM1 to VM2::

	Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

7. Check the iperf performance between two VMs by below commands::

	Under VM1, run: `iperf -s -i 1`
	Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`
