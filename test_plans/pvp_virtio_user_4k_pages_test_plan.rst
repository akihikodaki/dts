.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

=============================================
vhost/virtio-user pvp with 4K-pages test plan
=============================================

Dpdk 19.02 add support for using virtio-user without hugepages. The --no-huge mode was augmented to use memfd-backed memory (on systems that support memfd), to allow using virtio-user-based NICs without hugepages.

Prerequisites
-------------
Turn off transparent hugepage in grub by adding GRUB_CMDLINE_LINUX="transparent_hugepage=never"

Test Case1: Basic test vhost/virtio-user split ring with 4K-pages
=================================================================

1. Bind one port to vfio-pci, launch vhost::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py --bind=vfio-pci xx:xx.x
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/vhost-net,queues=1' -- -i --no-numa --socket-num=0
    testpmd>start

2. Prepare tmpfs with 4K-pages::

    mkdir /mnt/tmpfs_yinan
    mount tmpfs /mnt/tmpfs_yinan -t tmpfs -o size=4G

3. Launch virtio-user with 4K-pages::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-huge -m 1024 --file-prefix=virtio-user \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=1 -- -i
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

Test Case2: Basic test vhost/virtio-user packed ring with 4K-pages
==================================================================

1. Bind one port to vfio-pci, launch vhost::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py --bind=vfio-pci xx:xx.x
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/vhost-net,queues=1' -- -i --no-numa --socket-num=0
    testpmd>start

2. Prepare tmpfs with 4K-pages::

    mkdir /mnt/tmpfs_yinan
    mount tmpfs /mnt/tmpfs_yinan -t tmpfs -o size=4G

3. Launch virtio-user with 4K-pages::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 5-6 -n 4 --no-huge -m 1024 --file-prefix=virtio-user \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,packed_vq=1,queues=1 -- -i
    testpmd>start

4. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all
