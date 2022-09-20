.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

=====================================
vm2vm vhost-user/virtio-net test plan
=====================================

Description
===========

This test plan test several features in VM2VM topo:
1. Check Vhost tx offload (TSO and UFO) function by verifying the TSO/cksum in the TCP/IP stack and UFO/cksum
in the UDP/IP stack with vm2vm split ring and packed ring vhost-user/virtio-net mergeable path.
2. Check the payload of large packet (larger than 1MB) is valid after forwarding packets with vm2vm split ring
and packed ring vhost-user/virtio-net mergeable and non-mergeable path.
3. Check Vhost tx offload function by verifying the TSO/cksum in the TCP/IP stack with vm2vm split ring and
packed ring vhost-user/virtio-net mergeable path with CBDMA channel.
4. Multi-queues number dynamic change in vm2vm vhost-user/virtio-net with split ring and packed ring when vhost enqueue operation with multi-CBDMA channels.
Note: 
1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > v5.1.
2.For split virtqueue virtio-net with multi-queues server mode test, need qemu version > LTS 4.2.1, dut to old qemu exist reconnect issue when multi-queues test.
3.For PA mode, page by page mapping may exceed IOMMU's max capability, better to use 1G guest hugepage.

Test flow
=========

Virtio-net <-> Vhost <-> Testpmd <-> Vhost <-> Virtio-net

Test Case 1: VM2VM split ring vhost-user/virtio-net test with tcp traffic
=========================================================================

1. Launch the Vhost sample on socket 0 by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1' \
    --vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1' \
    -- -i --nb-cores=2 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2 on socket 1::

    taskset -c 32 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :10

    taskset -c 33 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

3. On VM1, set virtio device IP and run arp protocol::

    ifconfig ens5 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocol::

    ifconfig ens5 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance with different packet size between two VMs by below commands::

    Under VM1, run: `iperf -s -i 1`
    Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

6. Check 2VMs can receive and send big packets to each other::

    testpmd>show port xstats all
    Port 0 should have tx packets above 1522
    Port 1 should have rx packets above 1522

Test Case 2: VM2VM split ring vhost-user/virtio-net test with udp traffic
=========================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1' \
    --vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

3. On VM1, set virtio device IP and run arp protocol::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocol::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance between two VMs by below commands::

    Under VM1, run: `iperf -s -u -i 1`
    Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 30 -P 4 -u -b 1G -l 9000`

6. Check 2VMs can receive and send big packets to each other::

    testpmd>show port xstats all
    Port 0 should have tx packets above 1522
    Port 1 should have rx packets above 1522

Test Case 3: Check split ring virtio-net device capability
==========================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1' \
    --vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1' \
    -- -i --nb-cores=2 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2,set TSO and UFO on in qemu command::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

3. Check UFO and TSO offload status on for the Virtio-net driver on VM1 and VM2::

    Under VM1, run: `run ethtool -k ens3`
    udp-fragmentation-offload: on
    tx-tcp-segmentation: on
    tx-tcp-ecn-segmentation: on
    tx-tcp6-segmentation: on

    Under VM2, run: `run ethtool -k ens3`
    udp-fragmentation-offload: on
    tx-tcp-segmentation: on
    tx-tcp-ecn-segmentation: on
    tx-tcp6-segmentation: on

Test Case 4: VM2VM packed ring vhost-user/virtio-net test with tcp traffic
==========================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1' \
    --vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1' \
    -- -i --nb-cores=2 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2 with qemu::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

3. On VM1, set virtio device IP and run arp protocol::

    ifconfig ens5 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocol::

    ifconfig ens5 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance between two VMs by below commands::

    Under VM1, run: `iperf -s -i 1`
    Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 60`

6. Check 2VMs can receive and send big packets to each other::

    testpmd>show port xstats all
    Port 0 should have tx packets above 1522
    Port 1 should have rx packets above 1522

Test Case 5: VM2VM packed ring vhost-user/virtio-net test with udp traffic
==========================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1' \
    --vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1' \
    -- -i --nb-cores=2 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2 with qemu::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 40 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :12

3. On VM1, set virtio device IP and run arp protocol::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocol::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance between two VMs by below commands::

    Under VM1, run: `iperf -s -u -i 1`
    Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 30 -P 4 -u -b 1G -l 9000`

6. Check 2VMs can receive and send big packets to each other::

    testpmd>show port xstats all
    Port 0 should have tx packets above 1522
    Port 1 should have rx packets above 1522

Test Case 6: Check packed ring virtio-net device capability
============================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xF0000000 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1' \
    --vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1' \
    -- -i --nb-cores=2 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2 with qemu,set TSO and UFO on in qemu command::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,host_ufo=on,guest_ufo=on,guest_ecn=on,packed=on -vnc :12

3. Check UFO and TSO offload status on for the Virtio-net driver on VM1 and VM2::

    Under VM1, run: `run ethtool -k ens3`
    udp-fragmentation-offload: on
    tx-tcp-segmentation: on
    tx-tcp-ecn-segmentation: on
    tx-tcp6-segmentation: on

    Under VM2, run: `run ethtool -k ens3`
    udp-fragmentation-offload: on
    tx-tcp-segmentation: on
    tx-tcp-ecn-segmentation: on
    tx-tcp6-segmentation: on
