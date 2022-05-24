.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

========================================================
vhost/virtio pvp multi-paths vhost single core test plan
========================================================

Benchmark PVP virtio single core performance with 10 tx/rx paths. Includes mergeable, non-mergeable, vectorized_rx,
inorder mergeable, inorder non-mergeable, virtio 1.1 mergeable, virtio 1.1 non-mergeable，virtio 1.1 inorder
mergeable, virtio 1.1 inorder non-mergeable, virtio1.1 vectorized path.
Give 2 cores for virtio and 1 core for vhost, set io fwd at virtio side to lower the virtio workload.

Test flow
=========

TG --> NIC --> Virtio --> Vhost --> Virtio --> NIC --> TG

Test Case 1: vhost single core performance test with virtio 1.1 mergeable path
==============================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-9 -n 4 --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 2: vhost single core performance test with virtio 1.1 non-mergeable path
==================================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-9 -n 4 --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 3: vhost single core performance test with inorder mergeable path
===========================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-9 -n 4 --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,in_order=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 4: vhost single core performance test with inorder non-mergeable path
===============================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-9 -n 4 --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 5: vhost single core performance test with mergeable path
===================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-9 -n 4 --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 6: vhost single core performance test with non-mergeable path
=======================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-9 -n 4 --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 7: vhost single core performance test with vectorized_rx path
=======================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-9 -n 4 --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 8: vhost single core performance test with virtio 1.1 inorder mergeable path
======================================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-9 -n 4 --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 9: vhost single core performance test with virtio 1.1 inorder non-mergeable path
==========================================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-9 -n 4 --file-prefix=virtio \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=0 \
    -- -i --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.

Test Case 10: vhost single core performance test with virtio 1.1 vectorized path
================================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-9 -n 4 --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --rss-ip --nb-cores=2 --txd=1024 --rxd=1024
    >set fwd io
    >start

3. Send packet with packet generator with different packet size, check the throughput.