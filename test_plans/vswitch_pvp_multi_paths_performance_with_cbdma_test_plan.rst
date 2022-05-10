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

========================================================
Vswitch PVP multi-paths performance with CBDMA test plan
========================================================

Description
===========

Benchmark PVP multi-paths performance with CBDMA in vhost sample,
include 10 tx/rx paths: inorder mergeable, inorder non-mergeable,
mergeable, non-mergeable, vectorized_rx, virtio 1.1 inorder mergeable,
virtio 1.1 inorder non-mergeable, virtio 1.1  mergeable, virtio 1.1 non-mergeable,
virtio1.1 vectorized path. Give 1 core for vhost and virtio respectively.
About vswitch sample, a new option --total-num-mbufs is added from dpdk-22.03,
for the user to set larger mbuf pool to avoid launch fail. For example, dpdk-vhost
will fail to launch with a 40G i40e port without setting larger mbuf pool.
For more about vhost switch sample, please refer to the dpdk docs:
http://doc.dpdk.org/guides/sample_app_ug/vhost.html
For virtio-user vdev parameter, you can refer to the dpdk doc:
https://doc.dpdk.org/guides/nics/virtio.html#virtio-paths-selection-and-usage

Prerequisites
=============

Topology
--------

Test flow: TG-->nic-->vswitch-->virtio-user-->vswitch-->nic-->TG

Hardware
--------
Supportted NICs: all except Intel® Ethernet 800 Series that not support VMDQ

Software
--------
Trex:http://trex-tgn.cisco.com/trex/release/v2.26.tar.gz

General set up
--------------
1. Compile DPDK and vhost example::

	# meson <dpdk build dir>  
	# meson configure -Dexamples=vhost <dpdk build dir> 
	# ninja -C <dpdk build dir> -j 110

2. Get the pci device id and DMA device id of DUT.

For example, 0000:18:00.0 is pci device id, 0000:00:04.0 is DMA device id::

	<dpdk dir># ./usertools/dpdk-devbind.py -s

	Network devices using kernel driver
	===================================
	0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci
	
	DMA devices using kernel driver
	===============================
	0000:00:04.0 'Sky Lake-E CBDMA Registers 2021' drv=ioatdma unused=vfio-pci

Test case
=========	

Common steps
------------
1. Bind one physical port and one CBDMA port to vfio-pci::

	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
	<dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DMA device id>
	
	For example::
	./usertools/dpdk-devbind.py -b vfio-pci 0000:00:18.0
	./usertools/dpdk-devbind.py -b vfio-pci 0000:00:04.0

2. Inject different size of packets to NIC by traffic generator::

	The packet size include [64, 128, 256, 512, 1024, 1518], and the format of packet is as follows.
    +-------------+-------------+-------------+-------------+
    | MAC         | MAC         | IPV4        | IPV4        |
    | Src address | Dst address | Src address | Dst address |
    |-------------|-------------|-------------|-------------|
    | Any MAC     | Virtio mac  | Any IP      | Any IP      |
    +-------------+-------------+-------------+-------------+
	All the packets in this test plan use the Virtio mac:00:11:22:33:44:10.

Test Case 1: Vswitch PVP split ring inorder mergeable path performance with CBDMA
---------------------------------------------------------------------------------
This case uses Vswitch and Traffic generator(For example, Trex) to test performance of split ring inorder mergeable path with CBDMA. 

1. Bind one physical port and one CBDMA port to vfio-pci as common step 1.

2. Launch dpdk-vhost by below command::

	<dpdk dir>#./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:00:04.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0] --total-num-mbufs 600000

3. Launch virtio-user with split ring inorder mergeable path::

	<dpdk dir>#./<dpdk build dir>/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,packed_vq=0,mrg_rxbuf=1,in_order=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1 

4. Send packets from virtio-user to let vswitch know the mac addr::

	testpmd> set fwd mac
	testpmd> start tx_first
	testpmd> stop
	testpmd> start

5. Send packets by traffic generator as common step 2, and check the throughput with below command::

	testpmd> show port stats all

Test Case 2: Vswitch PVP split ring inorder non-mergeable path performance with CBDMA
-------------------------------------------------------------------------------------
This case uses Vswitch and Traffic generator(For example, Trex) to test performance of split ring inorder non-mergeable path with CBDMA.

1. Bind one physical port and one CBDMA port to vfio-pci as common step 1.

2. Launch dpdk-vhost by below command::

	<dpdk dir>#./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:00:04.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0] --total-num-mbufs 600000

3. Launch virtio-user with split ring non-mergeable path::

	<dpdk dir>#./<dpdk build dir>/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1 

4. Send packets from virtio-user to let vswitch know the mac addr::

	testpmd> set fwd mac
	testpmd> start tx_first
	testpmd> stop
	testpmd> start

5. Send packets by traffic generator as common step 2, and check the throughput with below command::

	testpmd> show port stats all
	
Test Case 3: Vswitch PVP split ring mergeable path performance with CBDMA
-------------------------------------------------------------------------
This case uses Vswitch and Traffic generator(For example, Trex) to test performance of split ring mergeable path with CBDMA.

1. Bind one physical port and one CBDMA port to vfio-pci as common step 1.

2. Launch dpdk-vhost by below command::

	<dpdk dir>#./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:00:04.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0] --total-num-mbufs 600000

3. Launch virtio-user with split ring mergeable path::

	<dpdk dir>#./<dpdk build dir>/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,packed_vq=0,mrg_rxbuf=1,in_order=0 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1 

4. Send packets from virtio-user to let vswitch know the mac addr::

	testpmd> set fwd mac
	testpmd> start tx_first
	testpmd> stop
	testpmd> start

5. Send packets by traffic generator as common step 2, and check the throughput with below command::

	testpmd> show port stats all	
	
Test Case 4: Vswitch PVP split ring non-mergeable path performance with CBDMA
-----------------------------------------------------------------------------
This case uses Vswitch and Traffic generator(For example, Trex) to test performance of split ring non-mergeable path with CBDMA.

1. Bind one physical port and one CBDMA port to vfio-pci as common step 1.

2. Launch dpdk-vhost by below command::

	<dpdk dir>#./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:00:04.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0] --total-num-mbufs 600000

3. Launch virtio-user with split ring non-mergeable path::

	<dpdk dir>#./<dpdk build dir>/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=0 \
	-- -i --enable-hw-vlan-strip --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1 

4. Send packets from virtio-user to let vswitch know the mac addr::

	testpmd> set fwd mac
	testpmd> start tx_first
	testpmd> stop
	testpmd> start

5. Send packets by traffic generator as common step 2, and check the throughput with below command::

	testpmd> show port stats all		

Test Case 5: Vswitch PVP split ring vectorized path performance with CBDMA
--------------------------------------------------------------------------
This case uses Vswitch and Traffic generator(For example, Trex) to test performance of split ring vectorized path with CBDMA.

1. Bind one physical port and one CBDMA port to vfio-pci as common step 1.

2. Launch dpdk-vhost by below command::

	<dpdk dir>#./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:00:04.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0] --total-num-mbufs 600000

3. Launch virtio-user with split ring vectorized path::

	<dpdk dir>#./<dpdk build dir>/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=1,vectorized=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1 

4. Send packets from virtio-user to let vswitch know the mac addr::

	testpmd> set fwd mac
	testpmd> start tx_first
	testpmd> stop
	testpmd> start

5. Send packets by traffic generator as common step 2, and check the throughput with below command::

	testpmd> show port stats all		
	
	
Test Case 6: Vswitch PVP packed ring inorder mergeable path performance with CBDMA
----------------------------------------------------------------------------------
This case uses Vswitch and Traffic generator(For example, Trex) to test performance of packed ring inorder mergeable path with CBDMA.

1. Bind one physical port and one CBDMA port to vfio-pci as common step 1.

2. Launch dpdk-vhost by below command::

	<dpdk dir>#./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:00:04.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0] --total-num-mbufs 600000

3. Launch virtio-user with packed ring inorder mergeable path::

	<dpdk dir>#./<dpdk build dir>/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1 

4. Send packets from virtio-user to let vswitch know the mac addr::

	testpmd> set fwd mac
	testpmd> start tx_first
	testpmd> stop
	testpmd> start

5. Send packets by traffic generator as common step 2, and check the throughput with below command::

	testpmd> show port stats all

Test Case 7: Vswitch PVP packed ring inorder non-mergeable path performance with CBDMA
--------------------------------------------------------------------------------------
This case uses Vswitch and Traffic generator(For example, Trex) to test performance of packed ring inorder non-mergeable path with CBDMA.

1. Bind one physical port and one CBDMA port to vfio-pci as common step 1.

2. Launch dpdk-vhost by below command::

	<dpdk dir>#./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:00:04.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0] --total-num-mbufs 600000

3. Launch virtio-user with packed ring inorder non-mergeable path::

	<dpdk dir>#./<dpdk build dir>/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1 

4. Send packets from virtio-user to let vswitch know the mac addr::

	testpmd> set fwd mac
	testpmd> start tx_first
	testpmd> stop
	testpmd> start

5. Send packets by traffic generator as common step 2, and check the throughput with below command::

	testpmd> show port stats all
	
Test Case 8: Vswitch PVP packed ring mergeable path performance with CBDMA
--------------------------------------------------------------------------
This case uses Vswitch and Traffic generator(For example, Trex) to test performance of packed ring mergeable path with CBDMA.

1. Bind one physical port and one CBDMA port to vfio-pci as common step 1.

2. Launch dpdk-vhost by below command::

	<dpdk dir>#./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:00:04.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0] --total-num-mbufs 600000

3. Launch virtio-user with packed ring mergeable path::

	<dpdk dir>#./<dpdk build dir>/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Send packets from virtio-user to let vswitch know the mac addr::

	testpmd> set fwd mac
	testpmd> start tx_first
	testpmd> stop
	testpmd> start

5. Send packets by traffic generator as common step 2, and check the throughput with below command::

	testpmd> show port stats all	
	
Test Case 9: Vswitch PVP packed ring non-mergeable path performance with CBDMA
------------------------------------------------------------------------------
This case uses Vswitch and Traffic generator(For example, Trex) to test performance of packed ring non-mergeable path with CBDMA.

1. Bind one physical port and one CBDMA port to vfio-pci as common step 1.

2. Launch dpdk-vhost by below command::

	<dpdk dir>#./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:00:04.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0] --total-num-mbufs 600000

3. Launch virtio-user with packed ring non-mergeable path::

	<dpdk dir>#./<dpdk build dir>/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0  \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=0 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1 

4. Send packets from virtio-user to let vswitch know the mac addr::

	testpmd> set fwd mac
	testpmd> start tx_first
	testpmd> stop
	testpmd> start

5. Send packets by traffic generator as common step 2, and check the throughput with below command::

	testpmd> show port stats all		

Test Case 10: Vswitch PVP packed ring vectorized path performance with CBDMA
----------------------------------------------------------------------------
This case uses Vswitch and Traffic generator(For example, Trex) to test performance of packed ring vectorized path with CBDMA.

1. Bind one physical port and one CBDMA port to vfio-pci as common step 1.

2. Launch dpdk-vhost by below command::

	<dpdk dir>#./<dpdk build dir>/examples/dpdk-vhost -l 2-3 -n 4 -a 0000:18:00.0 -a 0000:00:04.0 \
	-- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 --socket-file /tmp/vhost-net --dmas [txd0@0000:00:04.0] --total-num-mbufs 600000

3. Launch virtio-user with packed ring vectorized path::

	<dpdk dir>#./<dpdk build dir>/app/dpdk-testpmd -l 5-6 -n 4 --no-pci --file-prefix=testpmd0 --force-max-simd-bitwidth=512 \
	--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
	-- -i --rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1

4. Send packets from virtio-user to let vswitch know the mac addr::

	testpmd> set fwd mac
	testpmd> start tx_first
	testpmd> stop
	testpmd> start

5. Send packets by traffic generator as common step 2, and check the throughput with below command::

	testpmd> show port stats all		
