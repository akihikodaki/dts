.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

=============================================
vhost/virtio different qemu version test plan
=============================================

Description
===========

This test plan will test pvp different qemu version test cases, also cover virtio 0.95, virtio 1.0 and virtio 1.1.

Test flow
=========

TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Test Case 1: PVP multi qemu version test with virtio 0.95 mergeable path
========================================================================

1. Bind one port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed different version qemu, includes [qemu-5.2.0, qemu-6.2.0, qemu-7.0.0, qemu-7.1.0, qemu-7.2.0].

3. Go to the absolute_path of different version qemu,then launch VM with different version qemu, note: we need add "disable-modern=true" to enable virtio 0.95::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -netdev user,id=netdev0,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev1,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev1,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=on \
    -vnc :10

4. On VM, bind virtio net to vfio-pci and run testpmd ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 3 -- -i \
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

5. Send packet by packet generator with different packet sizes(68,128,256,512,1024,1280,1518),repeat below command to get throughput 10 times,then calculate the average throughput::

    testpmd>show port stats all

Test Case 2: PVP test with virtio 1.0 mergeable path
====================================================

1. Bind one port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed different version qemu, includes [qemu-5.2.0, qemu-6.2.0, qemu-7.0.0, qemu-7.1.0, qemu-7.2.0].

3. Go to the absolute_path of different version qemu,then launch VM with different version qemu, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -netdev user,id=netdev0,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev1,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev1,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on \
    -vnc :10

4. On VM, bind virtio net to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 3 -- -i \
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

5. Send packet by packet generator with different packet sizes(68,128,256,512,1024,1280,1518),repeat below command to get throughput 10 times,then calculate the average throughput::

    testpmd>show port stats all

Test Case 3: PVP test with virtio 1.1 mergeable path
====================================================

1. Bind one port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed different version qemu, includes [qemu-5.2.0, qemu-6.2.0, qemu-7.0.0, qemu-7.1.0, qemu-7.2.0].

3. Go to the absolute_path of different version qemu,then launch VM with different version qemu, note: we need add "disable-modern=false,packed=on" to enable virtio 1.1::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -netdev user,id=netdev0,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev1,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev1,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,packed=on \
    -vnc :10

4. On VM, bind virtio net to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 3 -- -i \
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

5. Send packet by packet generator with different packet sizes(68,128,256,512,1024,1280,1518),repeat below command to get throughput 10 times,then calculate the average throughput::

    testpmd>show port stats all
