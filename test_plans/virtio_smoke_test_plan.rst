. Copyright (c) <2020>, Intel Corporation
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

=================================
vhost/virtio-user smoke test plan
=================================

This test plan cover vhost/virtio pvp and loopback topolopy test, split ring and packed ring test,
server mode and client mode test, also multi-queues and dynamic queue size test.

Test Case 1: loopback reconnect test with split ring mergeable path and server mode
===================================================================================

1. Launch vhost as client mode with 2 queues::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=8' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 8 queues::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=8,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=8 --txq=8
    >set fwd mac
    >start tx_first 32

3. Stop vhost port and check queue0 and queue1 RX/TX direction both have packets::

    testpmd>stop

4. Relaunch vhost with 8 queues and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=8' -- -i --nb-cores=2 --rxq=8 --txq=8
    >set fwd mac
    >start tx_first 32
    stop
    set burst 1
    start tx_first 1

5. Stop vhost port and check queue0 to queue7 RX/TX direction both have packets::

    testpmd>stop

Test Case 2: pvp test with virtio packed ring vectorized path
============================================================

1. Bind one port to vfio-pci, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1' \
    -- -i --nb-cores=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=1024 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

3. Send 64B and 1518B packets with packet generator, check the throughput with below command::

    testpmd>show port stats all



