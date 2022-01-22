.. Copyright (c) <2019>, Intel Corporation
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

======================================================
vhost/virtio-user loopback with multi-queues test plan
======================================================

This test plan test loopback multi-queues with split virtqueue mergeable, non-mergeable, vectorized_rx,
inorder mergeable, inorder non-mergeable path, and packed virtqueue mergeable, non-mergeable，inorder mergeable,
inorder non-mergeable, vectorized path. And virtio-user support 8 queues in maximum, check performance could be
linear growth when enable 8 queues and 8 cores, notice cores should in same socket.

Test Case 1: loopback with virtio 1.1 mergeable path using 1 queue and 8 queues
===============================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each RX/TX queue has packets, then quit testpmd::

    testpmd>stop
    testpmd>quit

6. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-9 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac

7. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 10-18 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

8. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

9. Get throughput 10 times and calculate the average throughput，check the throughput of 8 queues is eight times of 1 queue::

    testpmd>show port stats all

Test Case 2: loopback with virtio 1.1 non-mergeable path using 1 queue and 8 queues
===================================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each RX/TX queue has packets, then quit testpmd::

    testpmd>stop
    testpmd>quit

6. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-9 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac

7. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 10-18 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

8. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

9. Get throughput 10 times and calculate the average throughput，check the throughput of 8 queues is eight times of 1 queue::

    testpmd>show port stats all

Test Case 3: loopback with virtio 1.0 inorder mergeable path using 1 queue and 8 queues
=======================================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each RX/TX queue has packets, then quit testpmd::

    testpmd>stop
    testpmd>quit

6. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-9 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac

7. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 10-18 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

8. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

9. Get throughput 10 times and calculate the average throughput，check the throughput of 8 queues is eight times of 1 queue::

    testpmd>show port stats all

Test Case 4: loopback with virtio 1.0 inorder non-mergeable path using 1 queue and 8 queues
===========================================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,mrg_rxbuf=0,in_order=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each RX/TX queue has packets, then quit testpmd::

    testpmd>stop
    testpmd>quit

6. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-9 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac

7. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 10-18 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,mrg_rxbuf=0,in_order=1 \
    -- -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

8. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

9. Get throughput 10 times and calculate the average throughput，check the throughput of 8 queues is eight times of 1 queue::

    testpmd>show port stats all

Test Case 5: loopback with virtio 1.0 mergeable path using 1 queue and 8 queues
===============================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each RX/TX queue has packets, then quit testpmd::

    testpmd>stop
    testpmd>quit

6. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-9 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac

7. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 10-18 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,mrg_rxbuf=1,in_order=0 \
    -- -i --enable-hw-vlan-strip --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

8. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

9. Get throughput 10 times and calculate the average throughput，check the throughput of 8 queues is eight times of 1 queue::

    testpmd>show port stats all

Test Case 6: loopback with virtio 1.0 non-mergeable path using 1 queue and 8 queues
===================================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,mrg_rxbuf=0,in_order=0,vectorized=1 \
    -- -i --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each RX/TX queue has packets, then quit testpmd::

    testpmd>stop
    testpmd>quit

6. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-9 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac

7. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 10-18 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1 \
    -- -i --enable-hw-vlan-strip --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

8. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

9. Get throughput 10 times and calculate the average throughput，check the throughput of 8 queues is eight times of 1 queue::

    testpmd>show port stats all

Test Case 7: loopback with virtio 1.0 vector_rx path using 1 queue and 8 queues
===============================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,mrg_rxbuf=0,in_order=0,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each RX/TX queue has packets, then quit testpmd::

    testpmd>stop
    testpmd>quit

6. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-9 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac

7. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 10-18 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1 \
    -- -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

8. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

9. Get throughput 10 times and calculate the average throughput，check the throughput of 8 queues is eight times of 1 queue::

    testpmd>show port stats all

Test Case 8: loopback with virtio 1.1 inorder mergeable path using 1 queue and 8 queues
=======================================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each RX/TX queue has packets, then quit testpmd::

    testpmd>stop
    testpmd>quit

6. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-9 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac

7. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 10-18 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

8. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

9. Get throughput 10 times and calculate the average throughput，check the throughput of 8 queues is eight times of 1 queue::

    testpmd>show port stats all

Test Case 9: loopback with virtio 1.1 inorder non-mergeable path using 1 queue and 8 queues
===========================================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --rx-offloads=0x10 --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each RX/TX queue has packets, then quit testpmd::

    testpmd>stop
    testpmd>quit

6. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-9 -n 4 --no-pci --vdev 'eth_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac

7. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 10-18 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --rx-offloads=0x10 --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

8. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

9. Get throughput 10 times and calculate the average throughput，check the throughput of 8 queues is eight times of 1 queue::

    testpmd>show port stats all

Test Case 10: loopback with virtio 1.1 vectorized path using 1 queue and 8 queues
=================================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each RX/TX queue has packets, then quit testpmd::

    testpmd>stop
    testpmd>quit

6. Launch testpmd by below command::

    rm -rf vhost-net*
    ./<build_target>/app/dpdk-testpmd -l 1-9 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac

7. Launch virtio-user by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 10-18 \
    --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --nb-cores=8 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

8. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

9. Get throughput 10 times and calculate the average throughput，check the throughput of 8 queues is eight times of 1 queue::

    testpmd>show port stats all
