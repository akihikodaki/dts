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

    I40e 25G*2
    enp216s0f0 <---> IXIA_port_0
    enp216s0f1 <---> IXIA_port_1

2. The NIC is located on the socket 1, so we define the cores of socket 1.

3. Take the kernel >= v5.2-rc2, build kernel and replace your host
   kernel with it.
   Update compiler to the proper version.
   Make sure you turn on XDP sockets when compiling::

    Networking support -->
         Networking options -->
                 [ * ] XDP sockets

   Then compile the kernel::

    make -j16
    make modules_install install

4. Build libbpf in tools/lib/bpf::

    cd tools/lib/bpf
    make install_lib prefix=/usr
    make install_headers prefix=/usr

5. Explicitly enable AF_XDP pmd by adding below line to
   config/common_linux::

    CONFIG_RTE_LIBRTE_PMD_AF_XDP=y

   Then build DPDK.

6. Set DUT port only has one queue::

    ethtool -L enp216s0f0 combined 1
    ethtool -L enp216s0f1 combined 1

Test case 1: single port
========================

1. Start the testpmd::

    ./testpmd -l 29,30 -n 6 --no-pci --vdev net_af_xdp0,iface=enp216s0f0 \
    -- -i --nb-cores=1 --rxq=1 --txq=1 --port-topology=loop

2. Assign the kernel core::

    ./set_irq_affinity 34 enp216s0f0

3. Send packets by packet generator with different packet size,
   from 64 bytes to 1518 bytes, check the throughput.

Test case 2: two ports
======================

1. Start the testpmd::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 29,30-31 --no-pci -n 6 \
    --vdev net_af_xdp0,iface=enp216s0f0 --vdev net_af_xdp1,iface=enp216s0f1 \
    -- -i --nb-cores=2 --rxq=1 --txq=1

2. Assign the kernel core::

    ./set_irq_affinity 33 enp216s0f0
    ./set_irq_affinity 34 enp216s0f1

3. Send packets by packet generator port0 with different packet size,
   from 64 bytes to 1518 bytes, check the throughput at port1.

4. Send packets by packet generator port0 and port1 with different packet size,
   from 64 bytes to 1518 bytes, check the throughput at port0 and port1.

Test case 3: zero copy
======================

1. Start the testpmd::

    ./testpmd -l 29,30 -n 6 --no-pci \
    --vdev net_af_xdp0,iface=enp216s0f0,pmd_zero_copy=1 \
    -- -i --nb-cores=1 --rxq=1 --txq=1 --port-topology=loop

2. Assign the kernel core::

    ./set_irq_affinity 34 enp216s0f0

3. Send packets by packet generator with different packet size,
   from 64 bytes to 1518 bytes, check the throughput.

Test case 4: multiqueue
=======================

1. One queue.

  1) Start the testpmd with one queue::

      ./testpmd -l 29,30 -n 6 --no-pci \
      --vdev net_af_xdp0,iface=enp216s0f0,start_queue=0,queue_count=1 \
      -- -i --nb-cores=1 --rxq=1 --txq=1 --port-topology=loop

  2) Assign the kernel core::

      ./set_irq_affinity 34 enp216s0f0

  3) Send packets with different dst IP address by packet generator
     with different packet size from 64 bytes to 1518 bytes, check the throughput.

2. Four queues.

  1) Set hardware queue::

      ethtool -L enp216s0f0 combined 4

  2) Start the testpmd with four queues::

      ./testpmd -l 29,30-33 -n 6 --no-pci \
      --vdev net_af_xdp0,iface=enp216s0f0,start_queue=0,queue_count=4 \
      -- -i --nb-cores=4 --rxq=4 --txq=4 --port-topology=loop

  3) Assign the kernel core::

      ./set_irq_affinity 34-37 enp216s0f0

  4) Send packets with different dst IP address by packet generator
      with different packet size from 64 bytes to 1518 bytes, check the throughput.
      The packets were distributed to the four queues.

Test case 5: multiqueue and zero copy
=====================================

1. One queue and zero copy.

  1) Set hardware queue::

      ethtool -L enp216s0f0 combined 1

  2) Start the testpmd with one queue::

      ./testpmd -l 29,30 -n 6 --no-pci \
      --vdev net_af_xdp0,iface=enp216s0f0,start_queue=0,queue_count=1,pmd_zero_copy=1 \
      -- -i --nb-cores=1 --rxq=1 --txq=1 --port-topology=loop

  3) Assign the kernel core::

      ./set_irq_affinity 34 enp216s0f0

  4) Send packets with different dst IP address by packet generator
     with different packet size from 64 bytes to 1518 bytes, check the throughput.
     Expect the performance is better than non-zero-copy.

2. Four queues and zero copy.

  1) Set hardware queue::

      ethtool -L enp216s0f0 combined 4

  2) Start the testpmd with four queues::

      ./testpmd -l 29,30-33 -n 6 --no-pci \
      --vdev net_af_xdp0,iface=enp216s0f0,start_queue=0,queue_count=4,pmd_zero_copy=1 \
      -- -i --nb-cores=4 --rxq=4 --txq=4 --port-topology=loop

  3) Assign the kernel core::

      ./set_irq_affinity 34-37 enp216s0f0

  4) Send packets with different dst IP address by packet generator
     with different packet size from 64 bytes to 1518 bytes, check the throughput.
     The packets were distributed to the four queues.
     Expect the performance of four queues is better than one queue.
     Expect the performance is better than non-zero-copy.

Test case 6: need_wakeup
========================

1. Set hardware queue::

    ethtool -L enp216s0f0 combined 1

2. Start the testpmd with one queue::

    ./testpmd -l 29,30 -n 6 --no-pci --vdev net_af_xdp0,iface=enp216s0f0 \
    -- -i --nb-cores=1 --rxq=1 --txq=1 --port-topology=loop

3. Assign the same core::

    ./set_irq_affinity 30 enp216s0f0

4. Send packets by packet generator with different packet size from 64 bytes
   to 1518 bytes, check the throughput.
   Expect the performance is better than no need_wakeup.

Test case 7: xdpsock sample performance
=======================================

1. One queue.

  1) Set hardware queue::

      ethtool -L enp216s0f0 combined 1

  2) Start the xdp socket with one queue::

      #taskset -c 30 ./xdpsock -l -i enp216s0f0

  3) Assign the kernel core::

      ./set_irq_affinity 34 enp216s0f0

  4) Send packets with different dst IP address by packet generator
     with different packet size from 64 bytes to 1518 bytes, check the throughput.

2. Four queues.

  1) Set hardware queue::

      ethtool -L enp216s0f0 combined 4

  2) Start the xdp socket with four queues::

      #taskset -c 30 ./xdpsock -l -i enp216s0f0 -q 0
      #taskset -c 31 ./xdpsock -l -i enp216s0f0 -q 1
      #taskset -c 32 ./xdpsock -l -i enp216s0f0 -q 2
      #taskset -c 33 ./xdpsock -l -i enp216s0f0 -q 3

  3) Assign the kernel core::

      ./set_irq_affinity 34-37 enp216s0f0

  4) Send packets with different dst IP address by packet generator
     with different packet size from 64 bytes to 1518 bytes, check the throughput.
     The packets were distributed to the four queues.
     Expect the performance of four queues is better than one queue.

3. Need_wakeup.

  1) Set hardware queue::

      ethtool -L enp216s0f0 combined 1

  2) Start the xdp socket with four queues::

      #taskset -c 30 ./xdpsock -l -i enp216s0f0

  3) Assign the kernel core::

      ./set_irq_affinity 30 enp216s0f0

  4) Send packets by packet generator with different packet size from 64 bytes
     to 1518 bytes, check the throughput.
     Expect the performance is better than no need_wakeup.