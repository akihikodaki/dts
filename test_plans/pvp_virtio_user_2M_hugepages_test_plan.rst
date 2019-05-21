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

================================================
vhost/virtio-user pvp with 2M hugepage test plan
================================================

Description
===========

Before 18.05, virtio-user can only work 1G hugepage. After 18.05, more hugepage pages can be represented by single fd （file descriptor）file, so virtio-user can work with 2M hugepage now. The key parameter is "--single-file-segments" when launch virtio-user.

Test Case1:  Basic test for virtio-user 2M hugepage
===================================================

1. Before the test, plese make sure only 2M hugepage are mounted in host.

2. Bind one port to igb_uio, launch vhost::

    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/sock0,queues=1' -- -i

3. Launch virtio-user with 2M hugepage::

    ./testpmd -l 5-6 -n 4  --no-pci --socket-mem 1024,1024 --single-file-segments --file-prefix=virtio-user \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,queues=1 -- -i


3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all