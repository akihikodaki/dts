.. Copyright (c) <2020>, Intel Corporation
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
DPDK GRO lib test plan
======================

Description
===========

Generic Receive Offload (GRO) is a widely used SW-based offloading
technique to reduce per-packet processing overheads. By reassembling
small packets into larger ones, GRO enables applications to process
fewer large packets directly, thus reducing the number of packets to
be processed. To benefit DPDK-based applications, like Open vSwitch,
DPDK also provides own GRO implementation. In DPDK, GRO is implemented
as a standalone library. Applications explicitly use the GRO library to
reassemble packets.

In the GRO library, there are many GRO types which are defined by packet
types. One GRO type is in charge of process one kind of packets. For
example, TCP/IPv4 GRO processes TCP/IPv4 packets.

Each GRO type has a reassembly function, which defines own algorithm and
table structure to reassemble packets. We assign input packets to the
corresponding GRO functions by MBUF->packet_type.

The GRO library doesn't check if input packets have correct checksums and
doesn't re-calculate checksums for merged packets. The GRO library
assumes the packets are complete (i.e., MF==0 && frag_off==0), when IP
fragmentation is possible (i.e., DF==0). Additionally, it complies RFC
6864 to process the IPv4 ID field.

Currently, the GRO library provides GRO supports for TCP/IPv4 packets and
VxLAN packets which contain an outer IPv4 header and an inner TCP/IPv4
packet.

This test plan includes dpdk gro lib test with TCP/IPv4 traffic and VxLAN traffic,
also cover lightmode and heavymode test.

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

Modify the dpdk code as following::

   diff --git a/drivers/net/vhost/rte_eth_vhost.c b/drivers/net/vhost/rte_eth_vhost.c
   index b38a4b6b1..573250dbe 100644
   --- a/drivers/net/vhost/rte_eth_vhost.c
   +++ b/drivers/net/vhost/rte_eth_vhost.c
   @@ -1071,8 +1071,14 @@ eth_dev_info(struct rte_eth_dev *dev,
     dev_info->min_rx_bufsize = 0;

     dev_info->tx_offload_capa = DEV_TX_OFFLOAD_MULTI_SEGS |
   -       DEV_TX_OFFLOAD_VLAN_INSERT;
   - dev_info->rx_offload_capa = DEV_RX_OFFLOAD_VLAN_STRIP;
   +       DEV_TX_OFFLOAD_VLAN_INSERT |
   +       DEV_TX_OFFLOAD_UDP_CKSUM |
   +       DEV_TX_OFFLOAD_TCP_CKSUM |
   +       DEV_TX_OFFLOAD_IPV4_CKSUM |
   +       DEV_TX_OFFLOAD_TCP_TSO;
   + dev_info->rx_offload_capa = DEV_RX_OFFLOAD_VLAN_STRIP |
   +       DEV_RX_OFFLOAD_TCP_CKSUM |
   +       DEV_RX_OFFLOAD_UDP_CKSUM |
   +       DEV_RX_OFFLOAD_IPV4_CKSUM |
   +       DEV_RX_OFFLOAD_TCP_LRO;
    }

Test flow
=========

NIC2(In kernel) -> NIC1(DPDK) -> testpmd(csum fwd) -> Vhost -> Virtio-net

Test Case1: DPDK GRO lightmode test with tcp/ipv4 traffic
=========================================================

1. Connect two nic port directly, put nic2 into another namesapce and turn on the tso of this nic port by below cmds::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1       # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig [enp216s0f0] 1.1.1.8 up
    ip netns exec ns1 ethtool -K [enp216s0f0] tso on

2. Bind nic1 to vfio-pci, launch vhost-user with testpmd and set flush interval to 1::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x
    ./testpmd -l 2-4 -n 4 \
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

     taskset -c 13 qemu-system-x86_64 -name us-vhost-vm1 \
       -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
       -numa node,memdev=mem \
       -mem-prealloc -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6001-:22 \
       -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu2004.img  \
       -chardev socket,id=char0,path=./vhost-net \
       -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on \
       -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip and turn the kernel gro off::

    ifconfig [ens3] 1.1.1.2 up  # [ens3] is the name of virtio-net
    ethtool -K [ens3] gro off

5. Start iperf test, run iperf server at vm side and iperf client at host side, check throughput in log can get expected data::

    Host side :  ip netns exec ns1 iperf -c 1.1.1.2 -i 1 -t 60 -m -P 1
    VM side:     iperf -s

Test Case2: DPDK GRO heavymode test with tcp/ipv4 traffic
=========================================================

1. Connect two nic port directly, put nic2 into another namesapce and turn on the tso of this nic port by below cmds::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1       # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig [enp216s0f0] 1.1.1.8 up
    ip netns exec ns1 ethtool -K [enp216s0f0] tso on

2. Bind nic1 to vfio-pci, launch vhost-user with testpmd and set flush interval to 2::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x
    ./testpmd -l 2-4 -n 4 \
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

     taskset -c 13 qemu-system-x86_64 -name us-vhost-vm1 \
       -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
       -numa node,memdev=mem \
       -mem-prealloc -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6001-:22 \
       -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu2004.img  \
       -chardev socket,id=char0,path=./vhost-net \
       -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on \
       -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip and turn the kernel gro off::

    ifconfig [ens3] 1.1.1.2 up  # [ens3] is the name of virtio-net
    ethtool -K [ens3] gro off

5. Start iperf test, run iperf server at vm side and iperf client at host side, check throughput in log can get expected data::

    Host side :  ip netns exec ns1 iperf -c 1.1.1.2 -i 1 -t 60 -m -P 1
    VM side:     iperf -s

Test Case3: DPDK GRO heavymode_flush4 test with tcp/ipv4 traffic
================================================================

1. Connect two nic port directly, put nic2 into another namesapce and turn on the tso of this nic port by below cmds::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1       # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig [enp216s0f0] 1.1.1.8 up
    ip netns exec ns1 ethtool -K [enp216s0f0] tso on

2. Bind nic1 to vfio-pci, launch vhost-user with testpmd and set flush interval to 4::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x
    ./testpmd -l 2-4 -n 4 \
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

     taskset -c 13 qemu-system-x86_64 -name us-vhost-vm1 \
       -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
       -numa node,memdev=mem \
       -mem-prealloc -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6001-:22 \
       -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu2004.img  \
       -chardev socket,id=char0,path=./vhost-net \
       -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on \
       -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip and turn the kernel gro off::

    ifconfig [ens3] 1.1.1.2 up  # [ens3] is the name of virtio-net
    ethtool -K [ens3] gro off

5. Start iperf test, run iperf server at vm side and iperf client at host side, check throughput in log can get expected data::

    Host side :  ip netns exec ns1 iperf -c 1.1.1.2 -i 1 -t 60 -m -P 1
    VM side:     iperf -s

Test Case4: DPDK GRO test with vxlan traffic
============================================

Vxlan topology
--------------
  VM          Host

50.1.1.2      50.1.1.1
   \|           \|
1.1.2.3       1.1.2.4
   \|------------Testpmd------------|

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

2. Bind nic1 to vfio-pci, launch vhost-user with testpmd and set flush interval to 4::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x
    ./testpmd -l 2-4 -n 4 \
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

     taskset -c 13 qemu-system-x86_64 -name us-vhost-vm1 \
       -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
       -numa node,memdev=mem \
       -mem-prealloc -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6001-:22 \
       -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu2004.img  \
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

5. Start iperf test, run iperf server at vm side and iperf client at host side, check throughput in log can get expected data::

    Host side :  ip netns exec t2 iperf -c 50.1.1.2 -i 2 -t 60 -f g -m
    VM side:     iperf -s -f g

Test Case5: DPDK GRO test with 2 queues using tcp/ipv4 traffic
==============================================================

Test flow
=========

NIC2(In kernel) -> NIC1(DPDK) -> testpmd(csum fwd) -> Vhost -> Virtio-net

1. Connect two nic port directly, put nic2 into another namesapce and turn on the tso of this nic port by below cmds::

    ip netns del ns1
    ip netns add ns1
    ip link set enp26s0f0 netns ns1       # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig enp26s0f0 1.1.1.8 up
    ip netns exec ns1 ethtool -K enp26s0f0 tso on

2. Bind cbdma port and nic1 to vfio-pci, launch vhost-user with testpmd and set flush interval to 1::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 29-31 -n 4 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --txd=1024 --rxd=1024 --txq=2 --rxq=2 --nb-cores=2
    set fwd csum
    stop
    port stop 0
    port stop 1
    csum set tcp hw 0
    csum set ip hw 0
    csum set tcp hw 1
    csum set ip hw 1
    set port 0 gro on
    set gro flush 1
    port start 0
    port start 1
    start

3.  Set up vm with virto device and using kernel virtio-net driver::

     taskset -c 31 /home/qemu-install/qemu-4.2.1/bin/qemu-system-x86_64 -name us-vhost-vm1 \
       -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
       -numa node,memdev=mem \
       -mem-prealloc -monitor unix:/tmp/vm2_monitor.sock,server,nowait -netdev user,id=yinan,hostfwd=tcp:127.0.0.1:6005-:22 -device e1000,netdev=yinan \
       -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu2004.img  \
       -chardev socket,id=char0,path=./vhost-net \
       -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on,mq=on,vectors=15 \
       -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip and turn the kernel gro off::

    ifconfig ens4 1.1.1.2 up  # [ens3] is the name of virtio-net
    ethtool -L ens4 combined 2
    ethtool -K ens4 gro off

5. Start iperf test, run iperf server at vm side and iperf client at host side, check throughput in log can get better performance than case1::

    Host side :  taskset -c 35 ip netns exec ns1 iperf -c 1.1.1.2 -i 1 -t 60 -m -P 2
    VM side:     iperf -s

Test Case6: DPDK GRO test with two queues and two CBDMA channels using tcp/ipv4 traffic
=======================================================================================

Test flow
=========

NIC2(In kernel) -> NIC1(DPDK) -> testpmd(csum fwd) -> Vhost -> Virtio-net

1. Connect two nic port directly, put nic2 into another namesapce and turn on the tso of this nic port by below cmds::

    ip netns del ns1
    ip netns add ns1
    ip link set enp26s0f0 netns ns1       # [enp216s0f0] is the name of nic2
    ip netns exec ns1 ifconfig enp26s0f0 1.1.1.8 up
    ip netns exec ns1 ethtool -K enp26s0f0 tso on

2. Bind cbdma port and nic1 to vfio-pci, launch vhost-user with testpmd and set flush interval to 1::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 29-31 -n 4 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2,dmas=[txq0@80:04.0;txq1@80:04.1]' -- -i --txd=1024 --rxd=1024 --txq=2 --rxq=2 --nb-cores=2
    set fwd csum
    stop
    port stop 0
    port stop 1
    csum set tcp hw 0
    csum set ip hw 0
    csum set tcp hw 1
    csum set ip hw 1
    set port 0 gro on
    set gro flush 1
    port start 0
    port start 1
    start

3.  Set up vm with virto device and using kernel virtio-net driver::

     taskset -c 31 /home/qemu-install/qemu-4.2.1/bin/qemu-system-x86_64 -name us-vhost-vm1 \
       -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
       -numa node,memdev=mem \
       -mem-prealloc -monitor unix:/tmp/vm2_monitor.sock,server,nowait -netdev user,id=yinan,hostfwd=tcp:127.0.0.1:6005-:22 -device e1000,netdev=yinan \
       -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu2004.img  \
       -chardev socket,id=char0,path=./vhost-net \
       -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
       -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on,mq=on,vectors=15 \
       -vnc :10 -daemonize

4. In vm, config the virtio-net device with ip and turn the kernel gro off::

    ifconfig ens4 1.1.1.2 up  # [ens3] is the name of virtio-net
    ethtool -L ens4 combined 2
    ethtool -K ens4 gro off

5. Start iperf test, run iperf server at vm side and iperf client at host side, check throughput, should be larger than 10Gbits/sec::

    Host side :  taskset -c 35 ip netns exec ns1 iperf -c 1.1.1.2 -i 1 -t 60 -m -P 2
    VM side:     iperf -s
