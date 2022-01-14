.. Copyright (c) <2016>, Intel Corporation
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

==========================================
Vhost/Virtio multiple queue qemu test plan
==========================================

This test plan will cover the vhost/virtio-pmd multiple queue qemu test case.
Will use testpmd as the test application. 

Test Case: vhost pmd/virtio-pmd PVP 2queues mergeable path performance
======================================================================

flow: 
TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

1. Bind one port to vfio-pci, then launch testpmd by below command:
    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2' -- \
    -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start

2. Launch VM with vectors=2*queue_num+2 and mrg_rxbuf/mq feature on::

    qemu-system-x86_64 -name vm1 -cpu host -enable-kvm \
    -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem \
    -mem-prealloc -smp cores=3,sockets=1 -drive file=/home/osimg/ubuntu16.img \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=6 \
    -netdev tap,id=ipvm1,ifname=tap3,script=/etc/qemu-ifup -device rtl8139,netdev=ipvm1,id=net0,mac=00:00:00:00:10:01 \
    -vnc :2 -daemonize

3. On VM, bind virtio net to vfio-pci and run testpmd ::
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x07 -n 3 -- -i \
    --rxq=2 --txq=2 --txqflags=0xf01 --rss-ip --nb-cores=2
    testpmd>set fwd mac
    testpmd>start

4. Check the performance for the 2core/2queue for vhost/virtio. 

Test Case: PVP virtio-pmd queue number dynamic change
=====================================================

This case is to check if the virtio-pmd can work well when queue number 
dynamic change. In this case, set both vhost-pmd and virtio-pmd max queue 
number as 2 queues. Launch vhost-pmd with 2 queues. Launch virtio-pmd with 
1 queue first then in testpmd, change the number to 2 queues. Expect no crash 
happened. And after the queue number changes, the virtio-pmd can use 2 queues 
to RX/TX packets normally. 


flow: 
TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

1. Bind one port to vfio-pci, then launch testpmd by below command,
   ensure the vhost using 2 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2' -- \
    -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd mac
    testpmd>start
    testpmd>clear port stats all

2. Launch VM with vectors=2*queue_num+2 and mrg_rxbuf/mq feature on::

    qemu-system-x86_64 -name vm1 -cpu host -enable-kvm \
    -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem \
    -mem-prealloc -smp cores=3,sockets=1 -drive file=/home/osimg/ubuntu16.img \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=6 \
    -netdev tap,id=ipvm1,ifname=tap3,script=/etc/qemu-ifup -device rtl8139,netdev=ipvm1,id=net0,mac=00:00:00:00:10:01 \
    -vnc :2 -daemonize

3. On VM, bind virtio net to vfio-pci and run testpmd,
   using one queue for testing at first::
 
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 3 -- -i --rxq=1 --txq=1 --tx-offloads=0x0 \
    --rss-ip --nb-cores=1
    testpmd>set fwd mac
    testpmd>start

4. Use scapy send packet::

    #scapy
    >>>pk1= [Ether(dst="52:54:00:00:00:01")/IP(dst="1.1.1.1")/UDP()/("X"*64)]
    >>>pk2= [Ether(dst="52:54:00:00:00:01")/IP(dst="1.1.1.7")/UDP()/("X"*64)]
    >>>pk3= [Ether(dst="52:54:00:00:00:01")/IP(dst="1.1.1.8")/UDP()/("X"*64)]
    >>>pk4= [Ether(dst="52:54:00:00:00:01")/IP(dst="1.1.1.20")/UDP()/("X"*64)]
    >>>pk= pk1 + pk2 + pk3 + pk4
    >>>sendp(pk, iface="ens785f1",count=10)
    
    check each queue's RX/TX packet numbers.

5. On VM, dynamic change queue numbers at virtio-pmd side from 1 queue to 2 
   queues, then ensure virtio-pmd RX/TX can work normally.
   The expected behavior is that both queues can RX/TX traffic::
   
    testpmd>stop
    testpmd>port stop all
    testpmd>port config all rxq 2
    testpmd>port config all txq 2
    testpmd>port start all
    testpmd>start
    
    use scapy send packets like step 4.
    testpmd>stop

    then check each queue's RX/TX packet numbers. 

6. There should be no core dump or unexpected crash happened during the queue
   number changes. 


Test Case: PVP Vhost-pmd queue number dynamic change
====================================================

This case is to check if the vhost-pmd queue number dynamic change can work
well. In this case, set vhost-pmd and virtio-pmd max queue number as 2. 
Launch vhost-pmd with 1 queue first then in testpmd, change the queue number
to 2 queues. At virtio-pmd side, launch it with 2 queues. Expect no crash 
happened. After the dynamical changes, vhost-pmd can use 2 queues to RX/TX 
packets. 


flow: 
TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

1. Bind one port to vfio-pci, then launch testpmd by below command,
   ensure the vhost using 2 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2' -- \
    -i --nb-cores=1 --rxq=1 --txq=1
    testpmd>set fwd mac
    testpmd>start
    testpmd>clear port stats all

2. Launch VM with vectors=2*queue_num+2 and mrg_rxbuf/mq feature on::

    qemu-system-x86_64 -name vm1 -cpu host -enable-kvm \
    -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem \
    -mem-prealloc -smp cores=3,sockets=1 -drive file=/home/osimg/ubuntu16.img \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=6 \
    -netdev tap,id=ipvm1,ifname=tap3,script=/etc/qemu-ifup -device rtl8139,netdev=ipvm1,id=net0,mac=00:00:00:00:10:01 \
    -vnc :2 -daemonize

3. On VM, bind virtio net to vfio-pci and run testpmd,
   using one queue for testing at first::
 
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 4 -- -i --rxq=2 --txq=2 \
    --tx-offloads=0x0 --rss-ip --nb-cores=2
    testpmd>set fwd mac
    testpmd>start
 
4. Use scapy send packet::

    #scapy
    >>>pk1= [Ether(dst="52:54:00:00:00:01")/IP(dst="1.1.1.1")/UDP()/("X"*64)]
    >>>pk2= [Ether(dst="52:54:00:00:00:01")/IP(dst="1.1.1.7")/UDP()/("X"*64)]
    >>>pk3= [Ether(dst="52:54:00:00:00:01")/IP(dst="1.1.1.8")/UDP()/("X"*64)]
    >>>pk4= [Ether(dst="52:54:00:00:00:01")/IP(dst="1.1.1.20")/UDP()/("X"*64)]
    >>>pk= pk1 + pk2 + pk3 + pk4
    >>>sendp(pk, iface="ens785f1", count=10)
    
    check each queue's RX/TX packet numbers.

5. On host, dynamic change queue numbers at vhost-pmd side from 1 queue to 2 
   queues, then ensure vhost-pmd RX/TX can work normally.
   The expected behavior is that both queues can RX/TX traffic::
   
    testpmd>stop
    testpmd>port stop all
    testpmd>port config all rxq 2
    testpmd>port config all txq 2
    testpmd>port start all
    testpmd>start
    
    use scapy send packets like step 4.
    testpmd>stop

    then check each queue's RX/TX packet numbers. 

6. There should be no core dump or unexpected crash happened during the 
   queue number changes. 
