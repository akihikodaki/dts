.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

==============================================
Virtio_user for container networking test plan
==============================================

Description
===========

Container becomes more and more popular for strengths, like low overhead, fast
boot-up time, and easy to deploy, etc.
Virtio, in essence, is a shm-based solution to transmit/receive packets. How is
memory shared? In VM's case, qemu always shares the whole physical layout of VM
to vhost backend. But it's not feasible for a container, as a process, to share
all virtual memory regions to backend. So only those virtual memory regions
(aka, hugepages initialized in DPDK) are sent to backend. It restricts that only
addresses in these areas can be used to transmit or receive packets.

Limitations
-----------
We have below limitations in this solution:
 * Cannot work with --huge-unlink option. As we need to reopen the hugepage
   file to share with vhost backend.
 * Cannot work with --no-huge option. Currently, DPDK uses anonymous mapping
   under this option which cannot be reopened to share with vhost backend.
 * Cannot work when there are more than VHOST_MEMORY_MAX_NREGIONS(8) hugepages.
   If you have more regions (especially when 2MB hugepages are used), the option,
   --single-file-segments, can help to reduce the number of shared files.
 * Applications should not use file name like HUGEFILE_FMT ("%smap_%d"). That
   will bring confusion when sharing hugepage files with backend by name.
 * Root privilege is a must. DPDK resolves physical addresses of hugepages
   which seems not necessary, and some discussions are going on to remove this
   restriction.

Test Case 1: packet forward test for container networking
=========================================================

1. Mount hugepage::

    mkdir /mnt/huge
    mount -t hugetlbfs nodev /mnt/huge

2. Bind one port to vfio-pci, launch vhost::

    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i

2. Start a container instance with a virtio-user port::

    docker run -i -t --privileged -v /root/dpdk/vhost-net:/tmp/vhost-net -v /mnt/huge:/dev/hugepages \
    -v /root/dpdk:/root/dpdk dpdk_image ./root/dpdk/x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 -m 1024 --no-pci --file-prefix=container \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net -- -i

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check virtio could receive and fwd packets correctly in container::

    testpmd>show port stats all

Test Case 2: packet forward with multi-queues for container networking
======================================================================

1. Mount hugepage::

    mkdir /mnt/huge
    mount -t hugetlbfs nodev /mnt/huge

2. Bind one port to vfio-pci, launch vhost::

    ./<build_target>/app/dpdk-testpmd -l 1-3 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2

2. Start a container instance with a virtio-user port::

    docker run -i -t --privileged -v /root/dpdk/vhost-net:/tmp/vhost-net -v /mnt/huge:/dev/hugepages \
    -v /root/dpdk:/root/dpdk dpdk_image ./root/dpdk/x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 4-6 -n 4 -m 1024 --no-pci --file-prefix=container \
    --vdev=virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=2 -- -i --rxq=2 --txq=2 --nb-cores=2

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check virtio could receive and fwd packets in container with two queues::

    testpmd>show port stats all
    testpmd>stop
