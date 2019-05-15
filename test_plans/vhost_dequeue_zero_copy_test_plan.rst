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

=================================
vhost dequeue zero-copy test plan
=================================

Description
===========

Vhost dequeue zero-copy is a performance optimization for vhost, the copy in the dequeue path is avoided in order to improve the performance.
There are three topology test (PVP/VM2VM/VM2NIC) for this feature, the automation of different topology cases are in three different test suite.
1. In the PVP case, when packet size is 1518B, 10G nic could be the performance bottleneck, so we use 40G traffic genarator and 40G nic.
Also as vhost zero copy mbufs should be consumed as soon as possible, don't start send packets at vhost side before VM and virtio-pmd launched.
2. In the VM2VM case, the boost is quite impressive. The bigger the packet size, the bigger performance boost you may get.
3. In the VM2NIC case, there are some limitations, so the boost is not as impressive as the VM2VM case. It may even drop quite a bit for small packets.For that reason, this feature is disabled by default, it can be enabled when the RTE_VHOST_USER_DEQUEUE_ZERO_COPY flag is set.

Test Case 1: pvp dequeue zero-copy test with different packet sizes
===================================================================
Test topology: TG --> NIC --> Vhost --> Virtio --> Vhost --> NIC --> TG

1. Bind one 40G port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1,dequeue-zero-copy=1' -- \
    -i --nb-cores=1 --txd=1024 --rxd=1024 --txfreet=992
    testpmd>set fwd mac

2. Launch VM with mrg_rxbuf feature on, note that qemu_version need > qemu_2.10 for support adjusting parameter rx_queue_size::

    qemu-system-x86_64 -name vm1 \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=5,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
     -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char0,path=./vhost-net \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
     -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd::

    ./dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./testpmd -c 0x3 -n 4 -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Start testpmd at host side after VM and virtio-pmd launched::

    testpmd>start

5. Send packets by packet generator with different packet sizes (64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

6. Repeat the test with dequeue-zero-copy=0, compare the performance gains or degradation. For small packet, we may expect ~20% performance drop, but for big packet, we expect ~20% performance gains.

Test Case 2: pvp dequeue zero-copy test with 2 queues
=====================================================
Test topology: TG --> NIC --> Vhost --> Virtio --> Vhost --> NIC --> TG

1. Bind one 40G port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -l 2-4 -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,dequeue-zero-copy=1' -- \
    -i --nb-cores=2 --rxq=2 --txq=2 --txd=1024 --rxd=1024 --txfreet=992
    testpmd>set fwd mac

2. Launch VM with vectors=2*queue_num+2 and mrg_rxbuf/mq feature on, note that qemu_version need > qemu_2.10 for support adjusting parameter rx_queue_size::

    qemu-system-x86_64 -name vm1 \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=5,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
     -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char0,path=./vhost-net \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=8,rx_queue_size=1024,tx_queue_size=1024 \
     -vnc :10

3. On VM, bind vdev to igb_uio and run testpmd::

    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./testpmd -c 0x07 -n 4 -- -i \
    --rxq=2 --txq=2 --txd=1024 --rxd=1024 --nb-cores=2
    testpmd>set fwd mac
    testpmd>start

4. Start testpmd at host side after VM and virtio-pmd launched::

    testpmd>start

5. Send packets by packet generator with different packet sizes (64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

6. Check each queue's rx/tx packet numbers at vhost side::

    testpmd>stop

Test Case 3: pvp dequeue zero-copy test with driver unload test
===============================================================
Test topology: TG --> NIC --> Vhost --> Virtio --> Vhost --> NIC --> TG

1. Bind one 40G port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -l 1-5 -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=16,dequeue-zero-copy=1,client=1' -- \
    -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024 --txfreet=992
    testpmd>set fwd mac

2. Launch VM with vectors=2*queue_num+2 and mrg_rxbuf/mq feature on, note that qemu_version need > qemu_2.10 for support adjusting parameter rx_queue_size::

    qemu-system-x86_64 -name vm1 \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=5,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
     -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char0,path=./vhost-net,server \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=40,rx_queue_size=1024,tx_queue_size=1024 \
     -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd::

    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./testpmd -l 0-4 -n 4 --socket-mem 1024,0 -- -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024
    testpmd>set fwd rxonly
    testpmd>start

4. Start testpmd at host side after VM launched::

    testpmd>start

5. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

6. Relaunch testpmd at virtio side in VM for driver reloading::

    testpmd>quit
    ./testpmd -l 0-4 -n 4 --socket-mem 1024,0 -- -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

7. Send packets by packet generator with different packet sizes (64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

8. Check each queue's rx/tx packet numbers at vhost side::

    testpmd>stop

Test Case 4: pvp dequeue zero-copy test with maximum txfreet
============================================================
Test topology: TG --> NIC --> Vhost --> Virtio --> Vhost --> NIC --> TG

1. Bind one 40G port to igb_uio, then launch testpmd by below command::

    rm -rf vhost-net*
    ./testpmd -l 1-5 -n 4 --socket-mem 1024,1024 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=16,dequeue-zero-copy=1,client=1' -- \
    -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024 --txfreet=1020 --txrs=4
    testpmd>set fwd mac

2. Launch VM with vectors=2*queue_num+2 and mrg_rxbuf/mq feature on, note that qemu_version need > qemu_2.10 for support adjusting parameter rx_queue_size::

    qemu-system-x86_64 -name vm1 \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=5,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f \
     -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char0,path=./vhost-net,server \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=40,rx_queue_size=1024,tx_queue_size=1024 \
     -vnc :10

3. On VM, bind virtio net to igb_uio and run testpmd::

    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./testpmd -l 0-4 -n 4 --socket-mem 1024,0 -- -i --nb-cores=4 --rxq=16 --txq=16 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Start testpmd at host side after VM launched::

    testpmd>start

5. Send packets by packet generator with different packet sizes(64,128,256,512,1024,1518), show throughput with below command::

    testpmd>show port stats all

6. Check each queue's rx/tx packet numbers at vhost side::

    testpmd>stop

Test Case 5: vhost-user + virtio-net VM2VM dequeue zero-copy test
=================================================================
Test topology: Virtio-net <-> Vhost <-> Testpmd <-> Vhost <-> Virtio-net

1. Launch the Vhost sample by below commands::

    rm -rf vhost-net*
    testpmd>./testpmd -c 0xF0000000 -n 4 --socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net0,queues=1,dequeue-zero-copy=1' --vdev 'net_vhost1,iface=vhost-net1,queues=1,dequeue-zero-copy=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txfreet=992
    testpmd>start

2. Launch VM1 and VM2::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-1.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net0 -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :10 -daemonize

    taskset -c 34-35 \
    qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16-2.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6005-:22 \
     -chardev socket,id=char1,path=./vhost-net1 -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet2,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on  \
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

6. Check both 2VM can receive and send big packets to each other::

    testpmd>show port xstats all
    Port 0 should have tx packets above 1522
    Port 1 should have rx packets above 1522

Prerequisites
=============

Modify the testpmd code as following::

    --- a/app/test-pmd/csumonly.c
    +++ b/app/test-pmd/csumonly.c
    @@ -693,10 +693,12 @@ pkt_burst_checksum_forward(struct fwd_stream *fs)
                     * and inner headers */
     
                    eth_hdr = rte_pktmbuf_mtod(m, struct ether_hdr *);
    +#if 0
                    ether_addr_copy(&peer_eth_addrs[fs->peer_addr],
                                    &eth_hdr->d_addr);
                    ether_addr_copy(&ports[fs->tx_port].eth_addr,
                                    &eth_hdr->s_addr);
    +#endif
                    parse_ethernet(eth_hdr, &info);
                    l3_hdr = (char *)eth_hdr + info.l2_len;

Test Case 6: VM2Nic dequeue zero copy test with tso offload enabled
===================================================================
Test topology: NIC2(In kernel) <- NIC1(DPDK) <- testpmd(csum fwd) <- Vhost <- Virtio-net

1. Connect two nic port directly, put nic2 into another namesapce and turn on the gro of this nic port by below cmds::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1                   # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig [enp216s0f0] 1.1.1.8 up
    ip netns exec ns1 ethtool -K [enp216s0f0] gro on

2. Bind nic1 to igb_uio, launch vhost-user with testpmd::

    ./dpdk-devbind.py -b igb_uio xx:xx.x       # xx:xx.x is the pci addr of nic1
    ./testpmd -l 2-4 -n 4 --socket-mem 1024,1024  --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --txd=1024 --rxd=1024
    testpmd>set fwd csum
    testpmd>port stop 0
    testpmd>csum set tcp hw 0
    testpmd>csum set ip hw 0
    testpmd>set port 0 gso off
    testpmd>tso set 1460 0
    testpmd>port start 0
    testpmd>start

3.  Set up vm with virto device and using kernel virtio-net driver::

    taskset -c 13 \
    qemu-system-x86_64 -name us-vhost-vm1 \
       -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
       -numa node,memdev=mem \
       -mem-prealloc -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6001-:22 \
       -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
       -chardev socket,id=char0,path=./vhost-net \
       -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on,rx_queue_size=1024,tx_queue_size=1024 -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip::

    ifconfig [ens3] 1.1.1.2 up  # [ens3] is the name of virtio-net

5. Start iperf test, run iperf server at host side and iperf client at vm side, check throughput in log::

    Host side :  ip netns exec ns1 iperf -s
    VM side:     iperf -c 1.1.1.8 -i 1 -t 60

6. Start netperf test, run netperf server at host side and netperf client at vm side, check throughput in log::

    Host side :  ip netns exec ns1 netserver
    VM side:  netperf -t TCP_STREAM -H 1.1.1.8 -- -m        # bydefault configuration
              netperf -t TCP_STREAM -H 1.1.1.8 -- -m 1440   # packet size < mtu
              netperf -t TCP_STREAM -H 1.1.1.8 -- -m 2100   # chain mode