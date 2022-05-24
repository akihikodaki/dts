.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

==================================================
vhost/virtio pvp multi-paths performance test plan
==================================================

Benchmark PVP multi-paths performance with 10 tx/rx paths. Includes mergeable, non-mergeable, vectorized_rx,
inorder mergeable, inorder non-mergeable, virtio 1.1 mergeable, virtio 1.1 non-mergeable，virtio 1.1 inorder
mergeable, virtio 1.1 inorder non-mergeable, virtio1.1 vectorized path. Give 1 core for vhost and virtio respectively.
Packed ring vectorized path need:

    AVX512F and required extensions are supported by compiler and host
    VERSION_1 and IN_ORDER features are negotiated
    mergeable feature is not negotiated
    LRO offloading is disabled

Split ring vectorized rx path need:
    mergeable and IN_ORDER features are not negotiated
    LRO, chksum and vlan strip offloadings are disabled

Test flow
=========

TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Test Case 1: pvp test with virtio 1.1 mergeable path
====================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 2: pvp test with virtio 1.1 non-mergeable path
========================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 3: pvp test with inorder mergeable path
=================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 4: pvp test with inorder non-mergeable path
=====================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 5: pvp test with mergeable path
=========================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 6: pvp test with non-mergeable path
=============================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --rx-offloads=0x10 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 7: pvp test with vectorized_rx path
=============================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 8: pvp test with virtio 1.1 inorder mergeable path
============================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 9: pvp test with virtio 1.1 inorder non-mergeable path
================================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=1 \
    -- -i --rx-offloads=0x10 --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 10: pvp test with virtio 1.1 vectorized path
======================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all
