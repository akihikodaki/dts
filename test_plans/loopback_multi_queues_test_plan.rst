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

=====================================================
vhost/virtio-user loopback with multi-queue test plan
=====================================================

Description
===========

Benchmark vhost/virtio-user loopback multi-queues test with 8 rx/tx paths, virtio-user support 8 queues in maximum.
Includes mergeable, normal, vector_rx, inorder mergeable,
inorder no-mergeable, virtio 1.1 mergeable, virtio 1.1 inorder, virtio 1.1 normal path.

Test Case 1: loopback 2 queues test with virtio 1.1 mergeable path
==================================================================
1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2' -- \
    -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each queue's RX/TX packet numbers::

    testpmd>stop

Test Case 2: loopback 2 queues test with virtio 1.1 normal path
===============================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2' -- \
    -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each queue's RX/TX packet numbers::

    testpmd>stop

Test Case 3: loopback 2 queues test with virtio 1.1 inorder path
================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2' -- \
    -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each queue's RX/TX packet numbers::

    testpmd>stop

Test Case 4: loopback 2 queues test with inorder mergeable path
===============================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2' -- \
    -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each queue's RX/TX packet numbers::

    testpmd>stop

Test Case 5: loopback 2 queues test with inorder no-mergeable path
==================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2' -- \
    -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each queue's RX/TX packet numbers::

    testpmd>stop

Test Case 6: loopback 8 queues test with mergeable path
=======================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -l 2-6 -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 7-11 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=4--rxq=8 --txq=8 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each queue's RX/TX packet numbers::

    testpmd>stop


Test Case 7: loopback 8 queues test with normal path
====================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-6  --socket-mem 1024,1024 --legacy-mem --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    >set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 7-11 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,in_order=0,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each queue's RX/TX packet numbers::

    testpmd>stop

Test Case 8: loopback 8 queues test with vector_rx path
=======================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-6  --socket-mem 1024,1024 --legacy-mem --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=8' -- \
    -i --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    >set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 7-11 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=8,in_order=0,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --rss-ip --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Check each queue's RX/TX packet numbers::

    testpmd>stop
