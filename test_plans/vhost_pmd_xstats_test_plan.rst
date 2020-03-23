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

========================================
vhost PMD Xstats Tests restart test plan
========================================

Description
===========

This test plan will cover the basic vhost pmd xstats test with each path of split ring
and packed ring, includes split virtqueue in-order mergeable, in-order non-mergeable,
mergeable, non-mergeable, vector_rx path test and packed virtqueue in-order mergeable,
in-order non-mergeable, mergeable, non-mergeable path, also cover a stability case. 
Note IXIA or Scapy packes includes 4 CRC bytes and vhost side will remove the CRC when receive packests.

Test flow
=========

TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Test Case 1: xstats test with packed ring mergeable path
========================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Let TG generate send 10000 packets for each packet sizes(64,128,255, 512, 1024, 1523).

4. On host run "show port xstats 1", and check the statistic type and number is correct.
For example: send 1000 packets with 1028B size(includes 4 CRC bytes), the statistic number of tx_size_1024_to_1522_packets and rx_size_1024_to_1522_packets should both 1000.

5. Let TG generate send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct.
For example: send 1000 packets with ucast type, the number of tx_unicast_packets and rx_unicast_packets should both 1000.

Test Case 2: xstats test with packed ring non-mergeable path
============================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Let TG generate send 10000 packets for each packet sizes(64,128,255, 512, 1024, 1523).

4. On host run "show port xstats 1", and check the statistic type and number is correct.

5. Let TG generate send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct.

Test Case 3: xstats stability test with split ring inorder mergeable path 
=========================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Let TG generate send 10000 packets for each packet sizes(64,128,255, 512, 1024, 1523).

4. On host run "show port xstats 1", and check the statistic type and number is correct.

5. Let TG generate send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct.

7.Send packets for 10 minutes with low speed, check the statistic type and number is correct.

Test Case 4: xstats test with split ring inorder non-mergeable path
===================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Let TG generate send 10000 packets for each packet sizes(64,128,255, 512, 1024, 1523).

4. On host run "show port xstats 1", and check the statistic type and number is correct.

5. Let TG generate send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct.

Test Case 5: xstats test with split ring mergeable path
=======================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Let TG generate send 10000 packets for each packet sizes(64,128,255, 512, 1024, 1523).

4. On host run "show port xstats 1", and check the statistic type and number is correct.

5. Let TG generate send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct.

Test Case 6: xstats test with split ring non-mergeable path
===========================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=0,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Let TG generate send 10000 packets for each packet sizes(64,128,255, 512, 1024, 1523).

4. On host run "show port xstats 1", and check the statistic type and number is correct.

5. Let TG generate send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct.

Test Case 7: xstats test with split ring vector_rx path
=======================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=0,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Let TG generate send 10000 packets for each packet sizes(64,128,255, 512, 1024, 1523).

4. On host run "show port xstats 1", and check the statistic type and number is correct.

5. Let TG generate send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct.

Test Case 8: xstats test with packed ring inorder mergeable path
================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Let TG generate send 10000 packets for each packet sizes(64,128,255, 512, 1024, 1523).

4. On host run "show port xstats 1", and check the statistic type and number is correct.

5. Let TG generate send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct.

7.Send packets for 10 minutes with low speed, check the statistic type and number is correct.

Test Case 9: xstats test with packed ring inorder non-mergeable path
====================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

3. Let TG generate send 10000 packets for each packet sizes(64,128,255, 512, 1024, 1523).

4. On host run "show port xstats 1", and check the statistic type and number is correct.

5. Let TG generate send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct.