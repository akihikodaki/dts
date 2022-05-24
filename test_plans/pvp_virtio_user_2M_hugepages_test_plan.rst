.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

================================================
vhost/virtio-user pvp with 2M hugepage test plan
================================================

Description
===========

Before 18.05, virtio-user can only work 1G hugepage. After 18.05, more hugepage pages can be represented by single fd （file descriptor）file, so virtio-user can work with 2M hugepage now. The key parameter is "--single-file-segments" when launch virtio-user.

Test Case1:  Basic test for virtio-user split ring 2M hugepage
==============================================================

1. Before the test, plese make sure only 2M hugepage are mounted in host.

2. Bind one port to vfio-pci, launch vhost::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/sock0,queues=1' -- -i

3. Launch virtio-user with 2M hugepage::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4  --no-pci --single-file-segments --file-prefix=virtio-user \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,queues=1 -- -i


3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case1:  Basic test for virtio-user packed ring 2M hugepage
===============================================================

1. Before the test, plese make sure only 2M hugepage are mounted in host.

2. Bind one port to vfio-pci, launch vhost::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/sock0,queues=1' -- -i

3. Launch virtio-user with 2M hugepage::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4  --no-pci --single-file-segments --file-prefix=virtio-user \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,packed_vq=1,queues=1 -- -i


3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all