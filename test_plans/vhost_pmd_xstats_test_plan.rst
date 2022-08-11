.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

============================
vhost PMD Xstats test plan
============================

Description
===========

This test plan will cover the basic vhost pmd xstats test with with 10 tx/rx paths. Includes mergeable, non-mergeable, vectorized_rx,
inorder mergeable, inorder non-mergeable, virtio 1.1 mergeable, virtio 1.1 non-mergeable，virtio 1.1 inorder
mergeable, virtio 1.1 inorder non-mergeable, virtio1.1 vectorized path, also cover stability cases. 
From DPDK 22.07, vhost support per-virtqueue statistics, Per-virtqueue statistics collection will be enabled when the flag "RTE_VHOST_USER_NET_STATS_ENABLE" is set. It is disabled by default.
Note IXIA or Scapy packes includes 4 CRC bytes and vhost side will remove the CRC when receive packests.

Prerequisites
=============

Topology
---------

        Test flow:Traffic Generator --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> Traffic Generator

Hardware
--------
        Supportted NICs: ALL

Software
--------

        Scapy: http://www.secdev.org/projects/scapy/

General set up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110
    For example：
    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

2. Get the PCI device ID of DUT, for example, 0000:18:00.0 is PCI device ID::

    <dpdk dir># ./usertools/dpdk-devbind.py -s

    Network devices using kernel driver
    ===================================
    0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci

Test case
=========

Common steps
------------

1. Bind 1 NIC port to vfio-pci::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>
    For example::
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:00:18.0

2. Check the statistic type and number in each queue is correct.
   For example: send 1000 packets with 1028B size(includes 4 CRC bytes) with different destination IP to two queues, the total statistic number of tx_q0_size_1024_to_1518_packets and tx_q1_size_1024_to_1518_packets should be 1000, the statistics about the rx direction is the same.
   Send 1000 packets with ucast type with different destination IP to two queues, the total number of tx_q0_unicast_packets and tx_q1_unicast_packets should both be 1000, the statistics about the rx direction is the same.


Test Case 1: Vhost pmd xstats stability test with split ring inorder mergeable path
-----------------------------------------------------------------------------------
This case use Scapy or other traffic generator to send packets of different types and packet sizes with different destination IP addresses to test vhost pmd xstats stability when using split ring inorder mergeable path.

1. Bind one port to vfio-pci like common step 1, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=1,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

3. Let Traffic Generator generate and send 10000 packets for each packet sizes(64, 128, 255, 512, 1024, 1523) with different destination IP.

4. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

5. Let Traffic Generator generate and send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

Test Case 2: Vhost pmd xstats test with split ring inorder non-mergeable path
-----------------------------------------------------------------------------
This case use Scapy or other traffic generator to send packets of different types and packet sizes with different destination IP addresses to test vhost pmd xstats when using split ring inorder non-mergeable path.

1. Bind one port to vfio-pci like common step 1, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=1,mrg_rxbuf=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

3. Let Traffic Generator generate and send 10000 packets for each packet sizes(64, 128, 255, 512, 1024, 1523) with different destination IP.

4. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

5. Let Traffic Generator generate and send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

Test Case 3: Vhost pmd xstats test with split ring mergeable path
-----------------------------------------------------------------
This case use Scapy or other traffic generator to send packets of different types and packet sizes with different destination IP addresses to test vhost pmd xstats when using split ring mergeable path.

1. Bind one port to vfio-pci like common step 1, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=0,mrg_rxbuf=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

3. Let Traffic Generator generate and send 10000 packets for each packet sizes(64, 128, 255, 512, 1024, 1523) with different destination IP.

4. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

5. Let Traffic Generator generate and send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

Test Case 4: Vhost pmd xstats test with split ring non-mergeable path
---------------------------------------------------------------------
This case use Scapy or other traffic generator to send packets of different types and packet sizes with different destination IP addresses to test vhost pmd xstats when using split ring non-mergeable path.

1. Bind one port to vfio-pci like common step 1, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

3. Let Traffic Generator generate and send 10000 packets for each packet sizes(64, 128, 255, 512, 1024, 1523) with different destination IP.

4. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

5. Let Traffic Generator generate and send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

Test Case 5: Vhost pmd xstats test with split ring vector_rx path
-----------------------------------------------------------------
This case use Scapy or other traffic generator to send packets of different types and packet sizes with different destination IP addresses to test vhost pmd xstats when using split ring vector_rx path.

1. Bind one port to vfio-pci like common step 1, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,in_order=0,mrg_rxbuf=0,vectorized=1 \
    -- -i --tx-offloads=0x0 --rss-ip --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

3. Let Traffic Generator generate and send 10000 packets for each packet sizes(64, 128, 255, 512, 1024, 1523) with different destination IP.

4. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

5. Let Traffic Generator generate and send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

Test Case 6: Vhost pmd xstats test with packed ring inorder mergeable path
--------------------------------------------------------------------------
This case use Scapy or other traffic generator to send packets of different types and packet sizes with different destination IP addresses to test vhost pmd xstats when using packed ring inorder mergeable path.

1. Bind one port to vfio-pci like common step 1, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

3. Let Traffic Generator generate and send 10000 packets for each packet sizes(64, 128, 255, 512, 1024, 1523) with different destination IP.

4. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

5. Let Traffic Generator generate and send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

Test Case 7: Vhost pmd xstats test with packed ring inorder non-mergeable path
------------------------------------------------------------------------------
This case use Scapy or other traffic generator to send packets of different types and packet sizes with different destination IP addresses to test vhost pmd xstats when using packed ring inorder non-mergeable path.

1. Bind one port to vfio-pci like common step 1, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --rx-offloads=0x10 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

3. Let Traffic Generator generate and send 10000 packets for each packet sizes(64, 128, 255, 512, 1024, 1523) with different destination IP.

4. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

5. Let Traffic Generator generate and send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

Test Case 8: Vhost pmd xstats test with packed ring mergeable path
------------------------------------------------------------------
This case use Scapy or other traffic generator to send packets of different types and packet sizes with different destination IP addresses to test vhost pmd xstats when using packed ring mergeable path.

1. Bind one port to vfio-pci like common step 1, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

3. Let Traffic Generator send 10000 packets for each packet sizes(64, 128, 255, 512, 1024, 1523) with different destination IP.

4. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

5. Let Traffic Generator generate and send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

7.Send packets for 10 minutes with low speed, check the statistic type and number is correct like common step 2.

Test Case 9: Vhost pmd xstats test with packed ring non-mergeable path
----------------------------------------------------------------------
This case use Scapy or other traffic generator to send packets of different types and packet sizes with different destination IP addresses to test vhost pmd xstats when using packed ring non-mergeable path.

1. Bind one port to vfio-pci like common step 1, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

3. Let Traffic Generator generate and send 10000 packets for each packet sizes(64, 128, 255, 512, 1024, 1523) with different destination IP.

4. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

5. Let Traffic Generator generate and send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.


Test Case 10: Vhost pmd xstats test with packed ring vectorized path
--------------------------------------------------------------------
This case use Scapy or other traffic generator to send packets of different types and packet sizes with different destination IP addresses to test vhost pmd xstats when using packed ring vectorized path.

1. Bind one port to vfio-pci like common step 1, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --rss-ip --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

3. Let Traffic Generator generate and send 10000 packets for each packet sizes(64, 128, 255, 512, 1024, 1523) with different destination IP.

4. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

5. Let Traffic Generator generate and send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

Test Case 11: Vhost pmd xstats test with packed ring vectorized path with ring size is not power of 2
-----------------------------------------------------------------------------------------------------
This case use Scapy or other traffic generator to send packets of different types and packet sizes with different destination IP addresses to test vhost pmd xstats when using packed ring vectorized path with ring size is not power of 2.

1. Bind one port to vfio-pci like common step 1, then launch vhost by below command::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 2-4  \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    testpmd>set fwd io
    testpmd>start

2. Launch virtio-user by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=255 \
    -- -i --rss-ip --nb-cores=2 --rxq=2 --txq=2 --txd=255 --rxd=255
    testpmd>set fwd io
    testpmd>start

3. Let Traffic Generator generate and send 10000 packets for each packet sizes(64, 128, 255, 512, 1024, 1523) with different destination IP.

4. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.

5. Let Traffic Generator generate and send 10000 packets for each different types (broadcast, multicast, ucast).

6. On host run "show port xstats 1", and check the statistic type and number is correct like common step 2.
