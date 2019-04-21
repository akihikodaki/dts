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

=====================================
vhost-user/virtio-pmd vm2vm test plan
=====================================

Description
===========

Test cases for vhost/virtio-pmd(0.95) VM2VM test with 3 rx/tx paths, includes mergeable, normal, vector_rx.
Also add vhost/virtio-pmd(1.0) vm2vm mergeable test for performance comparsion with vhost/virtio-pmd vm2vm mergeable.

Test flow
=========
Virtio-pmd <-> Vhost <-> Testpmd <-> Vhost <-> Virtio-pmd

Test Case 1: vhost-user + virtio-pmd with mergeable path
========================================================

1. Launch the testpmd by below commands::

     rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=on to enable mergeable path::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm0 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    taskset -c 34-35 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on  \
     -vnc :11 -daemonize

3. On VM1, bind vdev with igb_uio driver,then run testpmd, set rxonly mode for virtio1::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with igb_uio driver,then run testpmd, set txonly for virtio2 and send 64B packets::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    xxxxx
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 2: vhost-user + virtio-pmd with vector path
=====================================================

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

     rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=off to disable mergeable::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm0 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    taskset -c 34-35 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on  \
     -vnc :11 -daemonize

3. On VM1, bind vdev with igb_uio driver,then run testpmd, set rxonly for virtio1::

    ./testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with igb_uio driver,then run testpmd, set txonly for virtio2 and send 64B packets::

    ./testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    xxxxx
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 3: vhost-user + virtio-pmd with normal path
=====================================================

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

     rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=off to disable mergeable::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm0 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    taskset -c 34-35 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on  \
     -vnc :11 -daemonize

3. On VM1, bind vdev with igb_uio driver,then run testpmd, set rxonly for virtio1 ::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with igb_uio driver,then run testpmd, set rxonly for virtio2 and send 64B packets ::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    xxxxx
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 4: vhost-user + virtio1.0-pmd with mergeable path
===========================================================

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

     rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, note add "disable-modern=false" to enable virtio 1.0::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,disable-modern=false,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    taskset -c 34-35 \
    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,disable-modern=false,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on  \
     -vnc :11 -daemonize

3. On VM1, bind vdev with igb_uio driver,then run testpmd, set rxonly for virtio1 ::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with igb_uio driver,then run testpmd, set txonly for virtio2 ::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    xxxxx
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx
