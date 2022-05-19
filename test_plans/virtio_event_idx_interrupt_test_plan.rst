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

=========================================
virtio event idx interrupt mode test plan
=========================================

Description
===========

This feature is to suppress interrupts for performance improvement, need compare
interrupt times with and without virtio event idx enabled. Also need cover driver
reload test. For packed virtqueue test, need using qemu version > 4.2.0.

Test flow
=========

TG --> NIC --> Vhost-user --> Virtio-net

Test Case 1: Compare interrupt times with and without split ring virtio event idx enabled
=========================================================================================

1. Bind one nic port to vfio-pci, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=1' -- -i
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

3. On VM1, set virtio device IP::

    ifconfig [ens3] 1.1.1.2  # [ens3] is the name of virtio-net

4. Send 10M packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

    cat /proc/interrupts

5. Disable virtio event idx feature and rerun step1 ~ step4.

6. Compare interrupt times between virtio event_idx enabled and virtio event_idx disabled.

Test Case 2: Split ring virtio-pci driver reload test
=====================================================

1. Bind one nic port to vfio-pci, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

3. On VM1, set virtio device IP, send 10M packets from packet generator to nic then check virtio device can receive packets::

    ifconfig [ens3] 1.1.1.2      # [ens3] is the name of virtio-net
    tcpdump -i [ens3]

4. Reload virtio-net driver by below cmds::

    ifconfig [ens3] down
    ./usertools/dpdk-devbind.py -u [00:03.0]   # [00:03.0] is the pci addr of virtio-net
    ./usertools/dpdk-devbind.py -b virtio-pci [00:03.0]

5. Check virtio device can receive packets again::

    ifconfig [ens3] 1.1.1.2
    tcpdump -i [ens3]

6. Rerun step4 and step5 100 times to check event idx workable after driver reload.

Test Case 3: Wake up split ring virtio-net cores with event idx interrupt mode 16 queues test
=============================================================================================

1. Bind one nic port to vfio-pci, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-17 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=16' -- -i --nb-cores=16 --txd=1024 --rxd=1024 --rxq=16 --txq=16
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=16,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=40,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

3. On VM1, give virtio device ip addr and enable vitio-net with 16 quques::

    ifconfig [ens3] 1.1.1.2           # [ens3] is the name of virtio-net
    ethtool -L [ens3] combined 16

4. Send 10M different ip addr packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

    cat /proc/interrupts

5. After two hours stress test, stop and restart testpmd, check each queue has new packets coming::

    testpmd>stop
    testpmd>start
    testpmd>stop

Test Case 4: Compare interrupt times with and without packed ring virtio event idx enabled
==========================================================================================

1. Bind one nic port to vfio-pci, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=1' -- -i
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on \
     -vnc :12 -daemonize

3. On VM1, set virtio device IP::

    ifconfig [ens3] 1.1.1.2  # [ens3] is the name of virtio-net

4. Send 10M packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

    cat /proc/interrupts

5. Disable virtio event idx feature and rerun step1 ~ step4.

6. Compare interrupt times between virtio event_idx enabled and virtio event_idx disabled.

Test Case 5: Packed ring virtio-pci driver reload test
======================================================

1. Bind one nic port to vfio-pci, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on \
     -vnc :12 -daemonize

3. On VM1, set virtio device IP, send 10M packets from packet generator to nic then check virtio device can receive packets::

    ifconfig [ens3] 1.1.1.2      # [ens3] is the name of virtio-net
    tcpdump -i [ens3]

4. Reload virtio-net driver by below cmds::

    ifconfig [ens3] down
    ./usertools/dpdk-devbind.py -u [00:03.0]   # [00:03.0] is the pci addr of virtio-net
    ./usertools/dpdk-devbind.py -b virtio-pci [00:03.0]

5. Check virtio device can receive packets again::

    ifconfig [ens3] 1.1.1.2
    tcpdump -i [ens3]

6. Rerun step4 and step5 100 times to check event idx workable after driver reload.

Test Case 6: Wake up packed ring virtio-net cores with event idx interrupt mode 16 queues test
==============================================================================================

1. Bind one nic port to vfio-pci, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-17 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=16' -- -i --nb-cores=16 --txd=1024 --rxd=1024 --rxq=16 --txq=16
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=16,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=40,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on \
     -vnc :12 -daemonize

3. On VM1, give virtio device ip addr and enable vitio-net with 16 quques::

    ifconfig [ens3] 1.1.1.2           # [ens3] is the name of virtio-net
    ethtool -L [ens3] combined 16

4. Send 10M different ip addr packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

    cat /proc/interrupts

5. After two hours stress test, stop and restart testpmd, check each queue has new packets coming::

    testpmd>stop
    testpmd>start
    testpmd>stop
