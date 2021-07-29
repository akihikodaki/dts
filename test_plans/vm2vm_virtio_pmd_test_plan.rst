.. Copyright (c) <2021>, Intel Corporation
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

This test plan includes vm2vm mergeable, normal and vector_rx path test with virtio 0.95 and virtio 1.0,
also add mergeable and normal path test with virtio 1.1. Specially, three mergeable path cases check the
payload of each packets are valid by using pdump.

Test flow
=========
Virtio-pmd <-> Vhost-user <-> Testpmd <-> Vhost-user <-> Virtio-pmd

Test Case 1: VM2VM vhost-user/virtio-pmd with vector_rx path
============================================================

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
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

3. On VM1, bind vdev with igb_uio driver,then run testpmd, set rxonly for virtio1, [0000:xx.00] is [Bus,Device,Function] of virtio-net::

    ./testpmd -c 0x3 -n 4 -w 0000:xx.00,vectorized=1 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with igb_uio driver,then run testpmd, set txonly for virtio2 and send 64B packets, [0000:xx.00] is [Bus,Device,Function] of virtio-net::

    ./testpmd -c 0x3 -n 4 -w 0000:xx.00,vectorized=1 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>set txpkts 64
    testpmd>start tx_first 32

5. Check the performance at vhost testpmd to see the tx/rx rate with 64B packet size::

    testpmd>show port stats all
    ...
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 2: VM2VM vhost-user/virtio-pmd with normal path
=========================================================

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
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
    ...
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 3: VM2VM vhost-user/virtio1.0-pmd with vector_rx path
===============================================================

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
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

3. On VM1, bind vdev with igb_uio driver,then run testpmd, set rxonly for virtio1, [0000:xx.00] is [Bus,Device,Function] of virtio-net::

    ./testpmd -c 0x3 -n 4 -w 0000:xx.00,vectorized=1 -- -i --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. On VM2, bind vdev with igb_uio driver,then run testpmd, set txonly for virtio2, [0000:xx.00] is [Bus,Device,Function] of virtio-net::

    ./testpmd -c 0x3 -n 4 -w 0000:xx.00,vectorized=1 -- -i --txd=1024 --rxd=1024
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

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
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
    ...
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 5: VM2VM vhost-user/virtio-pmd mergeable path with payload valid check
================================================================================

1. Bind virtio with igb_uio driver, launch the testpmd by below commands::

    ./testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
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

    ./testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
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

Test Case 7: VM2VM vhost-user/virtio1.1-pmd mergeable path with payload valid check
===================================================================================

1. Bind virtio with igb_uio driver, launch the testpmd by below commands::

    ./testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
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

Test Case 8: VM2VM vhost-user/virtio1.1-pmd with normal path
============================================================

1. Bind one physical nic port to igb_uio, then launch the testpmd by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xc0000 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
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
    ...
    Throughput (since last show)
    RX-pps:            xxx
    TX-pps:            xxx

Test Case 9: VM2VM virtio-pmd split ring mergeable path 8 queues CBDMA enable with server mode stable test
==========================================================================================================

1. Bind 16 cbdma channels to igb_uio driver, then launch the testpmd with 2 vhost port and 8 queues by below commands::

    ./dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@00:04.0;txq1@00:04.1;txq2@00:04.2;txq3@00:04.3;txq4@00:04.4;txq5@00:04.5;txq6@00:04.6;txq7@00:04.7],dmathr=512' \
    --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7],dmathr=512'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
    testpmd>vhost enable tx all
    testpmd>start

2. Launch VM1 and VM2 using qemu5.2.0::

    taskset -c 6-16 /home/qemu-install/qemu-5.2/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

    taskset -c 17-27 /home/qemu-install/qemu-5.2/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

3. On VM1 and VM2, bind virtio device with vfio-pci driver::

    modprobe vfio
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

4. Launch testpmd in VM1::

    ./dpdk-testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set mac fwd
    testpmd>start

5. Launch testpmd in VM2, sent imix pkts from VM2::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set mac fwd
    testpmd>set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
    testpmd>start tx_first 1

6. Check imix packets can looped between two VMs for 1 mins and 8 queues all have packets rx/tx::

    testpmd>show port stats all
    testpmd>stop

7. Relaunch and start vhost side testpmd with below cmd, change cbdma threshold for one vhost port's cbdma channels::

    ./dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@00:04.0;txq1@00:04.1;txq2@00:04.2;txq3@00:04.3;txq4@00:04.4;txq5@00:04.5;txq6@00:04.6;txq7@00:04.7],dmathr=512' \
    --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7],dmathr=64'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
    testpmd>start

8. Send pkts by testpmd in VM2, check imix packets can looped between two VMs for 1 mins and 8 queues all have packets rx/tx::

    testpmd>stop
    testpmd>start tx_first 1
    testpmd>show port stats all
    testpmd>stop

9. Rerun step 7-8 for 10 times.

Test Case 10: VM2VM virtio-pmd split ring mergeable path dynamic queue size CBDMA enable with server mode test
==============================================================================================================

1. Bind 16 cbdma channels to igb_uio driver, then launch the testpmd with 2 vhost ports below commands::

    ./dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@00:04.0;txq1@00:04.1;txq2@00:04.2;txq3@00:04.3;txq4@00:04.4;txq5@00:04.5;txq6@00:04.6;txq7@00:04.7],dmathr=512' \
    --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7],dmathr=512'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4
    testpmd>vhost enable tx all
    testpmd>start

2. Launch VM1 and VM2 using qemu5.2.0::

    taskset -c 6-16 /home/qemu-install/qemu-5.2/bin/qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

    taskset -c 17-27 /home/qemu-install/qemu-5.2/bin/qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :12

3. On VM1 and VM2, bind virtio device with vfio-pci driver::

    modprobe vfio
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

4. Launch testpmd in VM1::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set mac fwd
    testpmd>start

5. Launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins and 4 queues (queue0 to queue3) have packets rx/tx::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set mac fwd
    testpmd>set txpkts 64,256,512,1024,2000,64,256,512,1024,2000
    testpmd>start tx_first 32
    testpmd>show port stats all
    testpmd>stop

6. Relaunch and start vhost side testpmd with eight queues, change cbdma threshold for one vhost port's cbdma channels::

    ./dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0@00:04.0;txq1@00:04.1;txq2@00:04.2;txq3@00:04.3;txq4@00:04.4;txq5@00:04.5;txq6@00:04.6;txq7@00:04.7],dmathr=512' \
    --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7],dmathr=64'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
    testpmd>start

7. Send pkts by testpmd in VM2, check imix packets can looped between two VMs for 1 mins and 8 queues all have packets rx/tx::

    testpmd>stop
    testpmd>start tx_first 32
    testpmd>show port stats all
    testpmd>stop

8. Rerun step 6-7 for 10 times.

Test Case 11: VM2VM virtio-pmd packed ring mergeable path 8 queues CBDMA enable test
=====================================================================================

1. Bind 16 cbdma channels to igb_uio driver, then launch the testpmd with 2 vhost port and 8 queues by below commands::

    rm -rf vhost-net*
    ./dpdk-testpmd -l 1-5 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[txq0@00:04.0;txq1@00:04.1;txq2@00:04.2;txq3@00:04.3;txq4@00:04.4;txq5@00:04.5;txq6@00:04.6;txq7@00:04.7],dmathr=512' \
    --vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7],dmathr=512'  -- -i --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8
    testpmd>vhost enable tx all
    testpmd>start

2. Launch VM1 and VM2 with qemu 5.2.0::

    taskset -c 6-16 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :10

    taskset -c 17-27 qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04-2.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on -vnc :12

3. On VM1 and VM2, bind virtio device with vfio-pci driver::

    modprobe vfio
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0

4. Launch testpmd in VM1::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set mac fwd
    testpmd>start

5. Launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins and 8 queues all have packets rx/tx::

    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set mac fwd
    testpmd>set txpkts 64,256,512,1024,20000,64,256,512,1024,20000
    testpmd>start tx_first 32
    testpmd>show port stats all
    testpmd>stop

6. Quit VM2 and relaunch VM2 with split ring::

    taskset -c 6-16 qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 9 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu20-04.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on -vnc :10

7. Bind virtio device with vfio-pci driver, launch testpmd in VM2 and send imix pkts, check imix packets can looped between two VMs for 1 mins and 8 queues all have packets rx/tx::

    modprobe vfio
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:00:05.0
    ./testpmd -c 0x3 -n 4 -- -i --tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024 --max-pkt-len=9600
    testpmd>set mac fwd
    testpmd>set txpkts 64,256,512,1024,20000,64,256,512,1024,20000
    testpmd>start tx_first 32
    testpmd>show port stats all
    testpmd>stop
