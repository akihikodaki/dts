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

=============================================
vhost/virtio different qemu version test plan
=============================================

Description
===========

This test plan will test pvp different qemu version test cases, also cover virtio 1.0 and virtio 0.95.

Test flow
=========

TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Test Case 1: PVP multi qemu version test with virtio 0.95 mergeable path
========================================================================

1. Bind one port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed different version qemu, includes [qemu_2.5, qemu_2.6, qemu_2.7, qemu_2.8, qemu_2.9, qemu_2.10, qemu_2.11, qemu_2.12, qemu_3.0].

3. Go to the absolute_path of different version qemu,then launch VM with different version qemu::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
    -netdev user,id=netdev0,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev1,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev1,mac=52:54:00:00:00:01,mrg_rxbuf=on \
    -vnc :10

4. On VM, bind virtio net to igb_uio and run testpmd ::
    ./testpmd -c 0x3 -n 3 -- -i \
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

5. Send packet by packet generator with different packet sizes(68,128,256,512,1024,1280,1518),repeat below command to get throughput 10 times,then calculate the average throughput::

    testpmd>show port stats all

Test Case 2: PVP test with virtio 1.0 mergeable path
====================================================

1. Bind one port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed different version qemu, includes [qemu_2.5, qemu_2.6, qemu_2.7, qemu_2.8, qemu_2.9, qemu_2.10, qemu_2.11, qemu_2.12, qemu_3.0].

3. Go to the absolute_path of different version qemu,then launch VM with different version qemu, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
    -netdev user,id=netdev0,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev1,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev1,mac=52:54:00:00:00:01,mrg_rxbuf=on \
    -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd::

    ./testpmd -c 0x3 -n 3 -- -i \
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packet by packet generator with different packet sizes(68,128,256,512,1024,1280,1518),repeat below command to get throughput 10 times,then calculate the average throughput::

    testpmd>show port stats all