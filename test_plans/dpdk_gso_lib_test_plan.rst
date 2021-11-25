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

======================
DPDK GSO lib test plan
======================

Generic Segmentation Offload (GSO) is a widely used software implementation of
TCP Segmentation Offload (TSO), which reduces per-packet processing overhead.
Much like TSO, GSO gains performance by enabling upper layer applications to
process a smaller number of large packets (e.g. MTU size of 64KB), instead of
processing higher numbers of small packets (e.g. MTU size of 1500B), thus
reducing per-packet overhead.

For example, GSO allows guest kernel stacks to transmit over-sized TCP segments
that far exceed the kernel interface's MTU; this eliminates the need to segment
packets within the guest, and improves the data-to-overhead ratio of both the
guest-host link, and PCI bus. The expectation of the guest network stack in this
scenario is that segmentation of egress frames will take place either in the NIC
HW, or where that hardware capability is unavailable, either in the host
application, or network stack.

Bearing that in mind, the GSO library enables DPDK applications to segment
packets in software. Note however, that GSO is implemented as a standalone
library, and not via a 'fallback' mechanism (i.e. for when TSO is unsupported
in the underlying hardware); that is, applications must explicitly invoke the
GSO library to segment packets. The size of GSO segments ``(segsz)`` is
configurable by the application.

This test plan includes dpdk gso lib test with TCP/UDP/VxLAN/GRE traffic.

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

Test flow
=========

::

  NIC2(In kernel) <- NIC1(DPDK) <- testpmd(csum fwd) <- Vhost <- Virtio-net

Test Case1: DPDK GSO test with tcp traffic
==========================================

1. Connect two nic port directly, put nic2 into another namesapce and turn on the gro of this nic port by below cmds::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1                   # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig [enp216s0f0] 1.1.1.8 up
    ip netns exec ns1 ethtool -K [enp216s0f0] gro on

2. Bind nic1 to vfio-pci, launch vhost-user with testpmd::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x       # xx:xx.x is the pci addr of nic1
    ./testpmd -l 2-4 -n 4 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --txd=1024 --rxd=1024
    testpmd>set fwd csum
    testpmd>stop
    testpmd>port stop 0
    testpmd>csum set tcp hw 0
    testpmd>csum set ip hw 0
    testpmd>set port 0 gso on
    testpmd>set gso segsz 1460
    testpmd>port start 0
    testpmd>start

3.  Set up vm with virto device and using kernel virtio-net driver:

  ::

    taskset -c 13 \
    qemu-system-x86_64 -name us-vhost-vm1 \
       -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
       -numa node,memdev=mem \
       -mem-prealloc -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6001-:22 \
       -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
       -chardev socket,id=char0,path=./vhost-net \
       -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on,rx_queue_size=1024,tx_queue_size=1024 -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip::

    ifconfig [ens3] 1.1.1.2 up  # [ens3] is the name of virtio-net

5. Start iperf test, run iperf server at host side and iperf client at vm side, check throughput in log::

    Host side :  ip netns exec ns1 iperf -s
    VM side:     iperf -c 1.1.1.8 -i 1 -t 60

Test Case2: DPDK GSO test with udp traffic
==========================================

Similar as Test Case1, all steps are similar except step 5.

5. Start iperf test, run iperf server at host side and iperf client at vm side, check throughput in log::

    Host side :  ip netns exec ns1 iperf -s -u
    VM side:     iperf -c 1.1.1.8 -i 1 -t 60 -P 4 -u -b 10G -l 9000

Test Case3: DPDK GSO test with vxlan traffic
============================================

1. Connect two nic port directly, put nic2 into another namesapce and generate the vxlan device in this name space::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1       # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig [enp216s0f0] 188.0.0.1 up
    ip netns exec ns1 ip link add vxlan100 type vxlan id 1000 remote 188.0.0.2 local 188.0.0.1 dstport 4789 dev [enp216s0f0]
    ip netns exec ns1 ifconfig vxlan100 1.1.1.1/24 up

2. Bind nic1 to vfio-pci, launch vhost-user with testpmd::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x
    ./testpmd -l 2-4 -n 4 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --txd=1024 --rxd=1024
    testpmd>set fwd csum
    testpmd>stop
    testpmd>port stop 0
    testpmd>csum set tcp hw 0
    testpmd>csum set ip hw 0
    testpmd>csum set outer-ip hw 0
    testpmd>csum parse-tunnel on 0
    testpmd>set port 0 gso on
    testpmd>set gso segsz 1400
    testpmd>port start 0
    testpmd>start

3.  Set up vm with virto device and using kernel virtio-net driver:

  ::

    taskset -c 13 \
    qemu-system-x86_64 -name us-vhost-vm1 \
       -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
       -numa node,memdev=mem \
       -mem-prealloc -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6001-:22 \
       -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
       -chardev socket,id=char0,path=./vhost-net \
       -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on,rx_queue_size=1024,tx_queue_size=1024 -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip::

    ifconfig [ens3] 188.0.0.2 up  # [ens3] is the name of virtio-net
    ip link add vxlan100 type vxlan id 1000 remote 188.0.0.1 local 188.0.0.2 dstport 4789 dev [ens3]
    ifconfig vxlan100 1.1.1.2/24 up

5. Start iperf test, run iperf server at host side and iperf client at vm side, check throughput in log::

    Host side :  ip netns exec ns1 iperf -s
    VM side:     iperf -c 1.1.1.1 -i 1 -t 60

Test Case4: DPDK GSO test with gre traffic
==========================================

1. Connect two nic port directly, put nic2 into another namesapce and generate the gre device in this name space::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1       # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig [enp216s0f0] 188.0.0.1 up
    ip netns exec ns1 ip tunnel add gre100 mode gre remote 188.0.0.2 local 188.0.0.1
    ip netns exec ns1 ifconfig gre100 1.1.1.1/24 up

2. Bind nic1 to vfio-pci, launch vhost-user with testpmd::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x
    ./testpmd -l 2-4 -n 4 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --txd=1024 --rxd=1024
    testpmd>set fwd csum
    testpmd>stop
    testpmd>port stop 0
    testpmd>csum set tcp hw 0
    testpmd>csum set ip hw 0
    testpmd>csum set outer-ip hw 0
    testpmd>csum parse-tunnel on 0
    testpmd>set port 0 gso on
    testpmd>set gso segsz 1400
    testpmd>port start 0
    testpmd>start

3.  Set up vm with virto device and using kernel virtio-net driver:

  ::

    taskset -c 13 \
    qemu-system-x86_64 -name us-vhost-vm1 \
       -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
       -numa node,memdev=mem \
       -mem-prealloc -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6001-:22 \
       -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
       -chardev socket,id=char0,path=./vhost-net \
       -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on,rx_queue_size=1024,tx_queue_size=1024 -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip::

    ifconfig [ens3] 188.0.0.2 up  # [ens3] is the name of virtio-net
    ip tunnel add gre100 mode gre remote 188.0.0.1 local 188.0.0.2
    ifconfig gre100 1.1.1.2/24 up

5. Start iperf test, run iperf server at host side and iperf client at vm side, check throughput in log::

    Host side :  ip netns exec ns1 iperf -s
    VM side:     iperf -c 1.1.1.1 -i 1 -t 60