
.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

===========================================
vhost/virtio multi-paths loopback test plan
===========================================

Benchmark vhost/virtio-user loopback test with 10 tx/rx paths.
Includes split ring mergeable, non-mergeable, vector_rx, inorder mergeable,
inorder non-mergeable, packed ring mergeable, packed ring non-mergeable,
packed ring inorder mergeable, packed ring inorder non-mergeable path,
packed ring vectorized path.

Test Case 1: loopback test with packed ring mergeable path
==========================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

Test Case 2: loopback test with packed ring non-mergeable path
==============================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd, [frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

Test Case 3: loopback test with packed ring inorder mergeable path
===================================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

Test Case 4: loopback test with packed ring inorder non-mergeable path
======================================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

Test Case 5: loopback test with split ring mergeable path
==========================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

Test Case 6: loopback test with split ring non-mergeable path
=============================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

Test Case 7: loopback test with split ring vector_rx path
=========================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

Test Case 8: loopback test with split ring inorder mergeable path
=================================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

Test Case 9: loopback test with split ring inorder non-mergeable path
=====================================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all

Test Case 10: loopback test with packed ring vectorized path
============================================================

1. Launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  --no-pci \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=0,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with vhost-testpmd,[frame_size] is the parameter changs in [64, 1518]::

    testpmd>set txpkts [frame_size]
    testpmd>start tx_first 32

4. Repeat below command to get throughput 10 times,then check the average throughput can get expected data with below command::

    testpmd>show port stats all
