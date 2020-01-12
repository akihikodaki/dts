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
vm2vm vhost-user/virtio-net test plan
=====================================

Description
===========

This test plan test vhost tx offload (TSO and UFO) function by verifing the TSO/cksum in the TCP/IP stack enabled environment and UFO/cksum in the UDP/IP stack enabled environment with vm2vm split ring and packed ring vhost-user/virtio-net non-mergeable path. Also add case to check the payload of large packet is valid with vm2vm split ring and packed ring vhost-user/virtio-net mergeable and non-mergeable dequeue zero copy test. For packed virtqueue test, need using qemu version > 4.2.0.

Test flow
=========

Virtio-net <-> Vhost <-> Testpmd <-> Vhost <-> Virtio-net

Test Case 1: VM2VM split ring vhost-user/virtio-net test with tcp traffic
=========================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -l 2-4 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=2 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :11 -daemonize

3. On VM1, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance between two VMs by below commands::

    Under VM1, run: `iperf -s -i 1`
    Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 30`

6. Check both 2VMs can receive and send big packets to each other::

    testpmd>show port xstats all
    Port 0 should have tx packets above 1522
    Port 1 should have rx packets above 1522

7. Check iperf throughput can get expected data.

Test Case 2: VM2VM split ring vhost-user/virtio-net dequeue zero-copy test with tcp traffic
===========================================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -l 2-4 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1,dequeue-zero-copy=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1,dequeue-zero-copy=1'  -- -i --nb-cores=2 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :11 -daemonize

3. On VM1, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance between two VMs by below commands::

    Under VM1, run: `iperf -s -i 1`
    Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 30`

6. Check both 2VMs can receive and send big packets to each other::

    testpmd>show port xstats all
    Port 0 should have tx packets above 1522
    Port 1 should have rx packets above 1522

7. Check iperf throughput can get expected data.

Test Case 3: VM2VM split ring vhost-user/virtio-net test with udp traffic
=========================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    testpmd>./testpmd -c 0xF0000000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :11 -daemonize

3. On VM1, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance between two VMs by below commands::

    Under VM1, run: `iperf -s -u -i 1`
    Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 30 -P 4 -u -b 1G -l 9000`

6. Check both 2VMs can receive and send big packets to each other::

    testpmd>show port xstats all
    Port 0 should have tx packets above 1522
    Port 1 should have rx packets above 1522

Test Case 4: Check split ring virtio-net device capability
==========================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    testpmd>./testpmd -c 0xF0000000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2,set TSO and UFO on in qemu command::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :11 -daemonize

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

Test Case 5: VM2VM virtio-net split ring mergeable zero copy test with large packet payload valid check
=======================================================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xF0000000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1,dequeue-zero-copy=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1,dequeue-zero-copy=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=on  \
     -vnc :11 -daemonize

3. On VM1, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Scp 64KB file form VM1 to VM2::

    Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

Test Case 6: VM2VM virtio-net split ring non-mergeable zero copy test with large packet payload valid check
===========================================================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xF0000000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1,dequeue-zero-copy=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1,dequeue-zero-copy=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off  \
     -vnc :11 -daemonize

3. On VM1, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Scp 64KB file form VM1 to VM2::

    Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

Test Case 7: VM2VM packed ring vhost-user/virtio-net test with tcp traffic
==========================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -l 2-4 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=2 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on \
     -vnc :11 -daemonize

3. On VM1, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance between two VMs by below commands::

    Under VM1, run: `iperf -s -i 1`
    Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 30`

6. Check both 2VMs can receive and send big packets to each other::

    testpmd>show port xstats all
    Port 0 should have tx packets above 1522
    Port 1 should have rx packets above 1522

7. Check iperf throughput can get expected data.

Test Case 8: VM2VM packed ring vhost-user/virtio-net dequeue zero-copy test with tcp traffic
============================================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -l 2-4 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1,dequeue-zero-copy=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1,dequeue-zero-copy=1'  -- -i --nb-cores=2 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on \
     -vnc :11 -daemonize

3. On VM1, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance between two VMs by below commands::

    Under VM1, run: `iperf -s -i 1`
    Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 30`

6. Check both 2VMs can receive and send big packets to each other::

    testpmd>show port xstats all
    Port 0 should have tx packets above 1522
    Port 1 should have rx packets above 1522

7. Check iperf throughput can get expected data.

Test Case 9: VM2VM packed ring vhost-user/virtio-net test with udp traffic
==========================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    testpmd>./testpmd -c 0xF0000000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :11 -daemonize

3. On VM1, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Check the iperf performance between two VMs by below commands::

    Under VM1, run: `iperf -s -u -i 1`
    Under VM2, run: `iperf -c 1.1.1.2 -i 1 -t 30 -P 4 -u -b 1G -l 9000`

6. Check both 2VMs can receive and send big packets to each other::

    testpmd>show port xstats all
    Port 0 should have tx packets above 1522
    Port 1 should have rx packets above 1522

Test Case 10: Check packed ring virtio-net device capability
===========================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    testpmd>./testpmd -c 0xF0000000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2,set TSO and UFO on in qemu command::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :11 -daemonize

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

Test Case 11: VM2VM packed ring virtio-net mergeable dequeue zero copy test with large packet payload valid check
=================================================================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xF0000000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1,dequeue-zero-copy=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1,dequeue-zero-copy=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,packed=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=on,packed=on \
     -vnc :11 -daemonize

3. On VM1, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Scp 64KB file form VM1 to VM2::

    Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name

Test Case 12: VM2VM packed ring virtio-net non-mergeable dequeue zero copy test with large packet payload valid check
=====================================================================================================================

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xF0000000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1,dequeue-zero-copy=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1,dequeue-zero-copy=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,packed=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,packed=on  \
     -vnc :11 -daemonize

3. On VM1, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.2
    arp -s 1.1.1.8 52:54:00:00:00:02

4. On VM2, set virtio device IP and run arp protocal::

    ifconfig ens3 1.1.1.8
    arp -s 1.1.1.2 52:54:00:00:00:01

5. Scp 64KB file form VM1 to VM2::

    Under VM1, run: `scp [xxx] root@1.1.1.8:/`   [xxx] is the file name
