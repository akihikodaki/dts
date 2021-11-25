.. Copyright (c) <2021>, Intel Corporation
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

==========================================================
DMA-accelerated Tx operations for vhost-user PMD test plan
==========================================================

Overview
--------

This feature supports to offload large data movement in vhost enqueue operations
from the CPU to the I/OAT device for every queue. Note that I/OAT acceleration
is just enabled for split rings now. In addition, a queue can only use one I/OAT
device, and I/OAT devices cannot be shared among vhost ports and queues. That is,
an I/OAT device can only be used by one queue at a time. DMA devices used by
queues are assigned by users; for a queue without assigning a DMA device, the
PMD will leverages librte_vhost to perform vhost enqueue operations. Moreover,
users cannot enable I/OAT acceleration for live-migration. Large copies are
offloaded from the CPU to the DMA engine in an asynchronous manner. The CPU just
submits copy jobs to the DMA engine and without waiting for DMA copy completion;
there is no CPU intervention during DMA data transfer. By overlapping CPU
computation and DMA copy, we can save precious CPU cycles and improve the overall
throughput for vhost-user PMD based applications, like OVS. Due to startup overheads
associated with DMA engines, small copies are performed by the CPU.

We introduce a new vdev parameter to enable DMA acceleration for Tx
operations of queues:

 - dmas: This parameter is used to specify the assigned DMA device of
   a queue.

Here is an example:
 $ ./dpdk-testpmd -c f -n 4 \
   --vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas=[txq0@80:04.0]'

Test Case 1: PVP Split all path with DMA-accelerated vhost enqueue
==================================================================

Packet pipeline: 
================
TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

1. Bind one cbdma port and one nic port to vfio-pci, then launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas=[txq0@80:04.0]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

2. Launch virtio-user with inorder mergeable path::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send imix packets [64,1518] from packet generator, check the throughput can get expected data, restart vhost port, then check throughput again::

    testpmd>show port stats all
    testpmd>stop
    testpmd>start
    testpmd>show port stats all

4. Relaunch virtio-user with mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,queues=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

5. Relaunch virtio-user with inorder non-mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

6. Relaunch virtio-user with non-mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,queues=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

7. Relaunch virtio-user with vector_rx path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,queues=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

Test Case 2: Split ring dynamic queue number test for DMA-accelerated vhost Tx operations
=========================================================================================

1. Bind 8 cbdma channels and one nic port to vfio-pci, then launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29  \
     --file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1' \
     -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
     >set fwd mac
     >start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 30-31 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=8,server=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

3. Send imix packets from packet generator with random ip, check perforamnce can get target.

4. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

5. Quit vhost port and relaunch vhost with 4 queues w/ cbdma::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=4,client=1,dmas=[txq0@00:04.0;txq1@00:04.1;txq2@00:04.2;txq3@00:04.3]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=4 --rxq=4
    >set fwd mac
    >start

6. Send imix packets from packet generator with random ip, check perforamnce can get target.

7. Stop vhost port, check vhost RX and TX direction both exist packtes in 4 queues from vhost log.

8. Quit vhost port and relaunch vhost with 8 queues w/ cbdma::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

9. Send imix packets from packet generator with random ip, check perforamnce can get target.

10. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

Test Case 3: PVP packed ring all path with DMA-accelerated vhost enqueue
========================================================================

Packet pipeline: 
================
TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

1. Bind one cbdma port and one nic port to vfio-pci, then launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas=[txq0@80:04.0]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

2. Launch virtio-user with inorder mergeable path::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=1,packed_vq=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send imix packets [64,1518] from packet generator, check the throughput can get expected data, restart vhost port, then check throughput again::

    testpmd>show port stats all
    testpmd>stop
    testpmd>start
    testpmd>show port stats all

4. Relaunch virtio-user with mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=0,queues=1,packed_vq=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

5. Relaunch virtio-user with inorder non-mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=1,packed_vq=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

6. Relaunch virtio-user with non-mergeable path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=0,queues=1,packed_vq=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

7. Relaunch virtio-user with vectorized path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=1,packed_vq=1 \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

8. Relaunch virtio-user with vector_rx path, then repeat step 3::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=0,in_order=1,queues=1,packed_vq=1 \
    -- -i --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

Test Case 4: Packed ring dynamic queue number test for DMA-accelerated vhost Tx operations
==========================================================================================

1. Bind 8 cbdma channels and one nic port to vfio-pci, then launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29  \
     --file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1' \
     -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
     >set fwd mac
     >start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 30-31 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=8,server=1,packed_vq=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

3. Send imix packets from packet generator with random ip, check perforamnce can get target.

4. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

5. Quit vhost port and relaunch vhost with 4 queues w/ cbdma::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=4,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=4 --rxq=4
    >set fwd mac
    >start

6. Send imix packets from packet generator with random ip, check perforamnce can get target.

7. Stop vhost port, check vhost RX and TX direction both exist packtes in 4 queues from vhost log.

8. Quit vhost port and relaunch vhost with 8 queues w/ cbdma::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 28-29  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024 --txq=8 --rxq=8
    >set fwd mac
    >start

9. Send imix packets from packet generator with random ip, check perforamnce can get target.

10. Stop vhost port, check vhost RX and TX direction both exist packtes in 8 queues from vhost log.

Test Case 5: Compare PVP split ring performance between CPU copy, CBDMA copy and Sync copy
==========================================================================================

1. Bind one cbdma port and one nic port which on same numa to vfio-pci, then launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=1,client=1,dmas=[txq0@00:01.0]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

2. Launch virtio-user with inorder mergeable path::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=1,server=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

3. Send packets with 64b and 1518b seperately from packet generator, record the throughput as sync copy throughput for 64b and cbdma copy for 1518b::

    testpmd>show port stats all

4.Quit vhost side, relaunch with below cmd::

 ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=1,client=1,dmas=[txq0@00:01.0]' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

5. Send packets with 1518b from packet generator, record the throughput as sync copy throughput for 1518b::

    testpmd>show port stats all

6. Quit two testpmd, relaunch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --file-prefix=vhost --vdev 'net_vhost0,iface=/tmp/s0,queues=1' \
    -- -i --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

7. Launch virtio-user with inorder mergeable path::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=/tmp/s0,mrg_rxbuf=1,in_order=1,queues=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024
    >set fwd mac
    >start

8. Send packets with 64b from packet generator, record the throughput as cpu copy for 64b::

    testpmd>show port stats all

9. Check performance can meet below requirement::

   (1)CPU copy vs. sync copy delta < 10% for 64B packet size
   (2)CBDMA copy vs sync copy delta > 5% for 1518 packet size
