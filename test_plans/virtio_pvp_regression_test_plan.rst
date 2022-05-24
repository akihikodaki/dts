.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

==========================================
vhost/virtio-pmd qemu regression test plan
==========================================

Add feature combind cases to capture regression issue: cover 2 queues
+ reconnect + multi qemu version + multi-paths with virtio1.0,
virtio0.95 and virtio 1.1. For packed virtqueue (virtio 1.1) test,
need using qemu version > 4.2.0. The qemu launch parameters
(rx_queue_size=1024,tx_queue_size=1024) only can be supported with qemu
version greater or equal to 2.10.

Test flow
=========

TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Test Case 1: pvp test with virtio 0.95 mergeable path
=====================================================

1. Bind one port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1' -- -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed different version qemu, includes [qemu_2.7, qemu_2.8, qemu_2.9, qemu_2.10, qemu_2.11, qemu_2.12, qemu_3.0], launch VM with different qemu version separately::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 3 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=2  \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,mq=on,vectors=15 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd without tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 4 -- -i --enable-hw-vlan-strip\
    --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send 64B and 1518B packets by packet generator separately, show throughput with below command::

    testpmd>show port stats all

5. Quit vhost-user, then re-launch, check if the reconnect can work and ensure the traffic can continue.

6. Kill VM, then re-launch VM, check if the reconnect can work and ensure the traffic can continue.

Test Case 2: pvp test with virtio 0.95 non-mergeable path
=========================================================

1. Bind one port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1' -- -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed different version qemu, includes [qemu_2.7, qemu_2.8, qemu_2.9, qemu_2.10, qemu_2.11, qemu_2.12, qemu_3.0], launch VM with different qemu version separately::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 3 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=2  \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024,mq=on,vectors=15 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd without tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 4 -- -i --enable-hw-vlan-strip\
    --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send 64B and 1518B packets by packet generator separately, show throughput with below command::

    testpmd>show port stats all

5. Quit vhost-user, then re-launch, check if the reconnect can work and ensure the traffic can continue.

6. Kill VM, then re-launch VM, check if the reconnect can work and ensure the traffic can continue.

Test Case 3: pvp test with virtio 0.95 vrctor_rx path
=====================================================

1. Bind one port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1' -- -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed different version qemu, includes [qemu_2.7, qemu_2.8, qemu_2.9, qemu_2.10, qemu_2.11, qemu_2.12, qemu_3.0], launch VM with different qemu version separately::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 3 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=2  \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024,mq=on,vectors=15 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd without tx-offloads, [0000:xx.00] is [Bus,Device,Function] of virtio-net::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 3 -a 0000:xx.00,vectorized -- -i \
    --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send 64B and 1518B packets by packet generator separately, show throughput with below command::

    testpmd>show port stats all

5. Quit vhost-user, then re-launch, check if the reconnect can work and ensure the traffic can continue.

6. Kill VM, then re-launch VM, check if the reconnect can work and ensure the traffic can continue.

Test Case 4: pvp test with virtio 1.0 mergeable path
====================================================

1. Bind one port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1' -- -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed different version qemu, includes [qemu_2.7, qemu_2.8, qemu_2.9, qemu_2.10, qemu_2.11, qemu_2.12, qemu_3.0], launch VM with different qemu version separately, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 3 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=2  \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,mq=on,vectors=15 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd without tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 4 -- -i --enable-hw-vlan-strip\
    --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send 64B and 1518B packets by packet generator separately, show throughput with below command::

    testpmd>show port stats all

5. Quit vhost-user, then re-launch, check if the reconnect can work and ensure the traffic can continue.

6. Kill VM, then re-launch VM, check if the reconnect can work and ensure the traffic can continue.

Test Case 5: pvp test with virtio 1.0 non-mergeable path
========================================================

1. Bind one port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1' -- -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed different version qemu, includes [qemu_2.7, qemu_2.8, qemu_2.9, qemu_2.10, qemu_2.11, qemu_2.12, qemu_3.0], launch VM with different qemu version separately, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 3 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=2  \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024,mq=on,vectors=15 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd without tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 4 -- -i --enable-hw-vlan-strip\
    --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send 64B and 1518B packets by packet generator separately, show throughput with below command::

    testpmd>show port stats all

5. Quit vhost-user, then re-launch, check if the reconnect can work and ensure the traffic can continue.

6. Kill VM, then re-launch VM, check if the reconnect can work and ensure the traffic can continue.

Test Case 6: pvp test with virtio 1.0 vrctor_rx path
====================================================

1. Bind one port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1' -- -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed different version qemu, includes [qemu_2.7, qemu_2.8, qemu_2.9, qemu_2.10, qemu_2.11, qemu_2.12, qemu_3.0], launch VM with different qemu version separately, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 3 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=2  \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024,mq=on,vectors=15 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd without tx-offloads, [0000:xx.00] is [Bus,Device,Function] of virtio-net::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 3 -a 0000:xx.00,vectorized -- -i \
    --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send 64B and 1518B packets by packet generator separately, show throughput with below command::

    testpmd>show port stats all

5. Quit vhost-user, then re-launch, check if the reconnect can work and ensure the traffic can continue.

6. Kill VM, then re-launch VM, check if the reconnect can work and ensure the traffic can continue.

Test Case 7: pvp test with virtio 1.1 mergeable path
====================================================

1. Bind one port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1' -- -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed qemu 4.2.0, then launch VM::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 3 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,mq=on,vectors=15,packed=on -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd without tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 4 -- -i --enable-hw-vlan-strip \
    --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send 64B and 1518B packets by packet generator separately, show throughput with below command::

    testpmd>show port stats all

5. Quit vhost-user, then re-launch, check if the reconnect can work and ensure the traffic can continue.

6. Kill VM, then re-launch VM, check if the reconnect can work and ensure the traffic can continue.

Test Case 8: pvp test with virtio 1.1 non-mergeable path
=========================================================

1. Bind one port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-3 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1' -- -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Check dut machine already has installed qemu 4.2.0, then launch VM::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 3 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024,mq=on,vectors=15,packed=on -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd without tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 4 -- -i --enable-hw-vlan-strip \
    --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send 64B and 1518B packets by packet generator separately, show throughput with below command::

    testpmd>show port stats all

5. Quit vhost-user, then re-launch, check if the reconnect can work and ensure the traffic can continue.

6. Kill VM, then re-launch VM, check if the reconnect can work and ensure the traffic can continue.
