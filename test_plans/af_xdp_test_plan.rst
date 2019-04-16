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
    enp216s0f1 <---> IXIA_port_0

2. The NIC is located on the socket 1, so we define the cores of socket 1.

3. Take the kernel >= v5.1-rc1, build kernel and replace your host
   kernel with it.
   Update compiler to the proper version.
   Make sure you turn on XDP sockets when compiling::

    Networking support -->
         Networking options -->
                 [ * ] XDP sockets

4. Build libbpf in tools/lib/bpf::

    cd tools/lib/bpf
    make

   Then copy the libbpf.a and libbpf.so to /usr/lib64

5. Set DUT port only has one queue::

    ethtool -L enp216s0f0 combined 1
    ethtool -L enp216s0f1 combined 1

6. Explicitly enable AF_XDP pmd by adding below line to
   config/common_linux::

    CONFIG_RTE_LIBRTE_PMD_AF_XDP=y

Test case 1: 1 port, 1 kernel core, 1 user core
===============================================

1. Start the testpmd::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 30,31 --no-pci -n 6 \
    --vdev net_af_xdp0,iface=enp216s0f0,queue=0 --file-prefix=port0 \
    --socket-mem 1024,1024 -- -a --nb-cores=1 -i --rxq=1 --txq=1 \
    --port-topology=loop

2. Assign the kernel core::

    ./set_irq_affinity 33 enp216s0f0

3. Send packet with packet generator with different packet size,
   from 64 bytes to 1518 bytes, check the throughput.

Test case 2: 2 ports, 2 kernel cores, 1 user cores
==================================================

1. Start the testpmd::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 30,32 --no-pci -n 6 \
    --vdev net_af_xdp0,iface=enp216s0f0,queue=0 --file-prefix=port0 \
    --socket-mem 1024,1024 -- -a  --nb-cores=1 -i --rxq=1 --txq=1 \
    --port-topology=loop

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 31,33 --no-pci -n 6 \
    --vdev net_af_xdp1,iface=enp216s0f1,queue=0 --file-prefix=port1 \
    --socket-mem 1024,1024 -- -a --nb-cores=1 -i --rxq=1 --txq=1 \
    --port-topology=loop

2. Assign the kernel core::

    ./set_irq_affinity 35 enp216s0f0
    ./set_irq_affinity 36 enp216s0f1

3. Send packet with packet generator with different packet size,
   from 64 bytes to 1518 bytes, check the throughput.
