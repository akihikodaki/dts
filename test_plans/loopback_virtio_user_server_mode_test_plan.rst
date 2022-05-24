.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

================================================
vhost/virtio-user loopback server mode test plan
================================================

Virtio-user server mode is a feature to enable virtio-user as the server, vhost as the client, thus after vhost-user is killed then relaunched,
virtio-user can reconnect back to vhost-user again; at another hand, virtio-user also can reconnect back to vhost-user after virtio-user is killed.
This feature test need cover different rx/tx paths with virtio 1.0 and virtio 1.1, includes split ring mergeable, non-mergeable, inorder mergeable,
inorder non-mergeable, vector_rx path and packed ring mergeable, non-mergeable, inorder non-mergeable, inorder mergeable, vectorized path.

Test Case 1: Basic test for packed ring server mode
===================================================

1. Launch virtio-user as server mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=1,packed_vq=1 -- -i --rxq=1 --txq=1 --no-numa
    >set fwd mac
    >start

2. Launch vhost as client mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/sock0,client=1,queues=1' -- -i --rxq=1 --txq=1 --nb-cores=1
    >set fwd mac
    >start tx_first 32

3. Run below command to get throughput,verify the loopback throughput is not zero::

    testpmd>show port stats all

Test Case 2:  Basic test for split ring server mode
===================================================

1. Launch virtio-user as server mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=1 -- -i --rxq=1 --txq=1 --no-numa
    >set fwd mac
    >start

2. Launch vhost as client mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-4 -n 4 --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/sock0,client=1,queues=1' -- -i --rxq=1 --txq=1 --nb-cores=1
    >set fwd mac
    >start tx_first 32

3. Run below command to get throughput,verify the loopback throughput is not zero::

    testpmd>show port stats all

Test Case 3: loopback reconnect test with split ring mergeable path and server mode
===================================================================================

1. launch vhost as client mode with 8 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=8' -- -i --nb-cores=2 --rxq=8 --txq=8
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 8 queues and check throughput can get expected::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=8,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=8 --txq=8
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32
    >show port stats all

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send chain packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=8' -- -i --nb-cores=2 --rxq=8 --txq=8
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=8,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=8 --txq=8
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and check throughput can get expected::

      testpmd>stop
      testpmd>port stop 0
      testpmd>port start 0
      testpmd>set txpkts 2000,2000,2000,2000
      testpmd>start tx_first 32
      testpmd>show port stats all

11. Check each RX/TX queue has packets::

      testpmd>stop

Test Case 4: loopback reconnect test with split ring inorder mergeable path and server mode
===========================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues, check throughput can get expected::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32
    >show port stats all

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=1,in_order=1\
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and check throughput can get expected::

      testpmd>stop
      testpmd>port stop 0
      testpmd>port start 0
      testpmd>set txpkts 2000,2000,2000,2000
      testpmd>start tx_first 32
      testpmd>show port stats all

11. Check each RX/TX queue has packets::

      testpmd>stop

Test Case 5: loopback reconnect test with split ring inorder non-mergeable path and server mode
===============================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues check throughput can get expected::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32
    >show port stats all

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and check throughput can get expected::

      testpmd>stop
      testpmd>port stop 0
      testpmd>port start 0
      testpmd>start tx_first 32
      testpmd>show port stats all

11. Check each RX/TX queue has packets::

      testpmd>stop

Test Case 6: loopback reconnect test with split ring non-mergeable path and server mode
=======================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues and check throughput can get expected::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=0,vectorized=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32
    >show port stats all

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=0,vectorized=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and check throughput can get expected::

      testpmd>stop
      testpmd>port stop 0
      testpmd>port start 0
      testpmd>start tx_first 32
      testpmd>show port stats all

11. Check each RX/TX queue has packets::

      testpmd>stop

Test Case 7: loopback reconnect test with split ring vector_rx path and server mode
===================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues and check throughput can get expected::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=0,vectorized=1 \
    -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32
    >show port stats all

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=0,vectorized=1 \
    -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and check throughput can get expected::

      testpmd>stop
      testpmd>port stop 0
      testpmd>port start 0
      testpmd>start tx_first 32
      testpmd>show port stats all

11. Check each RX/TX queue has packets::

      testpmd>stop

Test Case 8: loopback reconnect test with packed ring mergeable path and server mode
====================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues and check throughput can get expected::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32
    >show port stats all

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and check throughput can get expected::

     testpmd>stop
     testpmd>port stop 0
     testpmd>port start 0
     testpmd>set txpkts 2000,2000,2000,2000
     testpmd>start tx_first 32
     testpmd>show port stats all

11. Check each RX/TX queue has packets::

     testpmd>stop

Test Case 9: loopback reconnect test with packed ring non-mergeable path and server mode
========================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues and check throughput can get expected::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32
    >show port stats all

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and check throughput can get expected::

     testpmd>stop
     testpmd>port stop 0
     testpmd>port start 0
     testpmd>start tx_first 32
     testpmd>show port stats all

11. Check each RX/TX queue has packets::

     testpmd>stop

Test Case 10: loopback reconnect test with packed ring inorder mergeable path and server mode
=============================================================================================

1. launch vhost as client mode with 8 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=8' -- -i --nb-cores=2 --rxq=8 --txq=8
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 8 queues and check throughput can get expected::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=8,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=8 --txq=8
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32
    >show port stats all

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=8' -- -i --nb-cores=2 --rxq=8 --txq=8
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=8,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=8 --txq=8
    >set fwd mac
    >set txpkts 2000,2000,2000,2000
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and check throughput can get expected::

     testpmd>stop
     testpmd>port stop 0
     testpmd>port start 0
     testpmd>set txpkts 2000,2000,2000,2000
     testpmd>start tx_first 32
     testpmd>show port stats all

11. Check each RX/TX queue has packets::

     testpmd>stop

Test Case 11: loopback reconnect test with packed ring inorder non-mergeable path and server mode
=================================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues and check throughput can get expected::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --rx-offloads=0x10 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32
    >show port stats all

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --rx-offloads=0x10 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and check throughput can get expected::

     testpmd>stop
     testpmd>port stop 0
     testpmd>port start 0
     testpmd>start tx_first 32
     testpmd>show port stats all

11. Check each RX/TX queue has packets::

     testpmd>stop

Test Case 12: loopback reconnect test with packed ring vectorized path and server mode
=======================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --log-level=pmd.net.vhost.driver,8 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues and check throughput can get expected::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --log-level=pmd.net.virtio.driver,8 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32
    >show port stats all

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xe -n 4 --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-7 --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, check throughput can get expected::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and check throughput can get expected::

     testpmd>stop
     testpmd>port stop 0
     testpmd>port start 0
     testpmd>start tx_first 32
     testpmd>show port stats all

11. Check each RX/TX queue has packets::

     testpmd>stop

Test Case 13: loopback packed ring all path payload check test using server mode and multi-queues
=================================================================================================

1. launch vhost::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 32-33 --no-pci --file-prefix=vhost -n 4 --vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1' -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024

2. Launch virtio-user with packed ring mergeable inorder path::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio --no-pci --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1 -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
     testpmd> set fwd csum
     testpmd> start

3. Attach pdump secondary process to primary process by same file-prefix::

   ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio -- --pdump 'device_id=net_virtio_user0,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Send large pkts from vhost::

    testpmd> set fwd csum
    testpmd> set txpkts 2000,2000,2000,2000
    testpmd> set burst 1
    testpmd> start tx_first 1
    testpmd> stop

5. Quit pdump, check all the packets length are 8000 Byte in the pcap file, and the payload in receive packets are same.

6. Quit and relaunch vhost and rerun step 3-5.

7. Quit and relaunch virtio with packed ring mergeable path as below::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1 -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
     testpmd> set fwd csum
     testpmd> start

8. Rerun step 3-6.

9. Quit and relaunch virtio with packed ring non-mergeable path as below::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1 -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
    testpmd> set fwd csum
    testpmd> start

10. Rerun step 3.

11. Send pkts from vhost::

     testpmd> set fwd csum
     testpmd> set txpkts 64,128,256,512
     testpmd> set burst 1
     testpmd> start tx_first 1
     testpmd> stop

12. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

13. Quit and relaunch vhost and rerun step 10-12.

14. Quit and relaunch virtio with packed ring inorder non-mergeable path as below::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
     --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1 -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
     testpmd> set fwd csum
     testpmd> start

15. Rerun step 10-13.

16. Quit and relaunch virtio with packed ring vectorized path as below::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
     --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,vectorized=1,packed_vq=1,server=1 -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
     testpmd> set fwd csum
     testpmd> start

17 Rerun step 10-13.

18. Quit and relaunch virtio with packed ring vectorized path and ring size is not power of 2 as below::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci --force-max-simd-bitwidth=512 \
     --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,vectorized=1,packed_vq=1,queue_size=1025,server=1 \
     -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1025 --rxd=1025
     testpmd> set fwd csum
     testpmd> start

19. Rerun step 10-13.

Test Case 14: loopback split ring all path payload check test using server mode and multi-queues
================================================================================================

1. Launch vhost::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 32-33 --no-pci --file-prefix=vhost -n 4 --vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1' -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024

2. Launch virtio-user with split ring mergeable inorder path::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1 \
    -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
     testpmd>set fwd csum
     testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

   ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio-user0 -- --pdump 'device_id=net_virtio_user0,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Send large pkts from vhost::

    testpmd> set fwd csum
    testpmd> set txpkts 2000,2000,2000,2000
    testpmd> set burst 1
    testpmd> start tx_first 1
    testpmd> stop

5. Quit pdump, check all the packets length are 8000 Byte in the pcap file and the payload in receive packets are same.

6. Quit and relaunch vhost and rerun step3-5.

7. Quit and relaunch virtio with split ring mergeable path as below::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1 \
    -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
     testpmd>set fwd csum
     testpmd>start

8. Rerun steps 3-6.

9. Quit and relaunch virtio with split ring non-mergeable path as below::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,server=1 \
    -- -i --enable-hw-vlan-strip --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
     testpmd>set fwd csum
     testpmd>start

10. Rerun step 3.

11. Send pkts from vhost::

     testpmd> set fwd csum
     testpmd> set txpkts 64,128,256,512
     testpmd> set burst 1
     testpmd> start tx_first 1
     testpmd> stop

12. Quit pdump, check all the packets length are 960 Byte in the pcap file and the payload in receive packets are same.

13. Quit and relaunch vhost and rerun step 10-12.

14. Quit and relaunch virtio with split ring inorder non-mergeable path as below::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
     --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1 \
     -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
     testpmd>set fwd csum
     testpmd>start

15. Rerun step 10-13.

16. Quit and relaunch virtio with split ring vectorized path as below::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 30,31 -n 4 --file-prefix=virtio-user0 --no-pci \
     --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,server=1 \
     -- -i --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024
     testpmd>set fwd csum
     testpmd>start

17. Rerun step 10-13.
