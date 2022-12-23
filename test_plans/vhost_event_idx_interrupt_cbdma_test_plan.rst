.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

====================================================
vhost event idx interrupt modei with CBDMA test plan
====================================================

Description
===========

Vhost event idx interrupt need test with l3fwd-power sample with CBDMA channel,
send small packets from virtio-net to vhost side, check vhost-user cores can be
wakeup status，and vhost-user cores should be sleep status after stop sending
packets from virtioside.

.. note::

   1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > 5.1, and packed ring multi-queues not support reconnect in qemu yet.
   2.For split virtqueue virtio-net with multi-queues server mode test, better to use qemu version >= 5.2.0, dut to qemu(v4.2.0~v5.1.0) exist split ring multi-queues reconnection issue.
   3.Kernel version > 4.8.0, mostly linux distribution don't support vfio-noiommu mode by default,
   so testing this case need rebuild kernel to enable vfio-noiommu.
   4.When DMA devices are bound to vfio driver, VA mode is the default and recommended. For PA mode, page by page mapping may exceed IOMMU's max capability, better to use 1G guest hugepage.
   5.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

Prerequisites
=============
Topology
--------
Test flow: Virtio-net --> Vhost-user

General set up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110
    For example:
    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

Test case
=========

Test Case 1: wake up split ring vhost-user cores with event idx interrupt mode and cbdma enabled 16 queues test
---------------------------------------------------------------------------------------------------------------

1. Bind 8 cbdma ports to vfio-pci driver, then launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=./vhost-net0,queues=16,client=1,dmas=[rxq0@0000:80:04.0;rxq1@0000:80:04.1;rxq2@0000:80:04.2;rxq3@0000:80:04.3;rxq4@0000:80:04.4;rxq5@0000:80:04.5;rxq6@0000:80:04.6;rxq7@0000:80:04.7;rxq8@0000:80:04.0;rxq9@0000:80:04.1;rxq10@0000:80:04.2]' \
    -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

2. Launch VM1 with server mode::

    taskset -c 17-25 qemu-system-x86_64 -name us-vhost-vm1 -enable-kvm -cpu host -smp 16 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net0,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,mq=on,vectors=40 -vnc :12

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=./vhost-net0,queues=16,client=1,dmas=[rxq0@0000:80:04.0;rxq1@0000:80:04.1;rxq2@0000:80:04.2;rxq3@0000:80:04.3;rxq4@0000:80:04.4;rxq5@0000:80:04.5;rxq6@0000:80:04.6;rxq7@0000:80:04.7;rxq8@0000:80:04.0;rxq9@0000:80:04.1;rxq10@0000:80:04.2]' \
    -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

4. Set vitio-net with 16 quques and give vitio-net ip address::

    ethtool -L [ens3] combined 16    # [ens3] is the name of virtio-net
    ifconfig [ens3] 1.1.1.1

5. Send packets with different IPs from virtio-net, notice to bind each vcpu to different send packets process::

    taskset -c 0 ping 1.1.1.2
    taskset -c 1 ping 1.1.1.3
    taskset -c 2 ping 1.1.1.4
    taskset -c 3 ping 1.1.1.5
    taskset -c 4 ping 1.1.1.6
    taskset -c 5 ping 1.1.1.7
    taskset -c 6 ping 1.1.1.8
    taskset -c 7 ping 1.1.1.9
    taskset -c 8 ping 1.1.1.10
    taskset -c 9 ping 1.1.1.11
    taskset -c 10 ping 1.1.1.12
    taskset -c 11 ping 1.1.1.13
    taskset -c 12 ping 1.1.1.14
    taskset -c 13 ping 1.1.1.15
    taskset -c 14 ping 1.1.1.16
    taskset -c 15 ping 1.1.1.17

6. Check vhost related cores are waked up with l3fwd-power log, such as following::

    L3FWD_POWER: lcore 1 is waked up from rx interrupt on port 0 queue 0
    ...
    ...
    L3FWD_POWER: lcore 16 is waked up from rx interrupt on port 0 queue 15

Test Case 2: wake up split ring vhost-user cores by multi virtio-net in VMs with event idx interrupt mode and cbdma enabled test
--------------------------------------------------------------------------------------------------------------------------------

1. Bind 2 cbdma ports to vfio-pci driver, then launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=./vhost-net0,queues=1,client=1,dmas=[rxq0@0000:00:04.0]' \
    --vdev 'eth_vhost1,iface=./vhost-net1,queues=1,client=1,dmas=[rxq0@0000:80:04.0]' \
    -- -p 0x3 --parse-ptype 1 --config "(0,0,1),(1,0,2)"

2. Launch VM1 and VM2 with server mode::

     taskset -c 33 \
     qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu22-04.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
     -chardev socket,server,id=char0,path=./vhost-net0,server \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,csum=on -vnc :10 -daemonize

     taskset -c 34 \
     qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu22-04-2.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,server,id=char0,path=./vhost-net1,server \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,csum=on -vnc :11 -daemonize

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=./vhost-net0,queues=1,client=1,dmas=[rxq0@0000:00:04.0]' \
    --vdev 'eth_vhost1,iface=./vhost-net1,queues=1,client=1,dmas=[rxq0@0000:80:04.0]' \
    -- -p 0x3 --parse-ptype 1 --config "(0,0,1),(1,0,2)"

4. On VM1, set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.2
    #[ens3] is the virtual device name
    ping 1.1.1.3
    #send packets to vhost

5. On VM2, also set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.4
    #[ens3] is the virtual device name
    ping 1.1.1.5
    #send packets to vhost

6. Check vhost related cores are waked up with l3fwd-power log.

Test Case 3: wake up packed ring vhost-user cores with event idx interrupt mode and cbdma enabled 16 queues test
----------------------------------------------------------------------------------------------------------------

1. Bind 8 cbdma ports to vfio-pci driver, then launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=./vhost-net0,queues=16,client=1,dmas=[rxq0@0000:80:04.0;rxq1@0000:80:04.1;rxq2@0000:80:04.2;rxq3@0000:80:04.3;rxq4@0000:80:04.4;rxq5@0000:80:04.5;rxq6@0000:80:04.6;rxq7@0000:80:04.7;rxq8@0000:80:04.0;rxq9@0000:80:04.1;rxq10@0000:80:04.2]' \
    -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

2. Launch VM1 with server mode::

    taskset -c 17-25 qemu-system-x86_64 -name us-vhost-vm1 -enable-kvm -cpu host -smp 16 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu22-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net0,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,mq=on,vectors=40,packed=on -vnc :12

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=./vhost-net0,queues=16,client=1,dmas=[rxq0@0000:80:04.0;rxq1@0000:80:04.1;rxq2@0000:80:04.2;rxq3@0000:80:04.3;rxq4@0000:80:04.4;rxq5@0000:80:04.5;rxq6@0000:80:04.6;rxq7@0000:80:04.7;rxq8@0000:80:04.0;rxq9@0000:80:04.1;rxq10@0000:80:04.2]' \
    -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

4. Set vitio-net with 16 quques and give vitio-net ip address::

    ethtool -L [ens3] combined 16    # [ens3] is the name of virtio-net
    ifconfig [ens3] 1.1.1.1

5. Send packets with different IPs from virtio-net, notice to bind each vcpu to different send packets process::

    taskset -c 0 ping 1.1.1.2
    taskset -c 1 ping 1.1.1.3
    taskset -c 2 ping 1.1.1.4
    taskset -c 3 ping 1.1.1.5
    taskset -c 4 ping 1.1.1.6
    taskset -c 5 ping 1.1.1.7
    taskset -c 6 ping 1.1.1.8
    taskset -c 7 ping 1.1.1.9
    taskset -c 8 ping 1.1.1.10
    taskset -c 9 ping 1.1.1.11
    taskset -c 10 ping 1.1.1.12
    taskset -c 11 ping 1.1.1.13
    taskset -c 12 ping 1.1.1.14
    taskset -c 13 ping 1.1.1.15
    taskset -c 14 ping 1.1.1.16
    taskset -c 15 ping 1.1.1.17

6. Check vhost related cores are waked up with l3fwd-power log, such as following::

    L3FWD_POWER: lcore 1 is waked up from rx interrupt on port 0 queue 0
    ...
    ...
    L3FWD_POWER: lcore 16 is waked up from rx interrupt on port 0 queue 15

Test Case 4: wake up packed ring vhost-user cores by multi virtio-net in VMs with event idx interrupt mode and cbdma enabled test
---------------------------------------------------------------------------------------------------------------------------------

1. Bind 2 cbdma ports to vfio-pci driver, then launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=./vhost-net0,queues=1,client=1,dmas=[rxq0@0000:00:04.0]' \
    --vdev 'eth_vhost1,iface=./vhost-net1,queues=1,client=1,dmas=[rxq0@0000:80:04.0]' \
    -- -p 0x3 --parse-ptype 1 --config "(0,0,1),(1,0,2)"

2. Launch VM1 and VM2 with server mode::

     taskset -c 33 \
     qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu22-04.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
     -chardev socket,server,id=char0,path=./vhost-net0,server \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,csum=on,packed=on -vnc :10 -daemonize

     taskset -c 34 \
     qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu22-04-2.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,server,id=char0,path=./vhost-net1,server \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,csum=on,packed=on -vnc :11 -daemonize

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=./vhost-net0,queues=1,client=1,dmas=[rxq0@0000:00:04.0]' \
    --vdev 'eth_vhost1,iface=./vhost-net1,queues=1,client=1,dmas=[rxq0@0000:80:04.0]' \
    -- -p 0x3 --parse-ptype 1 --config "(0,0,1),(1,0,2)"

4. On VM1, set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.2
    #[ens3] is the virtual device name
    ping 1.1.1.3
    #send packets to vhost

5. On VM2, also set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.4
    #[ens3] is the virtual device name
    ping 1.1.1.5
    #send packets to vhost

6. Check vhost related cores are waked up with l3fwd-power log.
