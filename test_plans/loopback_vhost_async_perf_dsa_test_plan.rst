.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2023 Intel Corporation

===========================================================
Loopback vhost/virtio multi-paths async data-path test plan
===========================================================

Benchmark vhost/virtio-user loopback test with 10 tx/rx paths when vhost uses the asynchronous operation.
Includes split ring mergeable, non-mergeable, vector_rx, inorder mergeable,
inorder non-mergeable, packed ring mergeable, packed ring non-mergeable，
packed ring inorder mergeable, packed ring inorder non-mergeable path and vectorized path.

Test case
=========

Common steps
------------

1. Bind 1 dsa device to idxd, then generate 1wq by below command::

    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Bind 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b idxd 0000:6f:01.0

Test Case 1: loopback vhost async test with split ring inorder mergeable path using IDXD kernel driver
------------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 --no-pci --file-prefix=vhost \
    -    -vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different pac    ket length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 2: loopback vhost async test with split ring inorder non-mergeable path using IDXD kernel driver
----------------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4  --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 3: loopback vhost async test with split ring mergeable path using IDXD kernel driver
----------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 4: loopback vhost async test with split ring non-mergeable path using IDXD kernel driver
--------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 5: loopback vhost async test with split ring vectorized path using IDXD kernel driver
-----------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 6: loopback vhost async test with packed ring inorder mergeable path using IDXD kernel driver
-------------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 7: loopback vhost async test with packed ring inorder non-mergeable path using IDXD kernel driver
-----------------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 8: loopback vhost async test with packed ring mergeable path using IDXD kernel driver
-----------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 9: loopback vhost async test with packed ring non-mergeable path using IDXD kernel driver
---------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 10: loopback vhost async test with packed ring vectorized path using IDXD kernel driver
-------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=0,vectorized=1 \
    -- -i --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 11: loopback vhost async test with split ring inorder mergeable path using vfio-pci driver
----------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 -a 0000:6f:01.0,max_queues=2 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 12: loopback vhost async test with split ring inorder non-mergeable path using vfio-pci driver
--------------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 -a 0000:6f:01.0,max_queues=2 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 13: loopback vhost async test with split ring mergeable path using vfio-pci driver
--------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 -a 0000:6f:01.0,max_queues=2 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 14: loopback vhost async test with split ring non-mergeable path using vfio-pci driver
------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 -a 0000:6f:01.0,max_queues=2 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 15: loopback vhost async test with split ring vectorized path using vfio-pci driver
---------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 -a 0000:6f:01.0,max_queues=2 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 16: loopback vhost async test with packed ring inorder mergeable path using vfio-pci driver
-----------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 -a 0000:6f:01.0,max_queues=2 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 17: loopback vhost async test with packed ring inorder non-mergeable path using vfio-pci driver
---------------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 -a 0000:6f:01.0,max_queues=2 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 18: loopback vhost async test with packed ring mergeable path using vfio-pci driver
---------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 -a 0000:6f:01.0,max_queues=2 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 19: loopback vhost async test with packed ring non-mergeable path using vfio-pci driver
-------------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 -a 0000:6f:01.0,max_queues=2 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].

Test Case 20: loopback vhost async test with packed ring vectorized path using vfio-pci driver
----------------------------------------------------------------------------------------------

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 2-4 -a 0000:6f:01.0,max_queues=2 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6f:01.0-q0;rxq0@0000:6f:01.0-q1]' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 8 -l 5-6 \
    --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=0,vectorized=1 \
    -- -i --rss-ip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send packets with vhost-testpmd::

    testpmd>set txpkts <frame_size>
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

5. Quit virtio-user, rerun step 2-4 with different packet length, <frame_size> include [64, 128, 256, 512, 1024, 1518].
