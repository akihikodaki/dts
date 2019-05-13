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

==================
DPDK GRO test plan
==================

This test plan will cover vdev GRO light/heavy mode test.
As we need use checksum fwd in this test and make sure ping and iperf packets can reach each side.

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

NIC2(In kernel) -> NIC1(DPDK) -> testpmd(csum fwd) -> Vhost -> Virtio-net

Test Case1: DPDK GRO lightmode test with tcp traffic
====================================================

1. Connect two nic port directly, put nic2 into another namesapce and turn on the tso of this nic port by below cmds::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1       # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig [enp216s0f0] 1.1.1.8 up
    ip netns exec ns1 ethtool -K [enp216s0f0] tso on

2. Bind nic1 to igb_uio, launch vhost-user with testpmd and set flush interval to 1::

    ./dpdk-devbind.py -b igb_uio xx:xx.x
    ./testpmd -l 2-4 -n 4 --socket-mem 1024,1024  --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --txd=1024 --rxd=1024
    testpmd>set fwd csum
    testpmd>stop
    testpmd>port stop 0
    testpmd>port stop 1
    testpmd>csum set tcp hw 0
    testpmd>csum set ip hw 0
    testpmd>csum set tcp hw 1
    testpmd>csum set ip hw 1
    testpmd>set port 0 gro on
    testpmd>set gro flush 1
    testpmd>port start 0
    testpmd>port start 1
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
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on \
       -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip and turn the kernel gro off::

    ifconfig [ens3] 1.1.1.2 up  # [ens3] is the name of virtio-net
    ethtool -K [ens3] gro off

5. Start iperf test, run iperf server at vm side and iperf client at host side, check throughput in log::

    Host side :  ip netns exec ns1 iperf -c 1.1.1.2 -i 1 -t 60 -m -P 1
    VM side:     iperf -s

Test Case2: DPDK GRO heavymode test with tcp traffic
====================================================

1. Connect two nic port directly, put nic2 into another namesapce and turn on the tso of this nic port by below cmds::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1       # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig [enp216s0f0] 1.1.1.8 up
    ip netns exec ns1 ethtool -K [enp216s0f0] tso on

2. Bind nic1 to igb_uio, launch vhost-user with testpmd and set flush interval to 2::

    ./dpdk-devbind.py -b igb_uio xx:xx.x
    ./testpmd -l 2-4 -n 4 --socket-mem 1024,1024  --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --txd=1024 --rxd=1024
    testpmd>set fwd csum
    testpmd>stop
    testpmd>port stop 0
    testpmd>port stop 1
    testpmd>csum set tcp hw 0
    testpmd>csum set ip hw 0
    testpmd>csum set tcp hw 1
    testpmd>csum set ip hw 1
    testpmd>set port 0 gro on
    testpmd>set gro flush 2
    testpmd>port start 0
    testpmd>port start 1
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
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on \
       -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip and turn the kernel gro off::

    ifconfig [ens3] 1.1.1.2 up  # [ens3] is the name of virtio-net
    ethtool -K [ens3] gro off

5. Start iperf test, run iperf server at vm side and iperf client at host side, check throughput in log::

    Host side :  ip netns exec ns1 iperf -c 1.1.1.2 -i 1 -t 60 -m -P 1
    VM side:     iperf -s

Test Case3: DPDK GRO heavymode_flush4 test with tcp traffic
===========================================================

1. Connect two nic port directly, put nic2 into another namesapce and turn on the tso of this nic port by below cmds::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1       # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig [enp216s0f0] 1.1.1.8 up
    ip netns exec ns1 ethtool -K [enp216s0f0] tso on

2. Bind nic1 to igb_uio, launch vhost-user with testpmd and set flush interval to 4::

    ./dpdk-devbind.py -b igb_uio xx:xx.x
    ./testpmd -l 2-4 -n 4 --socket-mem 1024,1024  --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --txd=1024 --rxd=1024
    testpmd>set fwd csum
    testpmd>stop
    testpmd>port stop 0
    testpmd>port stop 1
    testpmd>csum set tcp hw 0
    testpmd>csum set ip hw 0
    testpmd>csum set tcp hw 1
    testpmd>csum set ip hw 1
    testpmd>set port 0 gro on
    testpmd>set gro flush 4
    testpmd>port start 0
    testpmd>port start 1
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
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on \
       -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip and turn the kernel gro off::

    ifconfig [ens3] 1.1.1.2 up  # [ens3] is the name of virtio-net
    ethtool -K [ens3] gro off

5. Start iperf test, run iperf server at vm side and iperf client at host side, check throughput in log::

    Host side :  ip netns exec ns1 iperf -c 1.1.1.2 -i 1 -t 60 -m -P 1
    VM side:     iperf -s

Test Case4: DPDK GRO test with vxlan traffic
============================================

Vxlan topology
--------------
  VM          Host
50.1.1.2      50.1.1.1
   |           |
1.1.2.3       1.1.2.4
   |------------Testpmd------------|

1. Connect two nic port directly, put nic2 into another namesapce and create Host VxLAN port::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1    # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig [enp216s0f0] 1.1.2.4/24 up
    VXLAN_NAME=vxlan1
    VXLAN_IP=50.1.1.1
    IF_NAME=[enp216s0f0]
    VM_IP=1.1.2.3
    ip netns exec t2 ip link add $VXLAN_NAME type vxlan id 42 dev $IF_NAME dstport 4789
    ip netns exec t2 bridge fdb append to 00:00:00:00:00:00 dst $VM_IP dev $VXLAN_NAME
    ip netns exec t2 ip addr add $VXLAN_IP/24 dev $VXLAN_NAME
    ip netns exec t2 ip link set up dev $VXLAN_NAME

2. Bind nic1 to igb_uio, launch vhost-user with testpmd and set flush interval to 4::

    ./dpdk-devbind.py -b igb_uio xx:xx.x
    ./testpmd -l 2-4 -n 4 --socket-mem 1024,1024  --legacy-mem \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i --txd=1024 --rxd=1024
    testpmd>set fwd csum
    testpmd>stop
    testpmd>port stop 0
    testpmd>port stop 1
    testpmd>csum set tcp hw 0
    testpmd>csum set ip hw 0
    testpmd>csum parse-tunnel on 0
    testpmd>csum parse-tunnel on 1
    testpmd>csum set outer-ip hw 0
    testpmd>csum set tcp hw 1
    testpmd>csum set ip hw 1
    testpmd>set port 0 gro on
    testpmd>set gro flush 4
    testpmd>port start 0
    testpmd>port start 1
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
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on \
       -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip and turn the kernel gro off::

    ip link add vxlan0 type vxlan id 42 dev [ens3] dstport 4789   # [ens3] is the name of virtio-net
    bridge fdb add to 00:00:00:00:00:00 dst 1.1.2.4 dev vxlan0
    ip addr add 50.1.1.2/24 dev vxlan0
    ip link set up dev vxlan0
    ifconfig [ens3] 1.1.2.3/24 up
    ifconfig -a

5. Start iperf test, run iperf server at vm side and iperf client at host side, check throughput in log::

    Host side :  ip netns exec t2 iperf -c 50.1.1.2 -i 2 -t 60 -f g -m
    VM side:     iperf -s -f g
