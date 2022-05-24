.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

=========================================
Vhost/virtio-user pvp share lib test plan
=========================================

Description
===========

The feature need compile dpdk as shared libraries, then application should use option ``-d`` to load the dynamic pmd that are built as shared libraries.

Test Case1: Vhost/virtio-user pvp share lib test with 82599
===========================================================

1. Enable the shared lib in DPDK configure file::

    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dc_args='-DRTE_BUILD_SHARED_LIB=1' --default-library=shared x86_64-native-linuxapp-gcc

2. Recompile dpdk code::

    ninja -C x86_64-native-linuxapp-gcc -j 55

3. Export shared lib files into host environment::

    export LD_LIBRARY_PATH=/root/dpdk/x86_64-native-linuxapp-gcc/drivers:$LD_LIBRARY_PATH

4. Bind 82599 port with vfio-pci, use option ``-d`` to load the dynamic pmd when launch vhost::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -c 0x03 -n 4 -d librte_net_vhost.so.21.0 -d librte_net_i40e.so.21.0 -d librte_mempool_ring.so.21.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i
    testpmd>start

5. Launch virtio-user::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0c -n 4 -d librte_net_virtio.so.21.0 -d librte_mempool_ring.so.21.0 \
    --no-pci --file-prefix=virtio  --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net -- -i
    testpmd>start

6. Send traffic by packet generator, check the throughput with below command::

    testpmd>show port stats all

Test Case2: Vhost/virtio-user pvp share lib test with Intel® Ethernet 700 Series
================================================================================

Similar as Test Case1, all steps are similar except step 4:

4. Bind Intel® Ethernet 700 Series port with vfio-pci, use option ``-d`` to load the dynamic pmd when launch vhost::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -c 0x03 -n 4 -d librte_net_vhost.so -d librte_net_i40e.so -d librte_mempool_ring.so \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i
    testpmd>start
