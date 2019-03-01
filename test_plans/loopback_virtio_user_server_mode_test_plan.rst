.. Copyright (c) <2019>, Intel Corporation
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

   - Redistributions in binary forim must reproduce the above copyright
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

==========================================
Loopback virtio-user server mode test plan
==========================================

Description
===========

Without virtio-user server mode support, if the vhost-user backend restarts, 
there’s no way for it to reconnect to virtio-user. To address this, support for server mode has been added.
In this mode the socket file is created by virtio-user, which the backend connects to. 
This means that if the backend restarts, it can reconnect to virtio-user and continue communications.
Design below five cases for virtio-user server mode test.


Test Case1:  Basic test for virtio-user server mode, launch vhost first
=============================================================================

1. Launch vhost as client mode::

    rm -rf vhost-net*
    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/sock0,client=1,queues=1' -- -i --rxq=1 --txq=1 --nb-cores=1
    >set fwd mac
    >start

2. Launch virtio-user as server mode::

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=1 -- -i --rxq=1 --txq=1 --no-numa
    >set fwd mac
    >start tx_first 32

3. Run below command to get throughput,verify the loopback throughput is not zero::

    testpmd>show port stats all

Test Case2:  Basic test for virtio-user server mode, launch virtio-user first
=============================================================================

1. Launch virtio-user as server mode::

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=1 -- -i --rxq=1 --txq=1 --no-numa
    >set fwd mac
    >start

2. Launch vhost as client mode::

    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/sock0,client=1,queues=1' -- -i --rxq=1 --txq=1 --nb-cores=1
    >set fwd mac
    >start tx_first 32

3. Run below command to get throughput,verify the loopback throughput is not zero::

    testpmd>show port stats all

Test Case3: Reconnect virtio-user from the vhost side:
=============================================================================

1. Launch vhost as client mode::

    rm -rf vhost-net*
    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/sock0,client=1,queues=1' -- -i --rxq=1 --txq=1 --nb-cores=1
    >set fwd mac
    >start

2. Launch virtio-user as server mode::

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=1 -- -i --rxq=1 --txq=1 --no-numa
    >set fwd mac
    >start tx_first 32

3. Quit vhost side, then relaunch it as step1

4. Run below command to get throughput,verify the loopback throughput is not zero::

    testpmd>show port stats all

Test Case4: Reconnect virtio-user from the vhost side with multi_queues :
=============================================================================

1. launch vhost as client mode with 2 queues:: 

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost\
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

3. Quit vhost side, then relaunch it as step1

4. Run below command to get throughput,verify the loopback throughput is not zero::

    testpmd>show port stats all

Test Case5: Port start/stop at virtio-user side with server mode multi queues
=============================================================================

1. launch vhost as client mode with 2 queues:: 

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost\
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

3. Stop/start virtio-user port,check Link status is down/up after stop/start virtio-user port::

    Virtio-user side: testpmd>stop
    Virtio-user side: testpmd>port stop 0
    Virtio-user side: testpmd>show port info all
    Virtio-user side: testpmd>port start 0
    Virtio-user side: testpmd>show port info all

4. Run below command to get throughput,verify the loopback throughput is not zero::

     testpmd>show port stats all

