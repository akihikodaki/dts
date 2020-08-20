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

==============================================
Virtio-pmd primary/secondary process test plan
==============================================

This test plan will test vdev primary/secondary with symmetric_mp, which demonstrates how a set of processes can run in parallel,
with each process performing the same set of packet processing operations. Also test vdev primary/secondary with hotplug_mp example.

Symmetric MP Application Description
------------------------------------

This test is a multi-process test which demonstrates how multiple processes can
work together to perform packet I/O and packet processing in parallel, much as
other example application work by using multiple threads. In this example, each
process reads packets from all network ports being used - though from a different
RX queue in each case. Those packets are then forwarded by each process which
sends them out by writing them directly to a suitable TX queue.

Prerequisites
-------------

Assuming that DPDK build has been set up and the multi-process sample
applications have been built. It is also assumed that a traffic generator has
been configured and plugged in to the NIC ports 0 and 1.
Also need modify l3fwd-power example code and recompile::

        --- a/examples/l3fwd-power/main.c
        +++ b/examples/l3fwd-power/main.c
        @@ -245,10 +245,9 @@ uint16_t nb_lcore_params = RTE_DIM(lcore_params_array_default);

         static struct rte_eth_conf port_conf = {
                .rxmode = {
        -               .mq_mode        = ETH_MQ_RX_RSS,
        +               .mq_mode        = ETH_MQ_RX_NONE,
                        .max_rx_pkt_len = RTE_ETHER_MAX_LEN,
                        .split_hdr_size = 0,
        -               .offloads = DEV_RX_OFFLOAD_CHECKSUM,
                },
                .rx_adv_conf = {
                        .rss_conf = {

Test Methodology
----------------

As with the simple_mp example, the first instance of the symmetric_mp process
must be run as the primary instance, though with a number of other application
specific parameters also provided after the EAL arguments. These additional
parameters are:

* -p <portmask>, where portmask is a hexadecimal bitmask of what ports on the
  system are to be used. For example: -p 3 to use ports 0 and 1 only.
* --num-procs <N>, where N is the total number of symmetric_mp instances that
  will be run side-by-side to perform packet processing. This parameter is used to
  configure the appropriate number of receive queues on each network port.
* --proc-id <n>, where n is a numeric value in the range 0 <= n < N (number of
  processes, specified above). This identifies which symmetric_mp instance is being
  run, so that each process can read a unique receive queue on each network port.

The secondary symmetric_mp instances must also have these parameters specified,
and the first two must be the same as those passed to the primary instance, or errors
result.

For example, to run a set of four symmetric_mp instances, running on lcores 1-4, all
performing level-2 forwarding of packets between ports 0 and 1, the following
commands can be used (assuming run as root)::

   ./build/symmetric_mp -c 2 --proc-type=auto -- -p 3 --num-procs=4 --proc-id=0
   ./build/symmetric_mp -c 4 --proc-type=auto -- -p 3 --num-procs=4 --proc-id=1
   ./build/symmetric_mp -c 8 --proc-type=auto -- -p 3 --num-procs=4 --proc-id=2
   ./build/symmetric_mp -c 10 --proc-type=auto -- -p 3 --num-procs=4 --proc-id=3

To run only 1 or 2 instances, the above parameters to the 1 or 2 instances being
run should remain the same, except for the ``num-procs`` value, which should be
adjusted appropriately.

Hotplug MP Application Description
----------------------------------

Currently secondary process will only sync ethdev from primary process at
init stage, but it will not be aware if device is attached/detached on
primary process at runtime.

While there is the requirement from application that take
primary-secondary process model. The primary process work as a resource
management process, it will create/destroy virtual device at runtime,
while the secondary process deal with the network stuff with these devices.

So the orignial intention is to fix this gap, but beyond that the patch
set provide a more comprehesive solution to handle different hotplug
cases in multi-process situation, it cover below scenario:

* Attach a device from the primary
* Detach a device from the primary
* Attach a device from a secondary
* Detach a device from a secondary

In primary-secondary process model, we assume ethernet devices are shared
by default, that means attach or detach a device on any process will
broadcast to all other processes through mp channel then device
information will be synchronized on all processes.

Any failure during attaching process will cause inconsistent status
between processes, so proper rollback action should be considered.

Test Case 1: Virtio-pmd primary and secondary process symmetric test
====================================================================

SW preparation: Change one line of the symmetric_mp sample and rebuild::

    vi ./examples/multi_process/symmetric_mp/main.c
    -.offloads = DEV_RX_OFFLOAD_CHECKSUM,

1. Bind one port to igb_uio, launch testpmd by below command::

    ./testpmd -l 1-6 -n 4 --socket-mem 2048,2048 --legacy-mem --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=2,client=1' --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1'  -- -i --nb-cores=4 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>start

2. Launch VM with two virtio ports, must set queues=2 as app receive packets from special queue which index same with proc-id::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char,path=./vhost-net,server -netdev type=vhost-user,id=mynet1,chardev=char,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,mrg_rxbuf=on,csum=on,mq=on,vectors=15  \
    -chardev socket,id=char1,path=./vhost-net1,server -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:03,netdev=mynet2,mrg_rxbuf=on,csum=on,mq=on,vectors=15  -vnc :10 -daemonize

3.  Bind virtio port to igb_uio::

    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x

4. Launch two process by example::

    ./examples/multi_process/symmetric_mp/build/symmetric_mp -l 1 -n 4 --proc-type=auto -- -p 3 --num-procs=2 --proc-id=0
    ./examples/multi_process/symmetric_mp/build/symmetric_mp -l 2 -n 4 --proc-type=secondary -- -p 3 --num-procs=2 --proc-id=1

5. Quit all process, check the packets number in rx/tx statistic like below for both primary process and secondary process::

    Port 0: RX - 27511680, TX - 256, Drop - 27499168
    Port 1: RX - 27499424, TX - 256, Drop - 27511424

Test Case 2: Virtio-pmd primary and secondary process hotplug test
==================================================================

1. Launch testpmd by below command::

    ./testpmd -l 1-6 -n 4 --socket-mem 2048,2048 --legacy-mem --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=2,client=1' --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1'  -- -i --nb-cores=4 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>start

2. Launch VM with two virtio ports, must set queues=2 as app receive packets from special queue which index same with proc-id::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 4 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char,path=./vhost-net,server -netdev type=vhost-user,id=mynet1,chardev=char,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,mrg_rxbuf=on,csum=on,mq=on,vectors=15  \
    -chardev socket,id=char1,path=./vhost-net1,server -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:03,netdev=mynet2,mrg_rxbuf=on,csum=on,mq=on,vectors=15  -vnc :10 -daemonize

3.  Bind virtio port to igb_uio::

    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x

4. Start sample code as primary process::

    ./examples/multi_process/hotplug_mp/build/hotplug_mp --proc-type=auto -- -p 3 --num-procs=2 --proc-id=0
    example> list
    list all etherdev
    0       0000:00:05.0
    1       0000:00:06.0

5. Start sample code as secondary process::

    ./examples/multi_process/hotplug_mp/build/hotplug_mp --proc-type=secondary -- -p 3 --num-procs=2 --proc-id=1
    example> list
    list all etherdev
    0       0000:00:05.0
    1       0000:00:06.0

6. Detach the virtual device from primary, check primary and secondary processes detach the share device successfully::

    example> detach 0000:00:05.0
    example> list
    list all etherdev
    1       0000:00:06.0

7. Attach a virtual device from secondary, check primary and secondary processes attach the share device successfully::

    example> attach 0000:00:05.0
    example> list
    list all etherdev
    0       0000:00:05.0
    1       0000:00:06.0

8. Repeat above attach and detach for 2 times.
