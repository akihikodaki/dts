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

=============================================
Primary/secondary process with vdev test plan
=============================================

This test plan will test vdev primary/secondary by symmetric multi-process example, which demonstrates how a set of processes can run in parallel,
with each process performing the same set of packet processing operations.

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

Test Case 1: Virtio primary and secondary process test
======================================================

SW preparation: Change one line of the symmetric_mp sample and rebuild::

    vi ./examples/multi_process/symmetric_mp/main.c
    -.offloads = DEV_RX_OFFLOAD_CHECKSUM,

1. Bind one port to igb_uio, launch testpmd by below command::

    ./testpmd -l 1-6 -n 4 --socket-mem 2048,2048 --legacy-mem --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=2,client=1' --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1'  -- -i --nb-cores=4 --rxq=2 --txq=2 --txd=1024 --rxd=1024
    testpmd>set fwd txonly
    testpmd>start

2. Launch VM with two virtio ports, must set queues=2 as app receive packets from special queue which index same with proc-id::

    qemu-system-x86_64 -name us-vhost-vm \
     -cpu host -enable-kvm -m 4096 -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=4,sockets=1 -drive file=/home/osimg/ubuntu16.img \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,vlan=2,macaddr=00:00:00:08:e8:aa,addr=1f -net user,vlan=2,hostfwd=tcp:127.0.0.1:6002-:22 \
     -chardev socket,id=char,path=./vhost-net,server -netdev type=vhost-user,id=mynet1,chardev=char,vhostforce,queues=2 \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,mrg_rxbuf=on,csum=on,mq=on,vectors=15  \
     -chardev socket,id=char1,path=./vhost-net1,server -netdev type=vhost-user,id=mynet2,chardev=char1,vhostforce,queues=2 \
     -device virtio-net-pci,mac=52:54:00:00:00:03,netdev=mynet2,mrg_rxbuf=on,csum=on,mq=on,vectors=15  \
     -vnc :10 -daemonize

3.  Bind virtio port to igb_uio::

    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x
    ./usertools/dpdk-devbind.py --bind=igb_uio xx:xx.x

4. Launch two process by example::

    examples/multi_process/symmetric_mp -l 1 -n 4 --proc-type=auto -- -p 3 --num-procs=2 --proc-id=0
    examples/multi_process/symmetric_mp -l 2 -n 4 --proc-type=secondary -- -p 3 --num-procs=2 --proc-id=1

5. Quit all process, check the packets number in rx/tx statistic like below for both primary process and secondary process::

    Port 0: RX - 27511680, TX - 256, Drop - 27499168
    Port 1: RX - 27499424, TX - 256, Drop - 27511424