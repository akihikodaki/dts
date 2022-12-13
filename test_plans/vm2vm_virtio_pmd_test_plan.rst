.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

=====================================
vm2vm vhost-user/virtio-pmd test plan
=====================================

This test plan includes vm2vm mergeable, normal and vector_rx path test with virtio 0.95 and virtio 1.0,
also add mergeable and normal path test with virtio 1.1. Specially, three mergeable path cases check the
payload of each packets are valid by using pdump.

Test flow
=========
Virtio-pmd <-> Vhost-user <-> Testpmd <-> Vhost-user <-> Virtio-pmd

Test Case 1: VM2VM vhost-user/virtio0.95-pmd with vector_rx path
================================================================

1. Launch the testpmd by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=off to disable mergeable::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

3. On VM1, bind vdev with vfio-pci driver,then run testpmd, set rxonly for virtio1, [0000:00:04.0] is [Bus,Device,Function] of virtio-net::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -a 0000:00:04.0,vectorized=1 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with vfio-pci driver,then run testpmd, set txonly for virtio2 and send 64B packets, [0000:00:04.0] is [Bus,Device,Function] of virtio-net::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -a 0000:00:04.0,vectorized=1 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    ...
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 2: VM2VM vhost-user/virtio0.95-pmd with normal path
=============================================================

1. Launch the testpmd by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=off to disable mergeable::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

3. On VM1, bind vdev with vfio-pci driver,then run testpmd, set rxonly for virtio1 ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with vfio-pci driver,then run testpmd, set rxonly for virtio2 and send 64B packets ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    ...
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 3: VM2VM vhost-user/virtio1.0-pmd with vector_rx path
===============================================================

1. Launch the testpmd by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, note add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

3. On VM1, bind vdev with vfio-pci driver,then run testpmd, set rxonly for virtio1, [0000:00:04.0] is [Bus,Device,Function] of virtio-net::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -a 0000:00:04.0,vectorized=1 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with vfio-pci driver,then run testpmd, set txonly for virtio2, [0000:00:04.0] is [Bus,Device,Function] of virtio-net::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -a 0000:00:04.0,vectorized=1 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    ...
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 4: VM2VM vhost-user/virtio1.0-pmd with normal path
============================================================

1. Launch the testpmd by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, note add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

3. On VM1, bind vdev with vfio-pci driver,then run testpmd, set rxonly for virtio1 ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with vfio-pci driver,then run testpmd, set txonly for virtio2 ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    ...
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 5: VM2VM vhost-user/virtio0.95-pmd mergeable path with payload valid check
====================================================================================

1. Launch the testpmd by below commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=on to enable mergeable path::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

3. Bind virtio with vfio-pci driver,then run testpmd, set rxonly mode for virtio-pmd on VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 --file-prefix=test -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd>set fwd rxonly
    testpmd>start

4. Bootup pdump in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=test -- --pdump  'port=0,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

5. On VM2, bind virtio with vfio-pci driver,then run testpmd, config tx_packets to 8k length with chain mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd>set fwd mac
    testpmd>set txpkts 2000,2000,2000,2000

6. Send ten packets with 8k length from virtio-pmd on VM2::

    testpmd>set burst 1
    testpmd>start tx_first 10

7. Check payload is correct in each dumped packets.

8. Relaunch testpmd in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 --file-prefix=test -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

9. Bootup pdump in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=test -- --pdump  'port=0,queue=*,rx-dev=/root/pdump-rx-small.pcap,mbuf-size=8000'

10. Relaunch testpmd on VM2, send ten 64B packets from virtio-pmd on VM2::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024
     testpmd>set fwd mac
     testpmd>set burst 1
     testpmd>start tx_first 10

11. Check payload is correct in each dumped packets.

Test Case 6: VM2VM vhost-user/virtio1.0-pmd mergeable path with payload valid check
===================================================================================

1. Launch the testpmd by below commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=on to enable mergeable path::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

3. Bind virtio with vfio-pci driver,then run testpmd, set rxonly mode for virtio-pmd on VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 --file-prefix=test -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd>set fwd rxonly
    testpmd>start

4. Bootup pdump in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=test -- --pdump  'port=0,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

5. On VM2, bind virtio with vfio-pci driver,then run testpmd, config tx_packets to 8k length with chain mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd>set fwd mac
    testpmd>set txpkts 2000,2000,2000,2000

6. Send ten packets from virtio-pmd on VM2::

    testpmd>set burst 1
    testpmd>start tx_first 10

7. Check payload is correct in each dumped packets.

8. Relaunch testpmd in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 --file-prefix=test -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

9. Bootup pdump in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=test -- --pdump  'port=0,queue=*,rx-dev=/root/pdump-rx-small.pcap'

10. Relaunch testpmd On VM2, send ten 64B packets from virtio-pmd on VM2::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
     testpmd>set fwd mac
     testpmd>set burst 1
     testpmd>start tx_first 10

11. Check payload is correct in each dumped packets.

Test Case 7: VM2VM vhost-user/virtio1.1-pmd mergeable path with payload valid check
===================================================================================

1. Launch the testpmd by below commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=on to enable mergeable path::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

3. Bind virtio with vfio-pci driver,then run testpmd, set rxonly mode for virtio-pmd on VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 --file-prefix=test -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd>set fwd rxonly
    testpmd>start

4. Bootup pdump in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=test -- --pdump  'port=0,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

5. On VM2, bind virtio with vfio-pci driver,then run testpmd, config tx_packets to 8k length with chain mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
    testpmd>set fwd mac
    testpmd>set txpkts 2000,2000,2000,2000

6. Send ten packets from virtio-pmd on VM2::

    testpmd>set burst 1
    testpmd>start tx_first 10

7. Check payload is correct in each dumped packets.

8. Relaunch testpmd in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 --file-prefix=test -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

9. Bootup pdump in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=test -- --pdump  'port=0,queue=*,rx-dev=/root/pdump-rx-small.pcap'

10. Relaunch testpmd On VM2, send ten 64B packets from virtio-pmd on VM2::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600 --rx-offloads=0x00002000
     testpmd>set fwd mac
     testpmd>set burst 1
     testpmd>start tx_first 10

11. Check payload is correct in each dumped packets.

Test Case 8: VM2VM vhost-user/virtio1.1-pmd with normal path
============================================================

1. Launch the testpmd by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, note add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

3. On VM1, bind vdev with vfio-pci driver,then run testpmd, set rxonly for virtio1 ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with vfio-pci driver,then run testpmd, set txonly for virtio2 ::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    ...
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx
