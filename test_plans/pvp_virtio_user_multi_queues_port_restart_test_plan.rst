.. Copyright (c) <2020>, Intel Corporation
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

==================================================================
vhost/virtio-user pvp with multi-queues and port restart test plan
==================================================================

Description
===========

This test plan test vhost/virtio-user pvp multi-queues with split virtqueue
and packed virtqueue different rx/tx paths, includes split virtqueue in-order
mergeable, in-order non-mergeable, mergeable, non-mergeable, vector_rx path test,
and packed virtqueue in-order mergeable, in-order non-mergeable, mergeable,
non-mergeable and vectorized path, also cover port restart test with each path.

Test flow
=========

TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Test Case 1: pvp 2 queues test with packed ring mergeable path
===============================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=255 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2 --txd=255 --rxd=255
    >set fwd mac
    >start

3. Send different ip packets with packet generator, check the throughput with below command::

    testpmd>show port stats all

4. Check each queue's rx/tx packet numbers::

    testpmd>stop

5. Port restart 100 times by below command and re-calculate the average througnput,verify the throughput is not zero after port restart::

    testpmd>stop
    testpmd>start
    ...
    testpmd>stop
    testpmd>show port stats all
    testpmd>start
    testpmd>show port stats all

Test Case 2: pvp 2 queues test with packed ring non-mergeable path
==================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=255 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2 --txd=255 --rxd=255
    >set fwd mac
    >start

3. Send different ip packets with packet generator, check the throughput with below command::

    testpmd>show port stats all

4. Check each queue's RX/TX packet numbers::

    testpmd>stop

5. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 3: pvp 2 queues test with split ring inorder mergeable path
=====================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Send different ip packets with packet generator, check the throughput with below command::

    testpmd>show port stats all

4. Check each queue's RX/TX packet numbers::

    testpmd>stop

5. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 4: pvp 2 queues test with split ring inorder non-mergeable path
==========================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=1,mrg_rxbuf=0,vectorized=1 \
    -- -i --rx-offloads=0x10 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Send different ip packets with packet generator, check the throughput with below command::

    testpmd>show port stats all

4. Check each queue's RX/TX packet numbers::

    testpmd>stop

5. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 5: pvp 2 queues test with split ring mergeable path
=============================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Send different ip packets with packet generator, check the throughput with below command::

    testpmd>show port stats all

4. Check each queue's RX/TX packet numbers::

    testpmd>stop

5. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 6: pvp 2 queues test with split ring non-mergeable path
=================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Send different ip packets with packet generator, check the throughput with below command::

    testpmd>show port stats all

4. Check each queue's RX/TX packet numbers::

    testpmd>stop

5. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 7: pvp 2 queues test with split ring vector_rx path
=============================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --tx-offloads=0x0 --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Send different ip packets with packet generator, check the throughput with below command::

    testpmd>show port stats all

4. Check each queue's RX/TX packet numbers::

    testpmd>stop

5. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 8: pvp 2 queues test with packed ring inorder mergeable path
======================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=255 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2 --txd=255 --rxd=255
    >set fwd mac
    >start

3. Send different ip packets with packet generator, check the throughput with below command::

    testpmd>show port stats all

4. Check each queue's RX/TX packet numbers::

    testpmd>stop

5. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 9: pvp 2 queues test with packed ring inorder non-mergeable path
===========================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=255 \
    -- -i --rx-offloads=0x10 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2 --txd=255 --rxd=255
    >set fwd mac
    >start

3. Send different ip packets with packet generator, check the throughput with below command::

    testpmd>show port stats all

4. Check each queue's RX/TX packet numbers::

    testpmd>stop

5. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 10: pvp 2 queues test with packed ring vectorized path
================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=255 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2 --txd=255 --rxd=255
    >set fwd mac
    >start

3. Send different ip packets with packet generator, check the throughput with below command::

    testpmd>show port stats all

4. Check each queue's RX/TX packet numbers::

    testpmd>stop

5. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all
