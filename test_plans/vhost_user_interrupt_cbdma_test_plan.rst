.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

==============================================
vhost-user interrupt mode with CBDMA test plan
==============================================

Description
===========

Vhost-user interrupt need test with l3fwd-power sample with CBDMA channel, 
small packets send from virtio-user to vhost side, check vhost-user cores 
can be wakeup，and vhost-user cores should be back to sleep after stop 
sending packets from virtio side.

.. note::

   1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > 5.1, and packed ring multi-queues not support reconnect in qemu yet.
   2.For split virtqueue virtio-net with multi-queues server mode test, better to use qemu version >= 5.2.0, dut to qemu(v4.2.0~v5.1.0) exist split ring multi-queues reconnection issue.
   3.Kernel version > 4.8.0, mostly linux distribution don't support vfio-noiommu mode by default,
   so testing this case need rebuild kernel to enable vfio-noiommu.
   4.When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may exceed IOMMU's max capability, better to use 1G guest hugepage.
   5.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

Prerequisites
=============
Topology
--------
Test flow: Virtio-user --> Vhost-user

General set up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110
    For example:
    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

Test case
=========

Test Case 1: Wake up split ring vhost-user cores with l3fwd-power sample when multi queues and cbdma are enabled
----------------------------------------------------------------------------------------------------------------

1. Launch virtio-user with server mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=4 -- -i --rxq=4 --txq=4 --rss-ip

2. Bind 4 cbdma ports to vfio-pci driver, then launch l3fwd-power with a virtual vhost device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 9-12 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=/tmp/sock0,queues=4,client=1,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1;txq2@0000:80:04.2;txq3@0000:80:04.3;rxq0@0000:80:04.0;rxq1@0000:80:04.1;rxq2@0000:80:04.2;rxq3@0000:80:04.3]' -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,9),(0,1,10),(0,2,11),(0,3,12)"

3. Send packet by testpmd, check vhost-user multi-cores will keep wakeup status::

    testpmd>set fwd txonly
    testpmd>start

4. Stop and restart testpmd again, check vhost-user cores will sleep and wakeup again.

Test Case 2: Wake up packed ring vhost-user cores with l3fwd-power sample when multi queues and cbdma are enabled
-----------------------------------------------------------------------------------------------------------------

1. Launch virtio-user with server mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=4,packed_vq=1 -- -i --rxq=4 --txq=4 --rss-ip

2. Bind 4 cbdma ports to vfio-pci driver, then launch l3fwd-power with a virtual vhost device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 9-12 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=/tmp/sock0,queues=4,client=1,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1;txq2@0000:80:04.2;txq3@0000:80:04.3;rxq0@0000:80:04.0;rxq1@0000:80:04.1;rxq2@0000:80:04.2;rxq3@0000:80:04.3]' -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,9),(0,1,10),(0,2,11),(0,3,12)"

3. Send packet by testpmd, check vhost-user multi-cores will keep wakeup status::

    testpmd>set fwd txonly
    testpmd>start

4. Stop and restart testpmd again, check vhost-user cores will sleep and wakeup again.
