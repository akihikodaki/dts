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

==========================================================
DMA-accelerated Tx operations for vhost-user PMD test plan
==========================================================

Overview
--------

This feature supports to offload large data movement in vhost enqueue operations
from the CPU to the I/OAT(a DMA engine in Intel's processor) device for every queue.
In addition, a queue can only use one I/OAT device, and I/OAT devices cannot be shared
among vhost ports and queues. That is, an I/OAT device can only be used by one queue at
a time. DMA devices(e.g.,CBDMA) used by queues are assigned by users; for a queue without
assigning a DMA device, the PMD will leverages librte_vhost to perform vhost enqueue
operations. Moreover, users cannot enable I/OAT acceleration for live-migration. Large
copies are offloaded from the CPU to the DMA engine in an asynchronous manner. The CPU
just submits copy jobs to the DMA engine and without waiting for DMA copy completion;
there is no CPU intervention during DMA data transfer. By overlapping CPU
computation and DMA copy, we can save precious CPU cycles and improve the overall
throughput for vhost-user PMD based applications, like OVS. Due to startup overheads
associated with DMA engines, small copies are performed by the CPU.
DPDK 21.11 adds vfio support for DMA device in vhost. When DMA devices are bound to
vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping
may exceed IOMMU's max capability, better to use 1G guest hugepage.

We introduce a new vdev parameter to enable DMA acceleration for Tx operations of queues:
- dmas: This parameter is used to specify the assigned DMA device of a queue.

Here is an example:
./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 \
--vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas=[txq0@0000:00:04.0] \
--iova=va -- -i'

Test Case 1: PVP split ring all path vhost enqueue operations with cbdma
========================================================================

Packet pipeline:
================
TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

1. Bind 1 CBDMA port and 1 NIC port to vfio-pci, then launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas=[txq0@0000:00:04.0]' \
    --iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

2. Launch virtio-user with inorder mergeable path::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send imix packets [64,1518] from packet generator, check the throughput can get expected data, restart vhost port and send imix pkts again, check get same throuhput::

    testpmd>show port stats all
    testpmd>stop
    testpmd>start
    testpmd>show port stats all

4. Relaunch virtio-user with mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,queues=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

5. Relaunch virtio-user with inorder non-mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

6. Relaunch virtio-user with non-mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,queues=1 \
    -- -i --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

7. Relaunch virtio-user with vector_rx path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,vectorized=1,queues=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

8. Quit all testpmd and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas=[txq0@0000:00:04.0]' \
    --iova=pa -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

9. Rerun steps 2-7.

Test Case 2: PVP split ring dynamic queue number vhost enqueue operations with cbdma
=====================================================================================

1. Bind 8 CBDMA ports and 1 NIC port to vfio-pci, then launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1' \
    --iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 30-31 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=8,server=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

3. Send imix packets[64,1518] from packet generator with random ip, check perforamnce can get target.

4. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

5. Quit and relaunch vhost with 4 queues w/ cbdma and 4 queues w/o cbdma::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1;txq2@0000:00:04.2;txq3@0000:00:04.3]' \
    --iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

6. Send imix packets[64,1518] from packet generator with random ip, check perforamnce can get target.

7. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

8. Quit and relaunch vhost with 8 queues w/ cbdma::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1;txq2@0000:00:04.2;txq3@0000:00:04.3;txq4@0000:00:04.4;txq5@0000:00:04.5;txq6@0000:00:04.6;txq7@0000:00:04.7]' \
    --iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

9. Send imix packets[64,1518] from packet generator with random ip, check perforamnce can get target.

10. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

11. Quit and relaunch vhost with iova=pa, 6 queues w/ cbdma and 2 queues w/o cbdma::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1;txq2@0000:00:04.2;txq3@0000:00:04.3;txq4@0000:00:04.4;txq5@0000:00:04.5]' \
	--iova=pa -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	>set fwd mac
	>start

12. Send imix packets[64,1518] from packet generator with random ip, check perforamnce can get target.

13. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

Test Case 3: PVP packed ring all path vhost enqueue operations with cbdma
=========================================================================

Packet pipeline:
================
TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

1. Bind 1 CBDMA port and 1 NIC port to vfio-pci, then launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas=[txq0@0000:80:04.0]' \
    --iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

2. Launch virtio-user with inorder mergeable path::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=1,packed_vq=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send imix packets [64,1518] from packet generator, check the throughput can get expected data, restart vhost port and send imix pkts again, check get same throuhput::

    testpmd>show port stats all
    testpmd>stop
    testpmd>start
    testpmd>show port stats all

4. Relaunch virtio-user with mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,queues=1,packed_vq=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

5. Relaunch virtio-user with inorder non-mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=1,packed_vq=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

6. Relaunch virtio-user with non-mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,queues=1,packed_vq=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

7. Relaunch virtio-user with vectorized path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queues=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

8. Relaunch virtio-user with vectorized path and ring size is not power of 2, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queues=1,queue_size=1025 \
    -- -i --nb-cores=1 --txd=1025 --rxd=1025
    >set fwd mac
    >start

9. Quit all testpmd and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas=[txq0@0000:80:04.0]' \
    --iova=pa -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

10. Rerun steps 2-8.

Test Case 4: PVP packed ring dynamic queue number vhost enqueue operations with cbdma
=====================================================================================

1. Bind 8 CBDMA ports and 1 NIC port to vfio-pci, then launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1' \
    --iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 30-31 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,queues=8,server=1,packed_vq=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

3. Send imix packets from packet generator with random ip, check perforamnce can get target.

4. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

5. Quit and relaunch vhost with 4 queues w/ cbdma and 4 queues w/o cbdma::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1;txq2@0000:80:04.2;txq3@0000:80:04.3]' \
    --iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

6. Send imix packets from packet generator with random ip, check perforamnce can get target.

7. Stop vhost port, check vhost RX and TX direction both exist packtes in 4 queues from vhost log.

8. Quit and relaunch vhost with 8 queues w/ cbdma::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1;txq2@0000:80:04.2;txq3@0000:80:04.3;txq4@0000:80:04.4;txq5@0000:80:04.5;txq6@0000:80:04.6;txq7@0000:80:04.7]' \
    --iova=va -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

9. Send imix packets from packet generator with random ip, check perforamnce can get target.

10. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

11. Quit and relaunch vhost with iova=pa, 6 queues w/ cbdma and 2 queues w/o cbdma::

	./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29 --file-prefix=vhost \
	--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1;txq2@0000:80:04.2;txq3@0000:80:04.3;txq4@0000:80:04.4;txq5@0000:80:04.5]' \
	--iova=pa -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
	>set fwd mac
	>start

12. Send imix packets from packet generator with random ip, check perforamnce can get target.

13. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

Test Case 5: loopback split ring large chain packets stress test with cbdma enqueue
====================================================================================

Packet pipeline:
================
Vhost <--> Virtio

1. Bind 1 CBDMA channel to vfio-pci and launch vhost::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0@0000:00:04.0]' \
    --iova=va -- -i --nb-cores=1 --mbuf-size=65535

2. Launch virtio and start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4  --file-prefix=testpmd0 --no-pci  \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1, \
    mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048 \
    -- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
    >start

3. Send large packets from vhost, check virtio can receive packets::

    testpmd> vhost enable tx all
    testpmd> set txpkts 65535,65535,65535,65535,65535
    testpmd> start tx_first 32
    testpmd> show port stats all

4. Quit all testpmd and relaunch vhost with iova=pa::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0@0000:00:04.0]' \
    --iova=pa -- -i --nb-cores=1 --mbuf-size=65535

5. Rerun steps 2-3.

Test Case 6: loopback packed ring large chain packets stress test with cbdma enqueue
====================================================================================

Packet pipeline:
================
Vhost <--> Virtio

1. Bind 1 CBDMA channel to vfio-pci and launch vhost::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0@0000:00:04.0]' \
    --iova=va -- -i --nb-cores=1 --mbuf-size=65535

2. Launch virtio and start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4  --file-prefix=testpmd0 --no-pci  \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1, \
    mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048 \
    -- -i --rxq=1 --txq=1 --txd=2048 --rxd=2048 --nb-cores=1
    >start

3. Send large packets from vhost, check virtio can receive packets::

    testpmd> vhost enable tx all
    testpmd> set txpkts 65535,65535,65535,65535,65535
    testpmd> start tx_first 32
    testpmd> show port stats all

4. Quit all testpmd and relaunch vhost with iova=pa::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net0,queues=1,dmas=[txq0@0000:00:04.0]' --iova=pa -- -i --nb-cores=1 --mbuf-size=65535

5. Rerun steps 2-3.
