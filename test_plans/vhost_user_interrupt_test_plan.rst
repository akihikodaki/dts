.. Copyright (c) <2019>, Intel Corporation
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

   - Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.

   - Neither the name of Intel Corporation nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.

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

    ./testpmd -l 7-8 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=1 -- -i

2. Build l3fwd-power sample and launch l3fwd-power with a virtual vhost device::

    ./l3fwd-power -l 0-3 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=/tmp/sock0,queues=1,client=1' -- -p 0x1 --parse-ptype 1 --config "(0,0,2)"

3. Send packet by testpmd, check vhost-user core will keep wakeup status::

    testpmd>set fwd txonly
    testpmd>start

4. Stop and restart testpmd again, check vhost-user core will sleep and wakeup again.

Test Case2: Wake up split ring vhost-user cores with l3fwd-power sample when multi queues are enabled
=====================================================================================================

1. Launch virtio-user with server mode::

    ./testpmd -l 1-5 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=4 -- -i --rxq=4 --txq=4 --rss-ip

2. Build l3fwd-power sample and launch l3fwd-power with a virtual vhost device::

    ./l3fwd-power -l 9-12 -n 4 --no-pci --log-level=9 \
    --vdev 'eth_vhost0,iface=/tmp/sock0,queues=4,client=1' -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,9),(0,1,10),(0,2,11),(0,3,12)"

3. Send packet by testpmd, check vhost-user multi-cores will keep wakeup status::

    testpmd>set fwd txonly
    testpmd>start

4. Stop and restart testpmd again, check vhost-user cores will sleep and wakeup again.

Test Case3: Wake up packed ring vhost-user core with l3fwd-power sample
=======================================================================

1. Launch virtio-user with server mode::

    ./testpmd -l 7-8 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=1,packed_vq=1 -- -i

2. Build l3fwd-power sample and launch l3fwd-power with a virtual vhost device::

    ./l3fwd-power -l 0-3 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=/tmp/sock0,queues=1,client=1' -- -p 0x1 --parse-ptype 1 --config "(0,0,2)"

3. Send packet by testpmd, check vhost-user core will keep wakeup status::

    testpmd>set fwd txonly
    testpmd>start

4. Stop and restart testpmd again, check vhost-user core will sleep and wakeup again.

Test Case4:  Wake up packed ring vhost-user cores with l3fwd-power sample when multi queues are enabled
=======================================================================================================

1. Launch virtio-user with server mode::

    ./testpmd -l 1-5 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=4,packed_vq=1,mrg_rxbuf=0 -- -i --rxq=4 --txq=4 --rss-ip

2. Build l3fwd-power sample and launch l3fwd-power with a virtual vhost device::

    ./l3fwd-power -l 9-12 -n 4 --no-pci --log-level=9 \
    --vdev 'eth_vhost0,iface=/tmp/sock0,queues=4,client=1' -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,9),(0,1,10),(0,2,11),(0,3,12)"

3. Send packet by testpmd, check vhost-user multi-cores will keep wakeup status::

    testpmd>set fwd txonly
    testpmd>start

4. Stop and restart testpmd again, check vhost-user cores will sleep and wakeup again.

Test Case5: Wake up split ring vhost-user cores with l3fwd-power sample when multi queues and cbdma are enabled
===============================================================================================================

1. Launch virtio-user with server mode::

    ./testpmd -l 1-5 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=4 -- -i --rxq=4 --txq=4 --rss-ip

2. Bind 4 cbdma ports to igb_uio driver, then launch l3fwd-power with a virtual vhost device::

    ./l3fwd-power -l 9-12 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=/tmp/sock0,queues=4,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3]' -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,9),(0,1,10),(0,2,11),(0,3,12)"

3. Send packet by testpmd, check vhost-user multi-cores will keep wakeup status::

    testpmd>set fwd txonly
    testpmd>start

4. Stop and restart testpmd again, check vhost-user cores will sleep and wakeup again.