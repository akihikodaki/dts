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

=================================
vhost dequeue zero-copy test plan
=================================

Description
===========

Vhost dequeue zero-copy is a performance optimization for vhost, the copy in the dequeue path is avoided in order to improve the performance. The test cases cover split ring and packed ring.
Notice:

* All packed ring case need special qemu version.
* In the PVP case, when packet size is 1518B, 10G nic could be the performance bottleneck, so we use 40G traffic genarator and 40G nic.
* Also as vhost zero copy mbufs should be consumed as soon as possible, don't start send packets at vhost side before VM and virtio-pmd launched.

Test flow
=========

TG --> NIC --> Vhost --> Virtio --> Vhost --> NIC --> TG

Test Case 1: pvp split ring dequeue zero-copy test
==================================================

1. Bind one 40G port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1,dequeue-zero-copy=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024 --txfreet=992
    testpmd>set fwd mac

2. Launch VM with mrg_rxbuf feature on, note that qemu_version need > qemu_2.10 for support adjusting parameter rx_queue_size::

    qemu-system-x86_64 -name vm1 \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=5,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
     -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char0,path=./vhost-net \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
     -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd::

    ./dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./testpmd -c 0x3 -n 4 -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Start testpmd at host side after VM and virtio-pmd launched::

    testpmd>start

5. Send packets by packet generator with different packet sizes (64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

6. Repeat the test with dequeue-zero-copy=0, compare the performance gains or degradation. For small packet, we may expect ~20% performance drop, but for big packet, we expect ~20% performance gains.

Test Case 2: pvp split ring dequeue zero-copy test with 2 queues
================================================================

1. Bind one 40G port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -l 2-4 -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,dequeue-zero-copy=1' -- \
    -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024 --txfreet=992
    testpmd>set fwd mac

2. Launch VM with vectors=2*queue_num+2 and mrg_rxbuf/mq feature on, note that qemu_version need > qemu_2.10 for support adjusting parameter rx_queue_size::

    qemu-system-x86_64 -name vm1 \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=5,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
     -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char0,path=./vhost-net \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=8,rx_queue_size=1024,tx_queue_size=1024 \
     -vnc :10

3. On VM, bind vdev to igb_uio and run testpmd::

    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./testpmd -c 0x07 -n 4 -- -i \
    --rxq=2 --txq=2 --txd=1024 --rxd=1024 --nb-cores=2
    testpmd>set fwd mac
    testpmd>start

4. Start testpmd at host side after VM and virtio-pmd launched::

    testpmd>start

5. Send packets by packet generator with different packet sizes (64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

6. Check each queue's rx/tx packet numbers at vhost side::

    testpmd>stop

Test Case 3: pvp split ring dequeue zero-copy test with driver reload test
==========================================================================

1. Bind one 40G port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -l 1-5 -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=16,dequeue-zero-copy=1,client=1' -- \
    -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024 --txfreet=992
    testpmd>set fwd mac

2. Launch VM with vectors=2*queue_num+2 and mrg_rxbuf/mq feature on, note that qemu_version need > qemu_2.10 for support adjusting parameter rx_queue_size::

    qemu-system-x86_64 -name vm1 \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=5,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
     -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char0,path=./vhost-net,server \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=40,rx_queue_size=1024,tx_queue_size=1024 \
     -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd::

    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./testpmd -l 0-4 -n 4 --socket-mem 1024,0 -- -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. Start testpmd at host side after VM launched::

    testpmd>start

5. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

6. Relaunch testpmd at virtio side in VM for driver reloading::

    testpmd>quit
    ./testpmd -l 0-4 -n 4 --socket-mem 1024,0 -- -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

7. Send packets by packet generator with different packet sizes (64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

8. Check each queue's rx/tx packet numbers at vhost side::

    testpmd>stop

Test Case 4: pvp split ring dequeue zero-copy test with maximum txfreet
=======================================================================

1. Bind one 40G port to igb_uio, then launch testpmd by below command::

     ./testpmd -l 1-5 -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=16,dequeue-zero-copy=1,client=1' -- \
    -i --nb-cores=4 --rxq=16 --txq=16  --txfreet=988 --txrs=4 --txd=992 --rxd=992
    testpmd>set fwd mac

2. Launch VM with vectors=2*queue_num+2 and mrg_rxbuf/mq feature on, note that qemu_version need>qemu_2.10 for support adjusting parameter rx_queue_size::

    qemu-system-x86_64 -name vm1 \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=5,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
     -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char0,path=./vhost-net,server \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=40,rx_queue_size=1024,tx_queue_size=1024 \
     -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd::

    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./testpmd -l 0-4 -n 4 --socket-mem 1024,0 -- -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Start testpmd at host side after VM launched::

    testpmd>start

5. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

6. Check each queue's rx/tx packet numbers at vhost side::

    testpmd>stop

Test Case 5: pvp split ring dequeue zero-copy test with vector_rx path
======================================================================

1. Bind one port to igb_uio, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 2-4  --socket-mem 1024,1024 --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0,dequeue-zero-copy=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txfreet=992 --txrs=32
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0,queue_size=1024 \
    -- -i --tx-offloads=0x0 --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packet with packet generator with different packet size,includes [64, 128, 256, 512, 1024, 1518], check the throughput with below command::

    testpmd>show port stats all

4. Repeat the test with dequeue-zero-copy=0, compare the performance gains or degradation. For small packet, we may expect ~20% performance drop, but for big packet, we expect ~20% performance gains.

Test Case 6: pvp packed ring dequeue zero-copy test
===================================================

1. Bind one 40G port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1,dequeue-zero-copy=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024 --txfreet=992
    testpmd>set fwd mac

2. Launch VM with mrg_rxbuf feature on, note that qemu_version need > qemu_2.10 for support adjusting parameter rx_queue_size::

    qemu-system-x86_64 -name vm1 \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=5,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
     -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char0,path=./vhost-net \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,packed=on \
     -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd::

    ./dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./testpmd -c 0x3 -n 4 -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Start testpmd at host side after VM and virtio-pmd launched::

    testpmd>start

5. Send packets by packet generator with different packet sizes (64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

6. Repeat the test with dequeue-zero-copy=0, compare the performance gains or degradation. For small packet, we may expect ~20% performance drop, but for big packet, we expect ~20% performance gains.

Test Case 7: pvp packed ring dequeue zero-copy test with 2 queues
=================================================================

1. Bind one 40G port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -l 2-4 -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,dequeue-zero-copy=1' -- \
    -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024 --txfreet=992
    testpmd>set fwd mac

2. Launch VM with vectors=2*queue_num+2 and mrg_rxbuf/mq feature on, note that qemu_version need > qemu_2.10 for support adjusting parameter rx_queue_size::

    qemu-system-x86_64 -name vm1 \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=5,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
     -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char0,path=./vhost-net \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=8,rx_queue_size=1024,tx_queue_size=1024,packed=on \
     -vnc :10

3. On VM, bind vdev to igb_uio and run testpmd::

    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./testpmd -c 0x07 -n 4 -- -i \
    --rxq=2 --txq=2 --txd=1024 --rxd=1024 --nb-cores=2
    testpmd>set fwd mac
    testpmd>start

4. Start testpmd at host side after VM and virtio-pmd launched::

    testpmd>start

5. Send packets by packet generator with different packet sizes (64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

6. Check each queue's rx/tx packet numbers at vhost side::

    testpmd>stop

Test Case 8: pvp packed ring dequeue zero-copy test with driver reload test
===========================================================================

1. Bind one 40G port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -l 1-5 -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=16,dequeue-zero-copy=1,client=1' -- \
    -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024 --txfreet=992
    testpmd>set fwd mac

2. Launch VM with vectors=2*queue_num+2 and mrg_rxbuf/mq feature on, note that qemu_version need > qemu_2.10 for support adjusting parameter rx_queue_size::

    qemu-system-x86_64 -name vm1 \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=5,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
     -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char0,path=./vhost-net,server \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=40,rx_queue_size=1024,tx_queue_size=1024,packed=on \
     -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd::

    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./testpmd -l 0-4 -n 4 --socket-mem 1024,0 -- -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. Start testpmd at host side after VM launched::

    testpmd>start

5. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

6. Relaunch testpmd at virtio side in VM for driver reloading::

    testpmd>quit
    ./testpmd -l 0-4 -n 4 --socket-mem 1024,0 -- -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

7. Send packets by packet generator with different packet sizes (64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

8. Check each queue's rx/tx packet numbers at vhost side::

    testpmd>stop
