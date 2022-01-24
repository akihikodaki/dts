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

=========================
DPDK PMD for AF_XDP Tests
=========================

Description
===========

AF_XDP is a proposed faster version of AF_PACKET interface in Linux.
This test plan is to analysis the performance of DPDK PMD for AF_XDP.

Prerequisites
=============

1. Hardware::

    I40e 40G*1
    enp26s0f1 <---> IXIA_port_0

2. The NIC is located on the socket 1, so we define the cores of socket 1.

3. Clone kernel branch master v5.4, make sure you turn on XDP socket/BPF/I40E before compiling kernel::

    make menuconfig
    Networking support -->
         Networking options -->
                 [ * ] XDP sockets

4. Build kernel and replace your host kernel with it::

    cd bpf-next
    sh -c 'yes "" | make oldconfig'
    make -j64
    make modules_install install
    make install
    make headers_install
    cd tools/lib/bpf && make clean && make install && make install_headers && cd -
    make headers_install ARCH=x86_64 INSTALL_HDR_PATH=/usr
    grub-mkconfig -o /boot/grub/grub.cfg
    reboot

5. Build DPDK::

    cd dpdk
    CC=gcc meson -Denable_kmods=True  -Dlibdir=lib --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc

6. Involve lib::

    export LD_LIBRARY_PATH=/home/linux/tools/lib/bpf:$LD_LIBRARY_PATH    

Test case 1: single port test with PMD core and IRQ core are pinned to separate cores
=====================================================================================

1. Start the testpmd::

    ethtool -L enp26s0f1 combined 1
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --vdev net_af_xdp0,iface=enp26s0f1,start_queue=0,queue_count=1 --log-level=pmd.net.af_xdp:8  -- -i --nb-cores=1 --rxq=1 --txq=1 --port-topology=loop

2. Assign the kernel core::

    ./set_irq_affinity 3 enp26s0f1         #PMD and IRQs pinned to seperate cores
    ./set_irq_affinity 2 enp26s0f1         #PMD and IRQs pinned to same cores

3. Send packets by packet generator with different packet size, from 64 bytes to 1518 bytes, check the throughput.

Test case 2: two ports test with PMD cores and IRQ cores are pinned to separate cores
=====================================================================================

1. Start the testpmd::

    ethtool -L enp26s0f0 combined 1
    ethtool -L enp26s0f1 combined 1
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-3 --no-pci -n 4 \
    --vdev net_af_xdp0,iface=enp26s0f0 --vdev net_af_xdp1,iface=enp26s0f1 \
    --log-level=pmd.net.af_xdp:8 -- -i --auto-start --nb-cores=2 --rxq=1 --txq=1 --port-topology=loop

2. Assign the kernel cores::

    ./set_irq_affinity 4 enp26s0f0
    ./set_irq_affinity 5 enp26s0f1

3. Send packets by packet generator to port0 and port1 with different packet size, from 64 bytes to 1518 bytes, check the throughput at port0 and port1.

Test case 3: multi-queue test with PMD cores and IRQ cores are pinned to separate cores
=======================================================================================

1. Set hardware queues::

      ethtool -L enp26s0f1 combined 2

2. Start the testpmd with two queues::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-3 -n 6 --no-pci \
      --vdev net_af_xdp0,iface=enp26s0f1,start_queue=0,queue_count=2 \
      -- -i --auto-start --nb-cores=2 --rxq=2 --txq=2 --port-topology=loop

3. Assign the kernel cores::

      ./set_irq_affinity 4-5 enp26s0f1

4. Send packets with different dst IP address by packet generator with different packet size from 64 bytes to 1518 bytes, check the throughput and ensure the packets were distributed to the two queues.

Test case 4: two ports test with PMD cores and IRQ cores pinned to same cores
=============================================================================

1. Start the testpmd::

    ethtool -L enp26s0f0 combined 1
    ethtool -L enp26s0f1 combined 1
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29,30-31 --no-pci -n 4 \
    --vdev net_af_xdp0,iface=enp26s0f0 --vdev net_af_xdp1,iface=enp26s0f1 \
    -- -i --auto-start --nb-cores=2 --rxq=1 --txq=1 --port-topology=loop

2. Assign the kernel cores::

    ./set_irq_affinity 30 enp26s0f0
    ./set_irq_affinity 31 enp26s0f1

3. Send packets by packet generator to port0 and port1 with different packet size, from 64 bytes to 1518 bytes, check the throughput at port0 and port1.

Test case 5: multi-queue test with PMD cores and IRQ cores pinned to same cores
===============================================================================

1. Set hardware queues::

      ethtool -L enp26s0f1 combined 2

2. Start the testpmd with two queues::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 29,30-31 -n 6 --no-pci \
      --vdev net_af_xdp0,iface=enp26s0f1,start_queue=0,queue_count=2 \
      -- -i --auto-start --nb-cores=2 --rxq=2 --txq=2 --port-topology=loop

3. Assign the kernel cores::

      ./set_irq_affinity 30-31 enp26s0f1

4. Send packets with different dst IP address by packet generator with different packet size from 64 bytes to 1518 bytes, check the throughput and ensure packets were distributed to the two queues.

Test case 6: one port with two vdev and single queue test
=========================================================

1. Set hardware queues::

      ethtool -L enp26s0f1 combined 2

2. Start the testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-3 --no-pci -n 4 \
    --vdev net_af_xdp0,iface=enp26s0f1,start_queue=0,queue_count=1 \
    --vdev net_af_xdp1,iface=enp26s0f1,start_queue=1,queue_count=1 \
    -- -i --nb-cores=2 --rxq=1 --txq=1 --port-topology=loop

3. Assign the kernel core::

    ./set_irq_affinity 4-5 enp26s0f1    #PMD and IRQs pinned to seperate cores
    ./set_irq_affinity 2-3 enp26s0f1    #PMD and IRQs pinned to same cores

4. Set flow director rules in kernel, mapping queue0 and queue1 of the port::

    ethtool -N enp26s0f1 rx-flow-hash udp4 fn
    ethtool -N enp26s0f1 flow-type udp4 src-port 4242 dst-port 4242 action 1
    ethtool -N enp26s0f1 flow-type udp4 src-port 4243 dst-port 4243 action 0

5. Send packets match the rules to port, check the throughput at queue0 and queue1.

Test case 7: one port with two vdev and multi-queues test
=========================================================

1. Set hardware queues::

      ethtool -L enp26s0f1 combined 8

2. Start the testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-9 --no-pci -n 6 \
    --vdev net_af_xdp0,iface=enp26s0f1,start_queue=0,queue_count=4 \
    --vdev net_af_xdp1,iface=enp26s0f1,start_queue=4,queue_count=4 --log-level=pmd.net.af_xdp:8 \
    -- -i --rss-ip --nb-cores=8 --rxq=4 --txq=4 --port-topology=loop

3. Assign the kernel core::

    ./set_irq_affinity 10-17 enp26s0f1    #PMD and IRQs pinned to seperate cores
    ./set_irq_affinity 2-9 enp26s0f1    #PMD and IRQs pinned to same cores

4. Send random ip packets , check the packets were distributed to queue0 ~ queue7.
