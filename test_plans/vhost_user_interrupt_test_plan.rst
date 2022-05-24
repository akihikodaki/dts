.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

===================================
vhost-user interrupt mode test plan
===================================

Description
===========

Vhost-user interrupt need test with l3fwd-power sample, small packets send from virtio-user to vhost side，
check vhost-user cores can be wakeup，and vhost-user cores should be back to sleep after stop sending packets
from virtio side.

Test flow
=========

Virtio-user --> Vhost-user

Test Case1: Wake up split ring vhost-user core with l3fwd-power sample
======================================================================

1. Launch virtio-user with server mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-8 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=1 -- -i

2. Build l3fwd-power sample and launch l3fwd-power with a virtual vhost device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 0-3 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=/tmp/sock0,queues=1,client=1' -- -p 0x1 --parse-ptype 1 --config "(0,0,2)"

3. Send packet by testpmd, check vhost-user core will keep wakeup status::

    testpmd>set fwd txonly
    testpmd>start

4. Stop and restart testpmd again, check vhost-user core will sleep and wakeup again.

Test Case2: Wake up split ring vhost-user cores with l3fwd-power sample when multi queues are enabled
=====================================================================================================

1. Launch virtio-user with server mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=4 -- -i --rxq=4 --txq=4 --rss-ip

2. Build l3fwd-power sample and launch l3fwd-power with a virtual vhost device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 9-12 -n 4 --no-pci --log-level=9 \
    --vdev 'eth_vhost0,iface=/tmp/sock0,queues=4,client=1' -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,9),(0,1,10),(0,2,11),(0,3,12)"

3. Send packet by testpmd, check vhost-user multi-cores will keep wakeup status::

    testpmd>set fwd txonly
    testpmd>start

4. Stop and restart testpmd again, check vhost-user cores will sleep and wakeup again.

Test Case3: Wake up packed ring vhost-user core with l3fwd-power sample
=======================================================================

1. Launch virtio-user with server mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 7-8 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=1,packed_vq=1 -- -i

2. Build l3fwd-power sample and launch l3fwd-power with a virtual vhost device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 0-3 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=/tmp/sock0,queues=1,client=1' -- -p 0x1 --parse-ptype 1 --config "(0,0,2)"

3. Send packet by testpmd, check vhost-user core will keep wakeup status::

    testpmd>set fwd txonly
    testpmd>start

4. Stop and restart testpmd again, check vhost-user core will sleep and wakeup again.

Test Case4:  Wake up packed ring vhost-user cores with l3fwd-power sample when multi queues are enabled
=======================================================================================================

1. Launch virtio-user with server mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-5 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=4,packed_vq=1,mrg_rxbuf=0 -- -i --rxq=4 --txq=4 --rss-ip

2. Build l3fwd-power sample and launch l3fwd-power with a virtual vhost device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 9-12 -n 4 --no-pci --log-level=9 \
    --vdev 'eth_vhost0,iface=/tmp/sock0,queues=4,client=1' -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,9),(0,1,10),(0,2,11),(0,3,12)"

3. Send packet by testpmd, check vhost-user multi-cores will keep wakeup status::

    testpmd>set fwd txonly
    testpmd>start

4. Stop and restart testpmd again, check vhost-user cores will sleep and wakeup again.
