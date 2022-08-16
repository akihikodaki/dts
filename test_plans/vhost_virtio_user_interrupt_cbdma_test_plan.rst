.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=====================================================
vhost/virtio-user interrupt mode with cbdma test plan
=====================================================

Description
===========

Virtio-user interrupt need test with l3fwd-power sample, small packets send from traffic generator
to virtio side, check virtio-user cores can be wakeup status, and virtio-user cores should be sleep
status after stop sending packets from traffic generator.
This test plan tests virtio-user Rx interrupt and LSC interrupt with vhost-user as the backend when cbdma enable.

..Note:

DPDK local patch that about vhost pmd is needed when testing Vhost asynchronous data path with testpmd.

Prerequisites
=============

Software
--------
    Trex:http://trex-tgn.cisco.com/trex/release/v2.26.tar.gz

General set up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110
    For example:
    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

2. Get the PCI device ID and DMA device ID of DUT, for example, 0000:18:00.0 is PCI device ID, 0000:00:04.0, 0000:00:04.1 is DMA device ID::

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

Test Case1: Split ring LSC event between vhost-user and virtio-user with cbdma enable
-------------------------------------------------------------------------------------
This case tests the LSC interrupt of split ring virtio-user with vhost-user as the back-end
when vhost uses the asynchronous operations with CBDMA channels.
Flow: Vhost <--> Virtio

1. Bind 1 CBDMA channel to vfio-pci driver, then start vhost-user side::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3000 -n 4 -a 00:04.0 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0,dmas=[txq0;rxq0]' \
    -- -i --lcore-dma=[lcore13@0000:00:04.0]
    testpmd> set fwd mac
    testpmd> start

2. Start virtio-user side::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc000 -n 4 --no-pci --file-prefix=virtio --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net -- -i --tx-offloads=0x00
    testpmd> set fwd mac
    testpmd> start

3. Check the virtio-user side link status::

    testpmd>  show port info 0
    #it should show "up"

4. Quit the vhost-user side with testpmd, then check the virtio-user side link status::

    testpmd>  show port info 0
    #it should show "down"

Test Case2: Split ring virtio-user interrupt test with vhost-user as backend and cbdma enable
---------------------------------------------------------------------------------------------
This case tests Rx interrupt of split ring virtio-user with vhost-user as the back-end when vhost uses the asynchronous operations with CBDMA channels.
Flow: TG --> NIC --> Vhost --> Virtio

1. Bind 1 CBDMA channel and 1 NIC port to vfio-pci, launch testpmd with a virtual vhost device as backend::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7c -n 4 --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0;rxq0]' \
    -- -i  --rxq=1 --txq=1 --lcore-dma=[lcore3@0000:00:04.0,lcore3@0000:00:04.1]
    testpmd> start

2. Start l3fwd-power with a virtio-user device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -c 0xc000 -n 4 --log-level='user1,7' --no-pci --file-prefix=l3fwd-pwd \
    --vdev=virtio_user0,path=./vhost-net -- -p 1 --config="(0,0,14)" --parse-ptype --interrupt-only

3. Send packets with packet generator, check the virtio-user related core can be wakeup status.

4. Stop sending packets with packet generator, check virtio-user related core change to sleep status.

5. Restart sending packets with packet generator, check virtio-user related core change to wakeup status again.

Test Case3: Packed ring LSC event between vhost-user and virtio-user with cbdma enable
--------------------------------------------------------------------------------------
This case tests the LSC interrupt of packed ring virtio-user with vhost-user as the back-end
when vhost uses the asynchronous operations with CBDMA channels.
Flow: Vhost <--> Virtio

1. Bind one cbdma port to vfio-pci driver, then start vhost-user side::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3000 -n 4 -a 00:04.0 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0,dmas=[txq0;rxq0]' \
    -- -i --lcore-dma=[lcore13@0000:00:04.0,lcore13@0000:00:04.1]
    testpmd> set fwd mac
    testpmd> start

2. Start virtio-user side::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc000 -n 4 --no-pci --file-prefix=virtio --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1 -- -i --tx-offloads=0x00
    testpmd> set fwd mac
    testpmd> start

3. Check the virtio-user side link status::

    testpmd>  show port info 0
    #it should show "up"

4. Quit the vhost-user side with testpmd, then check the virtio-user side link status::

    testpmd>  show port info 0
    #it should show "down"

Test Case4: Packed ring virtio-user interrupt test with vhost-user as backend and cbdma enable
----------------------------------------------------------------------------------------------
This case tests Rx interrupt of packed ring virtio-user with vhost-user as the back-end when vhost uses the asynchronous operations with CBDMA channels.

flow: TG --> NIC --> Vhost --> Virtio

1. Bind one cbdma port and one NIC port to vfio-pci, launch testpmd with a virtual vhost device as backend::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7c -n 4 --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0;rxq0]' \
    -- -i  --rxq=1 --txq=1 --lcore-dma=[lcore3@0000:00:04.0]
    testpmd> start

2. Start l3fwd-power with a virtio-user device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -c 0xc000 -n 4 --log-level='user1,7' --no-pci --file-prefix=l3fwd-pwd \
    --vdev=virtio_user0,path=./vhost-net,packed_vq=1 -- -p 1 --config="(0,0,14)" --parse-ptype --interrupt-only

3. Send packets with packet generator, check the virtio-user related core can be wakeup status.

4. Stop sending packets with packet generator, check virtio-user related core change to sleep status.

5. Restart sending packets with packet generator, check virtio-user related core change to wakeup status again.

