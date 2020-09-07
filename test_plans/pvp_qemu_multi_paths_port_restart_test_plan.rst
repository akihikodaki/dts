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

========================================================
vhost/virtio qemu multi-paths and port restart test plan
========================================================

Description
===========

Benchmark pvp qemu test with 3 tx/rx paths,includes mergeable, normal, vector_rx.
Cover virtio 1.0 and virtio 0.95, also cover port restart test with each path.

Test flow
=========

TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Test Case 1: pvp test with virtio 0.95 mergeable path
=====================================================

1. Bind one port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with mrg_rxbuf feature on::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd::

    ./testpmd -c 0x3 -n 3 -- -i \
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Port restart 100 times by below command and re-calculate the average througnput,verify the throughput is not zero after port restart::

    testpmd>stop
    testpmd>start
    ...
    testpmd>stop
    testpmd>show port stats all
    testpmd>start
    testpmd>show port stats all

Test Case 2: pvp test with virtio 0.95 normal path
==================================================

1. Bind one port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with mrg_rxbuf feature off::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd with tx-offloads::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x0 --enable-hw-vlan-strip \
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>show port stats all

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 3: pvp test with virtio 0.95 vrctor_rx path
=====================================================

1. Bind one port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with mrg_rxbuf feature off::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd without ant tx-offloads::

    ./testpmd -c 0x3 -n 3 -- -i \
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>show port stats all

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 4: pvp test with virtio 1.0 mergeable path
====================================================

1. Bind one port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with 1 virtio, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd::

    ./testpmd -c 0x3 -n 3 -- -i \
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>show port stats all

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 5: pvp test with virtio 1.0 normal path
=================================================

1. Bind one port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with 1 virtio, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd with tx-offloads::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x0 --enable-hw-vlan-strip\
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>show port stats all

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all

Test Case 6: pvp test with virtio 1.0 vrctor_rx path
====================================================

1. Bind one port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with 1 virtio, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd without tx-offloads::

    ./testpmd -c 0x3 -n 3 -- -i \
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>show port stats all

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>start
    testpmd>show port stats all