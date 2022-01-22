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

============================================
Virtio_user as an exceptional path test plan
============================================

This test plan will test exceptional path with virtio_user and measure throughput by iperf.

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

Test Case1:test exceptional path with virtio_user
=================================================
Flow:tap0-->vhost-net-->virtio_user-->nic0-->nic1
     tap0<--vhost-net<--virtio_user<--nic0<--nic1

1. Connect two nic port directly, put nic1 into another namesapce::

    ip netns del ns1
    ip netns add ns1
    ip link set [enp216s0f0] netns ns1       # [enp216s0f0] is the name of nic1
    ip netns exec ns1 ifconfig [enp216s0f0] 1.1.1.8 up

2. Modprobe vhost-net and make sure it's under /dev folder::

    modprobe vhost-net

3. Bind nic0 to vfio-pci and launch the virtio_user with testpmd::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x        # xx:xx.x is the pci addr of nic0
    ./<build_target>/app/dpdk-testpmd -c 0xc0000 -n 4 --file-prefix=test2 \
    --vdev=virtio_user0,mac=00:01:02:03:04:05,path=/dev/vhost-net,queue_size=1024 -- -i --rxd=1024 --txd=1024
    testpmd>set fwd csum
    testpmd>stop
    testpmd>port stop 0
    testpmd>port stop 1
    testpmd>port config 0 tx_offload tcp_cksum on
    testpmd>port config 0 tx_offload ipv4_cksum on
    testpmd>csum set tcp hw 0
    testpmd>csum set ip hw 0
    testpmd>csum set ip sw 1
    testpmd>csum set tcp hw 1
    testpmd>set port 0 gso on
    testpmd>tso set 1448 0
    testpmd>port start 0
    testpmd>port start 1
    testpmd>start

4. Check if there is a tap device generated and set the ip for tap0 device::

    ls /sys/class/net/tap0
    ifconfig tap0 1.1.1.2 up

5. Set sw ipv4_csum for virtio_user by setting testpmd cmd::

    testpmd>stop
    testpmd>port stop 1
    testpmd>csum set ip sw 1
    testpmd>port start 1
    testpmd>start

6. Run iperf server at host and iperf client at ns1 namespace, get the performance from nic in kernel to the tap0::

    iperf -s -i 1
    ip netns exec ns1 iperf -c 1.1.1.2 -i 1 -t 60

7. Change iperf server and client, run iperf server at ns1 namespace and iperf client at host, get the performance from tap0 to the nic in kernel::

    ip netns exec ns1 iperf -s -i 1
    iperf -c 1.1.1.8 -i 1 -t 60

Test Case2:test vhost-net/virtio_user single queue performance
==============================================================
Flow: tap0<-->vhost-net<-->virtio_user<-->nic0<-->TG

1. Disable ufw, otherwise virio-user can't received packets back from tap0::

    ufw disable

2. Bind the physical port to vfio-pci, launch testpmd with one queue for virtio_user::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x        # xx:xx.x is the pci addr of nic0
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4  --file-prefix=test2 --vdev=virtio_user0,mac=00:01:02:03:04:05,path=/dev/vhost-net,queue_size=1024,queues=1 -- -i --rxd=1024 --txd=1024

3. Check if there is a tap device generated::

    ls /sys/class/net/tap0
    ifconfig tap0 up

4. Set route table to let tap0 forward packets back to virtio-user port::

    ifconfig tap0 2.2.2.2/24 up
    route add -net 2.2.2.0/24 gw 2.2.2.1 dev tap0
    arp -s 2.2.2.1 68:01:02:03:04:05

5. Send 64 bytes traffic to the physical nic with dest mac= tap0's mac address, dest ip=2.2.2.x(except 2.2.2.2).

6. Bind vhost-net kthread with logical core: firstly check process by "ps -ef|grep vhost", check vhost-net kthread by "ps -T xxxx", then bind the pid to the core at the same socket as the nic port by taskset.

7. Try different line rate with ixia to find a point that rx_throughput=tx_throughput, for example if using ninatic 10G nic, the balance line rate is about 2.5.

Test Case3: test vhost-net/virtio_user multiple queue
=====================================================
Flow: tap0<-->vhost-net<-->virtio_user<-->nic0<-->TG

1.Disable ufw, otherwise virtio-user can't received packets back from tap0::

    ufw disable

2. Bind the physical port to vfio-pci, launch testpmd with two queues for virtio_user::

    ./dpdk-devbind.py -b vfio-pci xx:xx.x        # xx:xx.x is the pci addr of nic0
    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4  --file-prefix=test2 --vdev=virtio_user0,mac=00:01:02:03:04:05,path=/dev/vhost-net,queue_size=1024,queues=2 -- -i --rxd=1024 --txd=1024 --txq=2 --rxq=2 --nb-cores=1

3. Check if there is a tap device generated::

    ls /sys/class/net/tap0
    ifconfig tap0 up

4. Set route table to let tap0 forward packets back to virtio-user port::

    ifconfig tap0 2.2.2.2/24 up
    route add -net 2.2.2.0/24 gw 2.2.2.1 dev tap0
    arp -s 2.2.2.1 68:01:02:03:04:05

5. Send 64 bytes multi-ips traffic to the physical nic with dest mac= tap0's mac address, dest ip=2.2.2.x(except 2.2.2.2).

6. Bind vhost-net kthread with logical core: firstly check process by "ps -ef|grep vhost", check vhost-net kthread by "ps -T xxxx", for multiple queues, there are multiple vhost kthreads, then bind the pids to different logical cores at the same socket as the nic port by taskset.

7. Try different line rate with ixia to find a point that rx_throughput=tx_throughput, for example if using ninatic 10G nic, the balance line rate is about 5 (should be double of case 2).