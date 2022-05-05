.. Copyright (c) <2022>, Intel Corporation
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

Description
===========

This document provides the test plan for testing Vhost asynchronous
data path with CBDMA driver in the PVP topology environment with testpmd.

CBDMA is a kind of DMA engine, Vhost asynchronous data path leverages DMA devices
to offload memory copies from the CPU and it is implemented in an asynchronous way.
Linux kernel and DPDK provide CBDMA driver, no matter which driver is used,
DPDK DMA library is used in data-path to offload copies to CBDMA, and the only difference is which driver configures CBDMA.
It enables applications, like OVS, to save CPU cycles and hide memory copy overhead, thus achieving higher throughput.
Vhost doesn't manage DMA devices and applications, like OVS, need to manage and configure CBDMA devices.
Applications need to tell vhost what CBDMA devices to use in every data path function call.
This design enables the flexibility for applications to dynamically use DMA channels in different
function modules, not limited in vhost. In addition, vhost supports M:N mapping between vrings
and DMA virtual channels. Specifically, one vring can use multiple different DMA channels
and one DMA channel can be shared by multiple vrings at the same time.

Note:
1. When CBDMA devices are bound to vfio driver, VA mode is the default and recommended.
For PA mode, page by page mapping may exceed IOMMU's max capability, better to use 1G guest hugepage.
2. DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

For more about dpdk-testpmd sample, please refer to the DPDK docments:
https://doc.dpdk.org/guides/testpmd_app_ug/run_app.html
For virtio-user vdev parameter, you can refer to the DPDK docments:
https://doc.dpdk.org/guides/nics/virtio.html#virtio-paths-selection-and-usage.

Prerequisites
=============

Topology
--------
      Test flow: TG-->NIC-->Vhost-->Virtio-->Vhost-->NIC-->TG

Hardware
--------
      Supportted NICs: ALL

Software
--------
      Trex:http://trex-tgn.cisco.com/trex/release/v2.26.tar.gz

General set up
--------------
1. Compile DPDK::

      # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=<dpdk build dir>
      # ninja -C <dpdk build dir> -j 110
      For example：
      CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=x86_64-native-linuxapp-gcc
      ninja -C x86_64-native-linuxapp-gcc -j 110

2. Get the PCI device ID and DMA device ID of DUT, for example, 0000:18:00.0 is PCI device ID, 0000:00:04.0, 0000:00:04.1 are DMA device IDs::

      <dpdk dir># ./usertools/dpdk-devbind.py -s

      Network devices using kernel driver
      ===================================
      0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci

      DMA devices using kernel driver
      ===============================
      0000:00:04.0 'Sky Lake-E CBDMA Registers 2021' drv=ioatdma unused=vfio-pci
      0000:00:04.1 'Sky Lake-E CBDMA Registers 2021' drv=ioatdma unused=vfio-pci

Test case
=========

Common steps
------------
1. Bind 1 NIC port and CBDMA devices to vfio-pci::

      <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
      <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port DMA device id>

      For example, Bind 1 NIC port and 2 CBDMA devices::
      ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:18.0
      ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:04.0,0000:00:04.1

2. Send imix packets [64,1518] to NIC by traffic generator::

      The imix packets include packet size [64, 128, 256, 512, 1024, 1518], and the format of packet is as follows.
      +-------------+-------------+-------------+-------------+
      | MAC         | MAC         | IPV4        | IPV4        |
      | Src address | Dst address | Src address | Dst address |
      |-------------|-------------|-------------|-------------|
      | Random MAC  | Virtio mac  | Random IP   | Random IP   |
      +-------------+-------------+-------------+-------------+
      All the packets in this test plan use the Virtio mac: 00:11:22:33:44:10.

Test Case 1: PVP split ring all path vhost enqueue operations with 1 to 1 mapping between vrings and CBDMA virtual channels
---------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of split ring in each virtio path with 1 core and 1 queue
when vhost uses the asynchronous enqueue operations and the mapping between vrings and CBDMA virtual channels is 1:1.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 1 CBDMA device to vfio-pci, as common step 1.

2. Launch vhost by below command::

      <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 -a 0000:00:04.0 \
      --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=1,dmas=[txq0],dma_ring_size=2048' \
      --iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024 \
      --lcore-dma=[lcore11@0000:00:04.0]
      testpmd> set fwd mac
      testpmd> start

3. Launch virtio-user with inorder mergeable path::

      <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
      --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=1 \
      -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
      testpmd> set fwd mac
      testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and then check the throughput can get expected data::

      testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

      testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throuhput can get expected data::

      testpmd> start
      testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

      <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
      --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=0,queues=1 \
      -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
      testpmd> set fwd mac
      testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

      <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
      --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,queues=1 \
      -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
      testpmd> set fwd mac
      testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

      <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
      --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,queues=1 \
      -- -i --enable-hw-vlan-strip --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
      testpmd> set fwd mac
      testpmd> start

.. note::

    Rx offload(s) are requested when using split ring non-mergeable path. So add the parameter "--enable-hw-vlan-strip".

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

      <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
      --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,vectorized=1,queues=1 \
      -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
      testpmd> set fwd mac
      testpmd> start

11. Quit all testpmd and relaunch vhost with iova=pa by below command::

      <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 -a 0000:00:04.0
      --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=1,dmas=[txq0],dma_ring_size=2048' \
      --iova=pa -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024 \
      --lcore-dma=[lcore11@0000:00:04.0]
      testpmd> set fwd mac
      testpmd> start

12. Rerun steps 3-11.

Test Case 2: PVP split ring all path multi-queues vhost enqueue operations with 1 to 1 mapping between vrings and CBDMA virtual channels
----------------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of split ring in each virtio path with multi-queues
when vhost uses the asynchronous enqueue operations and the mapping between vrings and CBDMA virtual channels is 1:1.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 8 CBDMA devices to vfio-pci, as common step 1.

2. Launch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.3,lcore15@0000:00:04.4,lcore16@0000:00:04.5,lcore17@0000:00:04.6,lcore18@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

3. Launch virtio-user with inorder mergeable path::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and check the throughput can get expected data::

       testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

       testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throuhput can get expected data::

       testpmd> start
       testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=0,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,queues=8 \
       -- -i --enable-hw-vlan-strip --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,vectorized=1,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

11. Quit all testpmd and relaunch vhost with iova=pa by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=pa -- -i --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.3,lcore15@0000:00:04.4,lcore16@0000:00:04.5,lcore17@0000:00:04.6,lcore18@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

12. Rerun step 7.

Test Case 3: PVP split ring all path multi-queues vhost enqueue operations with M to 1 mapping between vrings and CBDMA virtual channels
----------------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of split ring in each virtio path with multi-queues
when vhost uses the asynchronous enqueue operations and the mapping between vrings and CBDMA virtual channels is M:1.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 8 CBDMA devices to vfio-pci, as common step 1.

2. Launch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 -a 0000:00:04.0 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0]
       testpmd> set fwd mac
       testpmd> start

3. Launch virtio-user with inorder mergeable path::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

3. Send imix packets [64,1518] from packet generator as common step2, and check the throughput can get expected data::

       testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

       testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throught can get expected data::

       testpmd> start
       testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=0,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,queues=8 \
       -- -i --enable-hw-vlan-strip --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,vectorized=1,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

11. Quit all testpmd and relaunch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 -a 0000:00:04.0 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=3 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.0]
       testpmd> set fwd mac
       testpmd> start

12. Rerun steps 4-6.

13. Quit all testpmd and relaunch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 -a 0000:00:04.0 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.0,lcore14@0000:00:04.0,lcore15@0000:00:04.0,lcore16@0000:00:04.0,lcore17@0000:00:04.0,lcore18@0000:00:04.0]
       testpmd> set fwd mac
       testpmd> start

14. Rerun steps 7.

15. Quit all testpmd and relaunch vhost with iova=pa by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 -a 0000:00:04.0 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=pa -- -i --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.0,lcore14@0000:00:04.0,lcore15@0000:00:04.0,lcore16@0000:00:04.0,lcore17@0000:00:04.0,lcore18@0000:00:04.0]
       testpmd> set fwd mac
       testpmd> start

16. Rerun steps 7.

Test Case 4: PVP split ring all path vhost enqueue operations with 1 to N mapping between vrings and CBDMA virtual channels
---------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of split ring in each virtio path when vhost uses
the asynchronous enqueue operations and the mapping between vrings and CBDMA virtual channels is 1:N.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 8 CBDMA devices to vfio-pci, as common step 1.

2. Launch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=1,dmas=[txq0],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

3. Launch virtio-user with inorder mergeable path::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and check the throughput can get expected data::

       testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

       testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throught can get expected data::

       testpmd> start
       testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=0,queues=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,queues=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,queues=1 \
       -- -i --enable-hw-vlan-strip --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,vectorized=1,queues=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

11. Quit all testpmd and relaunch vhost with iova=pa by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=1,dmas=[txq0],dma_ring_size=2048' \
       --iova=pa -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

12. Rerun steps 9.

Test Case 5: PVP split ring all path multi-queues vhost enqueue operations with M to N mapping between vrings and CBDMA virtual channels
----------------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of split ring in each virtio path with multi-queues
when vhost uses the asynchronous enqueue operations and the mapping between vrings and CBDMA virtual channels is M:N.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 8 CBDMA devices to vfio-pci, as common step 1.

2. Launch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

3. Launch virtio-user with inorder mergeable path::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and check the throughput can get expected data::

       testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

       testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throught can get expected data::

       testpmd> start
       testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=0,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,queues=8 \
       -- -i --enable-hw-vlan-strip --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,vectorized=1,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

11. Quit all testpmd and relaunch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

12. Rerun steps 8.

13. Quit all testpmd and relaunch vhost with iova=pa by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=pa -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

14. Rerun steps 10.

Test Case 6: PVP split ring dynamic queue number vhost enqueue operations with M to N mapping between vrings and CBDMA virtual channels
---------------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of split ring when vhost uses the asynchronous enqueue operations
and if the vhost-user can work well when the queue number dynamic change. Both iova as VA and PA mode have been tested.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 8 CBDMA devices to vfio-pci, as common step 1.

2. Launch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,client=1' \
       --iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

3. Launch virtio-user by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=8,server=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and check the throughput can get expected data::

       testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log.

       testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throught can get expected data::

       testpmd> start
       testpmd> show port stats all

7. Quit and relaunch vhost with 1:1 mapping between vrings and CBDMA virtual channels, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3]' \
       --iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.3]
       testpmd> set fwd mac
       testpmd> start

8. Quit and relaunch vhost with M:N(1:N;M<N) mapping between vrings and CBDMA virtual channels, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18  --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq6;txq7]' \
       --iova=va -- -i --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.7,lcore12@0000:00:04.1,lcore12@0000:00:04.2,lcore12@0000:00:04.3,lcore13@0000:00:04.2,lcore13@0000:00:04.3,lcore13@0000:00:04.4,lcore14@0000:00:04.2,lcore14@0000:00:04.3,lcore14@0000:00:04.4,lcore14@0000:00:04.5,lcore15@0000:00:04.0,lcore15@0000:00:04.1,lcore15@0000:00:04.2,lcore15@0000:00:04.3,lcore15@0000:00:04.4,lcore15@0000:00:04.5,lcore15@0000:00:04.6,lcore15@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

9. Quit and relaunch vhost with diff M:N(M:1;M>N) mapping between vrings and CBDMA virtual channels, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
       --iova=va -- -i --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.1,lcore14@0000:00:04.2,lcore15@0000:00:04.1,lcore15@0000:00:04.2]
       testpmd> set fwd mac
       testpmd> start

10. Quit and relaunch vhost with iova=pa by below command, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
       --iova=pa -- -i --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.1,lcore14@0000:00:04.2,lcore15@0000:00:04.1,lcore15@0000:00:04.2]
       testpmd> set fwd mac
       testpmd> start

Test Case 7: PVP packed ring all path vhost enqueue operations with 1 to 1 mapping between vrings and CBDMA virtual channels
----------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of packed ring in each virtio path with 1 core and 1 queue
when vhost uses the asynchronous enqueue operations and the mapping between vrings and CBDMA virtual channels is 1:1.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 1 CBDMA device to vfio-pci, as common step 1.

2. Launch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost  -a 0000:18:00.0 -a 0000:00:04.0
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=1,dmas=[txq0],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0]
       testpmd> set fwd mac
       testpmd> start

3. Launch virtio-user with inorder mergeable path::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=1,packed_vq=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and check the throughput can get expected data::

       testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

       testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throught can get expected data::

       testpmd> start
       testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=0,queues=1,packed_vq=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,queues=1,packed_vq=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,queues=1,packed_vq=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

.. note::

   If building and running environment support (AVX512 || NEON) && in-order feature is negotiated && Rx mergeable
   is not negotiated && TCP_LRO Rx offloading is disabled && vectorized option enabled, packed virtqueue vectorized Rx path will be selected.

11. Relaunch virtio-user with vectorized path and ring size is not power of 2, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=1,queue_size=1025 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1025 --rxd=1025
       testpmd> set fwd mac
       testpmd> start

12. Quit all testpmd and relaunch vhost with iova=pa by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 -a 0000:00:04.0 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=1,dmas=[txq0],dma_ring_size=2048' \
       --iova=pa -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0]
       testpmd> set fwd mac
       testpmd> start

12. Rerun steps 3-6.

Test Case 8: PVP packed ring all path multi-queues vhost enqueue operations with 1 to 1 mapping between vrings and CBDMA virtual channels
-----------------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of packed ring in each virtio path with multi-queues
when vhost uses the asynchronous enqueue operations and the mapping between vrings and CBDMA virtual channels is 1:1.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 8 CBDMA devices to vfio-pci, as common step 1.

2. Launch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.3,lcore15@0000:00:04.4,lcore16@0000:00:04.5,lcore17@0000:00:04.6,lcore18@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

3. Launch virtio-user with inorder mergeable path::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and check the throughput can get expected data::

       testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

       testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throught can get expected data::

       testpmd> start
       testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=0,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

11. Relaunch virtio-user with vectorized path and ring size is not power of 2, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=8,queue_size=1025 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1025 --rxd=1025
       testpmd> set fwd mac
       testpmd> start

12. Quit all testpmd and relaunch vhost with iova=pa by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=pa -- -i --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.3,lcore15@0000:00:04.4,lcore16@0000:00:04.5,lcore17@0000:00:04.6,lcore18@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

13. Rerun step 7.

Test Case 9: PVP packed ring all path multi-queues vhost enqueue operations with M to 1 mapping between vrings and CBDMA virtual channels
-----------------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of packed ring in each virtio path with multi-queues
when vhost uses the asynchronous enqueue operations and the mapping between vrings and CBDMA virtual channels is M:1.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 1 CBDMA device to vfio-pci, as common step 1.

2. Launch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 -a 0000:00:04.0 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0]
       testpmd> set fwd mac
       testpmd> start

3. Launch virtio-user with inorder mergeable path::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and check the throughput can get expected data::

       testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

       testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throught can get expected data::

       testpmd> start
       testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=0,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=8 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

11. Relaunch virtio-user with vectorized path and ring size is not power of 2, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=8,queue_size=1025 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1025 --rxd=1025
       testpmd> set fwd mac
       testpmd> start

12. Quit all testpmd and relaunch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 -a 0000:00:04.0 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=3 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.0]
       testpmd> set fwd mac
       testpmd> start

13. Rerun steps 3-6.

14. Quit all testpmd and relaunch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 -a 0000:00:04.0 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.0,lcore14@0000:00:04.0,lcore15@0000:00:04.0,lcore16@0000:00:04.0,lcore17@0000:00:04.0,lcore18@0000:00:04.0]
       testpmd> set fwd mac
       testpmd> start

15. Rerun steps 7.

16. Quit all testpmd and relaunch vhost with iova=pa by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 -a 0000:00:04.0 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=pa -- -i --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.0,lcore14@0000:00:04.0,lcore15@0000:00:04.0,lcore16@0000:00:04.0,lcore17@0000:00:04.0,lcore18@0000:00:04.0]
       testpmd> set fwd mac
       testpmd> start

17. Rerun steps 8.

Test Case 10: PVP packed ring all path vhost enqueue operations with 1 to N mapping between vrings and CBDMA virtual channels
-----------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of packed ring in each virtio path when vhost uses
the asynchronous enqueue operations and the mapping between vrings and CBDMA virtual channels is 1:N.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 8 CBDMA devices to vfio-pci, as common step 1.

2. Launch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=1,dmas=[txq0],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

3. Launch virtio-user with inorder mergeable path::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=1,packed_vq=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and check the throughput can get expected data::

       testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

       testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throught can get expected data::

       testpmd> start
       testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=0,queues=1,packed_vq=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,queues=1,packed_vq=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,queues=1,packed_vq=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queues=1 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

11. Relaunch virtio-user with vectorized path and ring size is not power of 2, then repeat step 3::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queues=1,queue_size=1025 \
       -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1025 --rxd=1025
       testpmd> set fwd mac
       testpmd> start

12. Quit all testpmd and relaunch vhost with iova=pa by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=1,dmas=[txq0],dma_ring_size=2048' \
       --iova=pa -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

13. Rerun steps 9.

Test Case 11: PVP packed ring all path multi-queues vhost enqueue operations with M to N mapping between vrings and CBDMA virtual channels
------------------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of packed ring in each virtio path with multi-queues
when vhost uses the asynchronous enqueue operations and the mapping between vrings and CBDMA virtual channels is M:N.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 8 CBDMA devices to vfio-pci, as common step 1.

2. Launch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

3. Launch virtio-user with inorder mergeable path::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and check the throughput can get expected data::

       testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

       testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throught can get expected data::

       testpmd> start
       testpmd> show port stats all

7. Relaunch virtio-user with mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=0,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

8. Relaunch virtio-user with inorder non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=1,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

9. Relaunch virtio-user with non-mergeable path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,queues=8,packed_vq=1 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

10. Relaunch virtio-user with vectorized path, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=8, \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

11. Relaunch virtio-user with vectorized path and ring size is not power of 2, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=0,in_order=0,packed_vq=1,vectorized=1,queues=8,queue_size=1025 \
       -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1025 --rxd=1025
       testpmd> set fwd mac
       testpmd> start

12. Quit all testpmd and relaunch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=va -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

13. Rerun steps 7.

14. Quit all testpmd and relaunch vhost with iova=pa by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7],dma_ring_size=2048' \
       --iova=pa -- -i --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.1,lcore11@0000:00:04.2,lcore11@0000:00:04.3,lcore11@0000:00:04.4,lcore11@0000:00:04.5,lcore11@0000:00:04.6,lcore11@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

15. Rerun steps 9.

Test Case 12: PVP packed ring dynamic queue number vhost enqueue operations with M to N mapping between vrings and CBDMA virtual channels
-----------------------------------------------------------------------------------------------------------------------------------------
This case uses testpmd and Traffic Generator(For example, Trex) to test performance of packed ring when vhost uses the asynchronous enqueue operations
and if the vhost-user can work well when the queue number dynamic change. Both iova as VA and PA mode have been tested.
Both iova as VA and PA mode have been tested.

1. Bind 1 NIC port and 8 CBDMA devices to vfio-pci, as common step 1.

2. Launch vhost by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost -a 0000:18:00.0 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,client=1' \
        --iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

3. Launch virtio-user by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-3 --no-pci --file-prefix=virtio \
       --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost_net0,mrg_rxbuf=1,in_order=1,queues=1,server=1,packed_vq=1 \
       -- -i  --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024
       testpmd> set fwd mac
       testpmd> start

4. Send imix packets [64,1518] from packet generator as common step2, and check the throughput can get expected data::

       testpmd> show port stats all

5. Stop vhost port, check that there are packets in both directions of RX and TX in each queue from vhost log::

       testpmd> stop

6. Restart vhost port and send imix pkts again, then check the throught can get expected data::

       testpmd> start
       testpmd> show port stats all

7. Quit and relaunch vhost with 1:1 mapping between vrings and CBDMA virtual channels, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18  --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 \
        --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3]' \
       --iova=va -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.3]
       testpmd> set fwd mac
       testpmd> start

9. Quit and relaunch vhost with M:N(1:N;M<N) mapping between vrings and CBDMA virtual channels, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 -a 0000:00:04.3 -a 0000:00:04.4 -a 0000:00:04.5 -a 0000:00:04.6 -a 0000:00:04.7 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq6;txq7]' \
       --iova=va -- -i --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore11@0000:00:04.7,lcore12@0000:00:04.1,lcore12@0000:00:04.2,lcore12@0000:00:04.3,lcore13@0000:00:04.2,lcore13@0000:00:04.3,lcore13@0000:00:04.4,lcore14@0000:00:04.2,lcore14@0000:00:04.3,lcore14@0000:00:04.4,lcore14@0000:00:04.5,lcore15@0000:00:04.0,lcore15@0000:00:04.1,lcore15@0000:00:04.2,lcore15@0000:00:04.3,lcore15@0000:00:04.4,lcore15@0000:00:04.5,lcore15@0000:00:04.6,lcore15@0000:00:04.7]
       testpmd> set fwd mac
       testpmd> start

11. Quit and relaunch vhost with diff M:N(M:1;M>N) mapping between vrings and CBDMA virtual channels, then repeat step 4-6::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]' \
       --iova=va -- -i --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.1,lcore14@0000:00:04.2,lcore15@0000:00:04.1,lcore15@0000:00:04.2]
       testpmd> set fwd mac
       testpmd> start

13. Quit and relaunch vhost with iova=pa by below command::

       <dpdk dir># ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 10-18 --file-prefix=vhost \
       -a 0000:18:00.0 -a 0000:00:04.0 -a 0000:00:04.1 -a 0000:00:04.2 \
       --vdev 'net_vhost0,iface=/tmp/vhost_net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6;txq7]' \
       --iova=pa -- -i --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 \
       --lcore-dma=[lcore11@0000:00:04.0,lcore12@0000:00:04.0,lcore13@0000:00:04.1,lcore13@0000:00:04.2,lcore14@0000:00:04.1,lcore14@0000:00:04.2,lcore15@0000:00:04.1,lcore15@0000:00:04.2]
       testpmd> set fwd mac
       testpmd> start

14. Rerun step 4-6.
