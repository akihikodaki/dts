.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=================================
DPDK GRO lib with cbdma test plan
=================================

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

This test plan includes dpdk gro lib test with TCP/IPv4 traffic when vhost uses the asynchronous operations with CBDMA channels.

..Note:
1.For packed virtqueue virtio-net test, need qemu version > 4.2.0 and VM kernel version > 5.1, and packed ring multi-queues not support reconnect in qemu yet.
2.For split virtqueue virtio-net with multi-queues server mode test, better to use qemu version >= 5.2.0, dut to qemu(v4.2.0~v5.1.0) exist split ring multi-queues reconnection issue.
3.DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

Prerequisites
=============
Topology
--------
	Test flow:NIC2(In kernel) -> NIC1(DPDK) -> testpmd(csum fwd) -> Vhost -> Virtio-net

General set up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110
    For example:
    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

Test case
=========

Test Case1: DPDK GRO test with two queues and cbdma channels using tcp/ipv4 traffic
-----------------------------------------------------------------------------------
This case tests dpdk gro lib with TCP/IPv4 traffic when vhost uses the asynchronous operations with CBDMA channels.

1. Connect 2 NIC port directly, put NIC2 into another namesapce and turn on the tso of this NIC port by below commands::

    ip netns del ns1
    ip netns add ns1
    ip link set enp26s0f0 netns ns1       # [enp216s0f0] is the name of NIC2
    ip netns exec ns1 ifconfig enp26s0f0 1.1.1.8 up
    ip netns exec ns1 ethtool -K enp26s0f0 tso on

2. Bind 2 CBDMA channels and NIC1 to vfio-pci, launch vhost-user with testpmd and set flush interval to 1::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29-31 -n 4 --file-prefix=vhost \
    --vdev 'net_vhost0,iface=vhost-net,queues=2,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.0;rxq0@0000:00:04.1;rxq1@0000:00:04.1]' \
    -- -i --txd=1024 --rxd=1024 --txq=2 --rxq=2 --nb-cores=2
    testpmd>set fwd csum
    testpmd>csum mac-swap off 0
    testpmd>csum mac-swap off 1
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

	taskset -c 31 qemu-system-x86_64 -name vm0 -enable-kvm -cpu host -smp 1 -m 4096 \
	-object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
	-numa node,memdev=mem -mem-prealloc -drive file=/home/image/ubuntu2004.img \
	-chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
	-device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -pidfile /tmp/.vm0.pid -daemonize \
	-monitor unix:/tmp/vm0_monitor.sock,server,nowait \
	-netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1 \
	-chardev socket,id=char0,path=./vhost-net \
	-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=2 \
	-device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on,mq=on,vectors=15 -vnc :4

4. In vm, config the virtio-net device with ip and turn the kernel gro off::

    ifconfig ens4 1.1.1.2 up  # [ens3] is the name of virtio-net
    ethtool -L ens4 combined 2
    ethtool -K ens4 gro off

5. Start iperf test, run iperf server at vm side and iperf client at host side, check throughput, should be larger than 10Gbits/sec::

    Host side :  taskset -c 35 ip netns exec ns1 iperf -c 1.1.1.2 -i 1 -t 60 -m -P 2
    VM side:     iperf -s

6. During the iperf send and receive packets, check that async data-path(virtio_dev_rx_async_xxx, virtio_dev_tx_async_xxx) is using at the host side::

    perf top
