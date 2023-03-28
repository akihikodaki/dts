.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

========================================================
vhost/virtio qemu multi-paths and port restart test plan
========================================================

Description
===========

Benchmark pvp qemu test with 3 tx/rx paths,includes mergeable, normal, vector_rx.
Cover virtio 1.1, virtio 1.0, virtio 0.95, also cover port restart test with each path.

Test flow
=========

TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Test Case 1: pvp test with virtio 0.95 mergeable path
=====================================================

1. Bind 1 NIC port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 -a 0000:af:00.0 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with mrg_rxbuf feature on::

    qemu-system-x86_64 -name vm0 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm0_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1 -a 0000:04:00.0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>port stop 0
    testpmd>show port stats 0

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>clear port stats all
    testpmd>port start all
    testpmd>start
    testpmd>show port stats 0

Test Case 2: pvp test with virtio 0.95 normal path
==================================================

1. Bind 1 NIC port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 -a 0000:af:00.0 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with mrg_rxbuf feature off::

    qemu-system-x86_64 -name vm0 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm0_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd with tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1 -a 0000:04:00.0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>port stop 0
    testpmd>show port stats 0

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>clear port stats all
    testpmd>port start all
    testpmd>start
    testpmd>show port stats 0

Test Case 3: pvp test with virtio 0.95 vector_rx path
=====================================================

1. Bind 1 NIC port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 -a 0000:af:00.0 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with mrg_rxbuf feature off::

    qemu-system-x86_64 -name vm0 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm0_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=true,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd without ant tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1 -a 0000:04:00.0,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>port stop 0
    testpmd>show port stats 0

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>clear port stats all
    testpmd>port start all
    testpmd>start
    testpmd>show port stats 0

Test Case 4: pvp test with virtio 1.0 mergeable path
====================================================

1. Bind 1 NIC port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 -a 0000:af:00.0 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with 1 virtio, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm0 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm0_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1 -a 0000:04:00.0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>port stop 0
    testpmd>show port stats 0

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>clear port stats all
    testpmd>port start all
    testpmd>start
    testpmd>show port stats 0

Test Case 5: pvp test with virtio 1.0 normal path
=================================================

1. Bind 1 NIC port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 -a 0000:af:00.0 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with 1 virtio, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm0 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm0_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd with tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1 -a 0000:04:00.0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>port stop 0
    testpmd>show port stats 0

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>clear port stats all
    testpmd>port start all
    testpmd>start
    testpmd>show port stats 0

Test Case 6: pvp test with virtio 1.0 vector_rx path
====================================================

1. Bind 1 NIC port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 -a 0000:af:00.0 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with 1 virtio, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm0 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm0_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd without tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1 -a 0000:04:00.0,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>port stop 0
    testpmd>show port stats 0

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>clear port stats all
    testpmd>port start all
    testpmd>start
    testpmd>show port stats 0

Test Case 7: pvp test with virtio 1.1 mergeable path
====================================================

1. Bind 1 NIC port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 -a 0000:af:00.0 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with 1 virtio, note: we need add "disable-modern=false" to enable virtio 1.1::

    qemu-system-x86_64 -name vm0 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm0_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,packed=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1 -a 0000:04:00.0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>port stop 0
    testpmd>show port stats 0

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>clear port stats all
    testpmd>port start all
    testpmd>start
    testpmd>show port stats 0

Test Case 8: pvp test with virtio 1.1 normal path
=================================================

1. Bind 1 NIC port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 -a 0000:af:00.0 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with 1 virtio, note: we need add "disable-modern=false" to enable virtio 1.1::

    qemu-system-x86_64 -name vm0 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm0_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,packed=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd with tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1 -a 0000:04:00.0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>port stop 0
    testpmd>show port stats 0

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>clear port stats all
    testpmd>port start all
    testpmd>start
    testpmd>show port stats 0

Test Case 9: pvp test with virtio 1.1 vector_rx path
====================================================

1. Bind 1 NIC port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 -a 0000:af:00.0 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with 1 virtio, note: we need add "disable-modern=false" to enable virtio 1.1::

    qemu-system-x86_64 -name vm0 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm0_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,packed=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd without tx-offloads::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1 -a 0000:04:00.0,vectorized=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1280,1518), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>port stop 0
    testpmd>show port stats 0

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>clear port stats all
    testpmd>port start all
    testpmd>start
    testpmd>show port stats 0

Test Case 10: pvp test with virtio 1.0 mergeable path restart 10 times
======================================================================

1. Bind 1 NIC port to vfio-pci, then launch testpmd by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 -a 0000:af:00.0 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with 1 virtio, note: we need add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name vm0 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm0_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1 -a 0000:04:00.0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator with different packet sizes(64), show throughput with below command::

    testpmd>show port stats all

5. Stop port at vhost side by below command and re-calculate the average throughput,verify the throughput is zero after port stop::

    testpmd>stop
    testpmd>port stop 0
    testpmd>show port stats 0

6. Restart port at vhost side by below command and re-calculate the average throughput,verify the throughput is not zero after port restart::

    testpmd>clear port stats all
    testpmd>port start all
    testpmd>start
    testpmd>show port stats 0

7. Rerun steps 4-6 10 times to check stability.
