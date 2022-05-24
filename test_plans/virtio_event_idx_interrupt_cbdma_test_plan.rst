.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

====================================================
virtio event idx interrupt mode with cbdma test plan
====================================================

Description
===========

This feature is to suppress interrupts for performance improvement, need compare
interrupt times with and without virtio event idx enabled. This test plan test 
virtio event idx interrupt with cbdma enabled. Also need cover driver reload test.

..Note:
1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > 5.1, and packed ring multi-queues not support reconnect in qemu yet.
2.For split virtqueue virtio-net with multi-queues server mode test, need qemu version >= 5.2.0, dut to old qemu exist reconnect issue when multi-queues test.
3.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

Test flow
=========

TG --> NIC --> Vhost-user --> Virtio-net

Test Case1: Split ring virtio-pci driver reload test with CBDMA enabled
=======================================================================

1. Bind one nic port and one cbdma channel to vfio-pci, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --file-prefix=vhost \
    --vdev 'net_vhost,iface=vhost-net,queues=1,dmas=[txq0@00:04.0]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd> start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu2004_2.img  \
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

Test Case2: Wake up split ring virtio-net cores with event idx interrupt mode and cbdma enabled 16 queues test
==============================================================================================================

1. Bind one nic port and 16 cbdma channels to vfio-pci, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-17 -n 4 --file-prefix=vhost \
    --vdev 'net_vhost,iface=vhost-net,queues=16,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7;txq8@00:04.0;txq9@00:04.1;txq10@00:04.2;txq11@00:04.3;txq12@00:04.4;txq13@00:04.5;txq14@00:04.6;txq15@00:04.7]' \
    -- -i --nb-cores=16 --txd=1024 --rxd=1024 --rxq=16 --txq=16
    testpmd> start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=16,sockets=1 -drive file=/home/osimg/ubuntu2004_2.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net,server -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=40,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

3. On VM1, give virtio device ip addr and enable vitio-net with 16 quques::

    ifconfig [ens3] 1.1.1.2           # [ens3] is the name of virtio-net
    ethtool -L [ens3] combined 16

4. Send 10M different ip addr packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

    cat /proc/interrupts

5. After two hours stress test, stop and restart testpmd, check each queue has new packets coming::

    testpmd> stop
    testpmd> start
    testpmd> stop

Test Case3: Packed ring virtio-pci driver reload test with CBDMA enabled
========================================================================

1. Bind one nic port and one cbdma channel to vfio-pci, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --file-prefix=vhost \
    --vdev 'net_vhost,iface=vhost-net,queues=1,dmas=[txq0@00:04.0]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd> start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu2004_2.img  \
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

Test Case4: Wake up packed ring virtio-net cores with event idx interrupt mode and cbdma enabled 16 queues test
===============================================================================================================

1. Bind one nic port and 16 cbdma channels to vfio-pci, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-17 -n 4 --file-prefix=vhost \
    --vdev 'net_vhost,iface=vhost-net,queues=16,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7;txq8@00:04.0;txq9@00:04.1;txq10@00:04.2;txq11@00:04.3;txq12@00:04.4;txq13@00:04.5;txq14@00:04.6;txq15@00:04.7]' \
    -- -i --nb-cores=16 --txd=1024 --rxd=1024 --rxq=16 --txq=16
    testpmd> start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=16,sockets=1 -drive file=/home/osimg/ubuntu2004_2.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net,server -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=40,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on \
     -vnc :12 -daemonize

3. On VM1, give virtio device ip addr and enable vitio-net with 16 quques::

    ifconfig [ens3] 1.1.1.2           # [ens3] is the name of virtio-net
    ethtool -L [ens3] combined 16

4. Send 10M different ip addr packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

    cat /proc/interrupts

5. After two hours stress test, stop and restart testpmd, check each queue has new packets coming::

    testpmd> stop
    testpmd> start
    testpmd> stop

