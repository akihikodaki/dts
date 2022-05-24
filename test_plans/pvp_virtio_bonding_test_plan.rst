.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

===========================================
vhost-user/virtio-pmd pvp bonding test plan
===========================================

Description
===========

The Link Bonding functions make it possible to dynamically create and manage link bonding devices from within testpmd interactive prompt, below are the introduction of seven bonding modes：
- Mode = 0 (balance-rr) Round-robin policy: (default).
- Mode = 1 (active-backup) Active-backup policy: Only one NIC slave in the bond is active.
- Mode = 2 (balance-xor) XOR policy: Transmit network packets based on the default transmit policy.
- Mode = 3 (broadcast) Broadcast policy: Transmit network packets on all slave network interfaces.
- Mode = 4 (802.3ad) IEEE 802.3ad Dynamic link aggregation.
- Mode = 5 (balance-tlb) Adaptive transmit load balancing.
- Mode = 6 (balance-alb) Adaptive load balancing.

Test case 1: vhost-user/virtio-pmd pvp bonding test with mode 0
===============================================================
Flow: TG--> NIC --> Vhost --> Virtio3 --> Virtio4 --> Vhost--> NIC--> TG

1. Bind one port to vfio-pci,launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-6 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1' --vdev 'net_vhost2,iface=vhost-net2,client=1,queues=1' --vdev 'net_vhost3,iface=vhost-net3,client=1,queues=1'  -- -i --port-topology=chained --nb-cores=4 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Bootup one vm with four virtio-net devices::

    qemu-system-x86_64 -name vm0 -enable-kvm -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
    -device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 \
    -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
    -net nic,macaddr=00:00:00:c7:56:64,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6008-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01 \
    -chardev socket,id=char1,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev1,chardev=char1,vhostforce \
    -device virtio-net-pci,netdev=netdev1,mac=52:54:00:00:00:02 \
    -chardev socket,id=char2,path=./vhost-net2,server \
    -netdev type=vhost-user,id=netdev2,chardev=char2,vhostforce \
    -device virtio-net-pci,netdev=netdev2,mac=52:54:00:00:00:03 \
    -chardev socket,id=char3,path=./vhost-net3,server \
    -netdev type=vhost-user,id=netdev3,chardev=char3,vhostforce \
    -device virtio-net-pci,netdev=netdev3,mac=52:54:00:00:00:04 \
    -cpu host -smp 8 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img -vnc :10

3. On vm, bind four virtio-net devices to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci xx:xx.x xx:xx.x xx:xx.x xx:xx.x

4. Launch testpmd in VM::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 0-5 -n 4 -- -i --port-topology=chained --nb-cores=5

5. Create one bonded device in mode 0 on socket 0::

    testpmd>create bonded device 0 0        # create bonded device (mode) (socket)
    created new bonded device on (port 4)   # in this case, already has port 0,1,2,3 for vdev, so the bonded device port is 4

6. Add three vdev (port 0,1,2) to link bonding device (port 4) and configure forwarding on port 3 and port 4::

    testpmd>add bonding slave 0 4     # add bonding slave (slave id) (port id)
    testpmd>add bonding slave 1 4
    testpmd>add bonding slave 2 4
    testpmd>port start 4
    testpmd>show bonding config 4
    testpmd>set portlist 3,4
    testpmd>set fwd mac
    testpmd>start

7. Send packets to nic port by packet generator.

8. Check port stats at VM side, there are throughput between port 3 and port 4::

    testpmd>show port stats all

Test case 2: vhost-user/virtio-pmd pvp bonding test with different mode from 1 to 6
===================================================================================

1. Bind one port to vfio-pci,launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-6 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1' --vdev 'net_vhost2,iface=vhost-net2,client=1,queues=1' --vdev 'net_vhost3,iface=vhost-net3,client=1,queues=1'  -- -i --port-topology=chained --nb-cores=4 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Bootup one vm with four virtio-net devices::

    qemu-system-x86_64 -name vm0 -enable-kvm -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
    -device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 \
    -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
    -net nic,macaddr=00:00:00:c7:56:64,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6008-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01 \
    -chardev socket,id=char1,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev1,chardev=char1,vhostforce \
    -device virtio-net-pci,netdev=netdev1,mac=52:54:00:00:00:02 \
    -chardev socket,id=char2,path=./vhost-net2,server \
    -netdev type=vhost-user,id=netdev2,chardev=char2,vhostforce \
    -device virtio-net-pci,netdev=netdev2,mac=52:54:00:00:00:03 \
    -chardev socket,id=char3,path=./vhost-net3,server \
    -netdev type=vhost-user,id=netdev3,chardev=char3,vhostforce \
    -device virtio-net-pci,netdev=netdev3,mac=52:54:00:00:00:04 \
    -cpu host -smp 8 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img -vnc :10

3. On vm, bind four virtio-net devices to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci xx:xx.x xx:xx.x xx:xx.x xx:xx.x

4. Launch testpmd in VM::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 0-5 -n 4 -- -i --port-topology=chained --nb-cores=5

5. Create bonding device with mode 1 to mode 6::

    testpmd> create bonded device (mode) 0

6. Add three vdev (port 0,1,2) to link bonding device (port 4) and configure forwarding on port 3 and port 4::

    testpmd>add bonding slave 0 4     # add bonding slave (slave id) (port id)
    testpmd>add bonding slave 1 4
    testpmd>add bonding slave 2 4
    testpmd>port start 4
    testpmd>show bonding config 4
    testpmd>set portlist 3,4
    testpmd>set fwd mac
    testpmd>start