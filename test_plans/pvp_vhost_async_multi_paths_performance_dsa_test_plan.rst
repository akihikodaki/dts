.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2023 Intel Corporation

==================================================================
PVP vhost/virtio multi-paths async data-path performance test plan
==================================================================

Benchmark PVP multi-paths performance with 10 tx/rx paths when vhost uses the asynchronous operation. Includes mergeable, 
non-mergeable, vectorized_rx, inorder mergeable, inorder non-mergeable, packed ring mergeable, packed ring non-mergeable，
packed ring inorder mergeable, packed ring inorder non-mergeable, virtio1.1 vectorized path. Give 1 core for vhost and virtio 
respectively. Packed ring vectorized path need:

    AVX512 and required extensions are supported by compiler and host
    VERSION_1 and IN_ORDER features are negotiated
    mergeable feature is not negotiated
    LRO offloading is disabled

Split ring vectorized rx path need:
    mergeable and IN_ORDER features are not negotiated
    LRO, chksum and vlan strip offloadings are disabled

Test flow
=========

TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Test Case 1: pvp vhost async test with split ring inorder mergeable path using IDXD kernel driver
-------------------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 1wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 2: pvp vhost async test with split ring inorder non-mergeable path using IDXD kernel driver
-----------------------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 1wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4 -a 0000:27:00.0 -a wq0.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 3: pvp vhost async test with split ring mergeable path using IDXD kernel driver
-----------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 1wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4 -a 0000:27:00.0 -a wq0.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 4: pvp vhost async test with split ring non-mergeable path using IDXD kernel driver
---------------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 1wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4 -a 0000:27:00.0 -a wq0.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --rx-offloads=0x10 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 5: pvp vhost async test with split ring vectorized path using IDXD kernel driver
------------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 1wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4 -a 0000:27:00.0 -a wq0.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 6: pvp vhost async test with packed ring inorder mergeable path using IDXD kernel driver
--------------------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 1wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a wq0.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 7: pvp vhost async test with packed ring inorder non-mergeable path using IDXD kernel driver
------------------------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 1wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a wq0.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=1 \
    -- -i --rx-offloads=0x10 --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 8: pvp vhost async test with packed ring mergeable path using IDXD kernel driver
------------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 1wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a wq0.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 9: pvp vhost async test with packed ring non-mergeable path using IDXD kernel driver
----------------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 1wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a wq0.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 10: pvp vhost async test with packed ring vectorized path using IDXD kernel driver
--------------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 1wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a wq0.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 11: pvp vhost async test with split ring inorder mergeable path using vfio-pci driver
-----------------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0 0000:6f:01.0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a 0000:6f:01.0,max_queues=2 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 12: pvp vhost async test with split ring inorder non-mergeable path using vfio-pci driver
---------------------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0 0000:6f:01.0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a 0000:6f:01.0,max_queues=2 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 13: pvp vhost async test with split ring mergeable path using vfio-pci driver
---------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0 0000:6f:01.0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a 0000:6f:01.0,max_queues=2 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 14: pvp vhost async test with split ring non-mergeable path using vfio-pci driver
-------------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0 0000:6f:01.0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a 0000:6f:01.0,max_queues=2 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --rx-offloads=0x10 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 15: pvp vhost async test with split ring vectorized_rx path using vfio-pci driver
-------------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0 0000:6f:01.0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a 0000:6f:01.0,max_queues=2 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 16: pvp vhost async test with packed ring inorder mergeable path using vfio-pci driver
------------------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0 0000:6f:01.0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a 0000:6f:01.0,max_queues=2 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 17: pvp vhost async test with packed ring inorder non-mergeable path using vfio-pci driver
----------------------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0 0000:6f:01.0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a 0000:6f:01.0,max_queues=2 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=1 \
    -- -i --rx-offloads=0x10 --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 18: pvp vhost async test with packed ring mergeable path using vfio-pci driver
----------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0 0000:6f:01.0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a 0000:6f:01.0,max_queues=2 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 19: pvp vhost async test with packed ring non-mergeable path using vfio-pci driver
--------------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0 0000:6f:01.0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a 0000:6f:01.0,max_queues=2 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case 20: pvp vhost async test with packed ring vectorized path using vfio-pci driver
-----------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:27:00.0 0000:6f:01.0

2. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 -a 0000:27:00.0 -a 0000:6f:01.0,max_queues=2 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all
