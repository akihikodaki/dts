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

=====================================
vm2vm vhost-user/virtio-pmd test plan
=====================================

This test plan includes vm2vm vhost-user/virtio-pmd(0.95) mergeable ,normal and vector_rx path test, and vm2vm vhost/virtio-pmd(1.0) mergeable,
normal and vector_rx path test. Specially, two mergeable path test check the payload of each packets are valid by using pdump.

Prerequisites
=============

Enable pcap lib in dpdk code and recompile::

    --- a/config/common_base
    +++ b/config/common_base
    @@ -492,7 +492,7 @@ CONFIG_RTE_LIBRTE_PMD_NULL=y
     #
     # Compile software PMD backed by PCAP files
     #
    -CONFIG_RTE_LIBRTE_PMD_PCAP=n
    +CONFIG_RTE_LIBRTE_PMD_PCAP=y

Test flow
=========
Virtio-pmd <-> Vhost-user <-> Testpmd <-> Vhost-user <-> Virtio-pmd

Test Case 1: VM2VM vhost-user/virtio-pmd with vector_rx path
============================================================

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

     rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=off to disable mergeable::

    qemu-system-x86_64 -name us-vhost-vm0 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on  \
     -vnc :11 -daemonize

3. On VM1, bind vdev with igb_uio driver,then run testpmd, set rxonly for virtio1::

    ./testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with igb_uio driver,then run testpmd, set txonly for virtio2 and send 64B packets::

    ./testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    xxxxx
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 2: VM2VM vhost-user/virtio-pmd with normal path
=========================================================

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

     rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=off to disable mergeable::

    qemu-system-x86_64 -name us-vhost-vm0 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on  \
     -vnc :11 -daemonize

3. On VM1, bind vdev with igb_uio driver,then run testpmd, set rxonly for virtio1 ::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with igb_uio driver,then run testpmd, set rxonly for virtio2 and send 64B packets ::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    xxxxx
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 3: VM2VM vhost-user/virtio1.0-pmd with vector_rx path
===============================================================

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

     rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, note add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,disable-modern=false,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,disable-modern=false,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on  \
     -vnc :11 -daemonize

3. On VM1, bind vdev with igb_uio driver,then run testpmd, set rxonly for virtio1 ::

    ./testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with igb_uio driver,then run testpmd, set txonly for virtio2 ::

    ./testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    xxxxx
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 4: VM2VM vhost-user/virtio1.0-pmd with normal path
============================================================

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

     rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, note add "disable-modern=false" to enable virtio 1.0::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,disable-modern=false,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,disable-modern=false,mrg_rxbuf=off,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on  \
     -vnc :11 -daemonize

3. On VM1, bind vdev with igb_uio driver,then run testpmd, set rxonly for virtio1 ::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with igb_uio driver,then run testpmd, set txonly for virtio2 ::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    xxxxx
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 5: VM2VM vhost-user/virtio-pmd mergeable path with payload valid check
================================================================================

1. Bind virtio with igb_uio driver, launch the testpmd by below commands::

    ./testpmd -c 0xc0000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=on to enable mergeable path::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6003-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :11 -daemonize

3. On VM1, enable pcap lib in dpdk code and recompile::

    diff --git a/config/common_base b/config/common_base
    index 6b96e0e80..0f7d22f22 100644
    --- a/config/common_base
    +++ b/config/common_base
    @@ -492,7 +492,7 @@ CONFIG_RTE_LIBRTE_PMD_NULL=y
     #
     # Compile software PMD backed by PCAP files
     #
    -CONFIG_RTE_LIBRTE_PMD_PCAP=n
    +CONFIG_RTE_LIBRTE_PMD_PCAP=y

4. Bind virtio with igb_uio driver,then run testpmd, set rxonly mode for virtio-pmd on VM1::

    ./testpmd -c 0x3 -n 4 --file-prefix=test -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set fwd rxonly
    testpmd>start

5. Bootup pdump in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=test -- --pdump  'port=0,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

6. On VM2, bind virtio with igb_uio driver,then run testpmd, config tx_packets to 8k length with chain mode::

    ./testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set fwd mac
    testpmd>set txpkts 2000,2000,2000,2000

7. Send ten packets with 8k length from virtio-pmd on VM2::

    testpmd>set burst 1
    testpmd>start tx_first 10

8. Check payload is correct in each dumped packets.

9. Relaunch testpmd in VM1::

    ./testpmd -c 0x3 -n 4 --file-prefix=test -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

10. Bootup pdump in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=test -- --pdump  'port=0,queue=*,rx-dev=/root/pdump-rx-small.pcap,mbuf-size=8000'

11. Relaunch testpmd on VM2, send ten 64B packets from virtio-pmd on VM2::

     ./testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024
     testpmd>set fwd mac
     testpmd>set burst 1
     testpmd>start tx_first 10

12. Check payload is correct in each dumped packets.

Test Case 6: VM2VM vhost-user/virtio1.0-pmd mergeable path with payload valid check
===================================================================================

1. Bind virtio with igb_uio driver, launch the testpmd by below commands::

    ./testpmd -c 0xc0000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2, mrg_rxbuf=on to enable mergeable path::

    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,disable-modern=false,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6003-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,disable-modern=false,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :11 -daemonize

3. On VM1, enable pcap lib in dpdk code and recompile::

    diff --git a/config/common_base b/config/common_base
    index 6b96e0e80..0f7d22f22 100644
    --- a/config/common_base
    +++ b/config/common_base
    @@ -492,7 +492,7 @@ CONFIG_RTE_LIBRTE_PMD_NULL=y
     #
     # Compile software PMD backed by PCAP files
     #
    -CONFIG_RTE_LIBRTE_PMD_PCAP=n
    +CONFIG_RTE_LIBRTE_PMD_PCAP=y

4. Bind virtio with igb_uio driver,then run testpmd, set rxonly mode for virtio-pmd on VM1::

    ./testpmd -c 0x3 -n 4 --file-prefix=test -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set fwd rxonly
    testpmd>start

5. Bootup pdump in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=test -- --pdump  'port=0,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

6. On VM2, bind virtio with igb_uio driver,then run testpmd, config tx_packets to 8k length with chain mode::

    ./testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set fwd mac
    testpmd>set txpkts 2000,2000,2000,2000

7. Send ten packets from virtio-pmd on VM2::

    testpmd>set burst 1
    testpmd>start tx_first 10

8. Check payload is correct in each dumped packets.

9. Relaunch testpmd in VM1::

    ./testpmd -c 0x3 -n 4 --file-prefix=test -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

10. Bootup pdump in VM1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=test -- --pdump  'port=0,queue=*,rx-dev=/root/pdump-rx-small.pcap'

11. Relaunch testpmd On VM2, send ten 64B packets from virtio-pmd on VM2::

     ./testpmd -c 0x3 -n 4 -- -i --txd=1024 --rxd=1024 --max-pkt-len=9600
     testpmd>set fwd mac
     testpmd>set burst 1
     testpmd>start tx_first 10

12. Check payload is correct in each dumped packets.

Test Case 7: vm2vm vhost-user/virtio1.1-pmd mergeable path test with payload check
==================================================================================

1. Launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch virtio-user1 by below command::

    ./testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>set burst 1
    testpmd>start tx_first 10

5. Check payload is correct in each dumped packets.
