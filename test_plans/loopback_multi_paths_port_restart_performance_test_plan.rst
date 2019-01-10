.. Copyright (c) <2010-2017>, Intel Corporation
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
Loopback multi-paths and port restart Tests
===========================================


Description
===========

Benchmark vhost/virtio-user loopback performance for 7 RX/TX PATHs.
Includes Mergeable, Normal, Vector_RX, Inorder mergeable,
Inorder no-mergeable, Virtio 1.1 mergeable, Virtio 1.1 no-mergeable Path.
Also cover port restart test with each path.

Test Case 1: vhost/virtio-user loopback test with Virtio 1.1 mergeable path
===========================================================================

1. Not bind nic port to igb_uio, launch vhost testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32
    testpmd>start

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Port restart by below command and re-calculate the average througnput::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start
    testpmd>show port stats all


Test Case 2: vhost/virtio-user loopback test with Virtio 1.1 no-mergeable path
===========================================================================

1. Not bind nic port to igb_uio, launch vhost testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32
    testpmd>start

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Port restart by below command and re-calculate the average througnput::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start
    testpmd>show port stats all

Test Case 3: vhost/virtio-user loopback test with Inorder mergeable path
===========================================================================

1. Not bind nic port to igb_uio, launch vhost testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32
    testpmd>start

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Port restart by below command and re-calculate the average througnput::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start
    testpmd>show port stats all

Test Case 4: vhost/virtio-user loopback test with Inorder no-mergeable path
===========================================================================

1. Not bind nic port to igb_uio, launch vhost testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32
    testpmd>start

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Port restart by below command and re-calculate the average througnput::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start
    testpmd>show port stats all

Test Case 5: vhost/virtio-user loopback test with Mergeable path
===========================================================================

1. Not bind nic port to igb_uio, launch vhost testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32
    testpmd>start

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Port restart by below command and re-calculate the average througnput::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start
    testpmd>show port stats all


Test Case 6: vhost/virtio-user loopback test with Normal path
===========================================================================

1. Not bind nic port to igb_uio, launch vhost testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32
    testpmd>start

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Port restart by below command and re-calculate the average througnput::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start
    testpmd>show port stats all

Test Case 7: vhost/virtio-user loopback test with Vector_RX path
===========================================================================

1. Not bind nic port to igb_uio, launch vhost testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 128, 256, 512, 1024, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32
    testpmd>start

4. Get throughput 10 times and calculate the average throughput::

    testpmd>show port stats all

5. Port restart by below command and re-calculate the average througnput::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start
    testpmd>show port stats all
