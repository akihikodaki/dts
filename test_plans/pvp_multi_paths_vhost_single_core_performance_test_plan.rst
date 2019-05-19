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


========================================================
vhost/virtio pvp multi-paths vhost single core test plan
========================================================

Description
===========

Benchmark PVP vhost single core performance with 8 tx/rx paths.
Includes mergeable, normal, vector_rx, inorder mergeable,
inorder no-mergeable, virtio 1.1 mergeable, virtio 1.1 inorder, virtio 1.1 normal path.
Give 2 cores for virtio and 1 core for vhost, set io fwd at virtio side to lower the virtio workload.

Test flow
=========

TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Test Case 1: vhost single core performance test with virtio 1.1 mergeable path
==============================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -l 7-9 -n 4  --socket-mem 1024,1024 --legacy-mem --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 2: vhost single core performance test with virtio 1.1 normal path
===========================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -l 7-9 -n 4  --socket-mem 1024,1024 --legacy-mem --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 3: vhost single core performance test with inorder mergeable path
===========================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -l 7-9 -n 4  --socket-mem 1024,1024 --legacy-mem --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,in_order=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 4: vhost single core performance test with inorder no-mergeable path
==============================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -l 7-9 -n 4  --socket-mem 1024,1024 --legacy-mem --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 5: vhost single core performance test with mergeable path
===================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -l 7-9 -n 4  --socket-mem 1024,1024 --legacy-mem --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 6: vhost single core performance test with normal path
================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -l 7-9 -n 4  --socket-mem 1024,1024 --legacy-mem --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,in_order=0,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 7: vhost single core performance test with vector_rx path
===================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -l 7-9 -n 4  --socket-mem 1024,1024 --legacy-mem --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,in_order=0,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 8: vhost single core performance test with virtio 1.1 inorder path
============================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -l 7-9 -n 4  --socket-mem 1024,1024 --legacy-mem --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.
