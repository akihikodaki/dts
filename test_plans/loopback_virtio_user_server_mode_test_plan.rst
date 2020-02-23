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
   (INCLUDING, BUT NOgit T LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.

================================================
vhost/virtio-user loopback server mode test plan
================================================

Virtio-user server mode is a feature to enable virtio-user as the server, vhost as the client, thus after vhost-user is killed then relaunched,
virtio-user can reconnect back to vhost-user again; at another hand, virtio-user also can reconnect back to vhost-user after virtio-user is killed.
This feature test need cover different rx/tx paths with virtio 1.0 and virtio 1.1, includes split ring mergeable, non-mergeable, inorder mergeable,
inorder non-mergeable, vector_rx path and packed ring mergeable, non-mergeable, inorder non-mergeable, inorder mergeable path.

Test Case 1: Basic test for packed ring server mode
===================================================

1. Launch virtio-user as server mode::

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=1,packed_vq=1 -- -i --rxq=1 --txq=1 --no-numa
    >set fwd mac
    >start

2. Launch vhost as client mode::

    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/sock0,client=1,queues=1' -- -i --rxq=1 --txq=1 --nb-cores=1
    >set fwd mac
    >start tx_first 32

3. Run below command to get throughput,verify the loopback throughput is not zero::

    testpmd>show port stats all

Test Case 2:  Basic test for split ring server mode
===================================================

1. Launch virtio-user as server mode::

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=/tmp/sock0,server=1,queues=1 -- -i --rxq=1 --txq=1 --no-numa
    >set fwd mac
    >start

2. Launch vhost as client mode::

    ./testpmd -l 3-4 -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'net_vhost0,iface=/tmp/sock0,client=1,queues=1' -- -i --rxq=1 --txq=1 --nb-cores=1
    >set fwd mac
    >start tx_first 32

3. Run below command to get throughput,verify the loopback throughput is not zero::

    testpmd>show port stats all

Test Case 3: loopback reconnect test with split ring mergeable path and server mode
===================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput,verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and re-calculate the average throughput::

      testpmd>stop
      testpmd>port stop 0
      testpmd>port start 0
      testpmd>start tx_first 32
      testpmd>show port stats all

11. Check each RX/TX queue has packets::

      testpmd>stop

Test Case 4: loopback reconnect test with split ring inorder mergeable path and server mode
===========================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput,verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=1,in_order=1\
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and re-calculate the average throughput::

      testpmd>stop
      testpmd>port stop 0
      testpmd>port start 0
      testpmd>start tx_first 32
      testpmd>show port stats all

11. Check each RX/TX queue has packets::

      testpmd>stop

Test Case 5: loopback reconnect test with split ring inorder non-mergeable path and server mode
===============================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput,verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and re-calculate the average throughput::

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
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput,verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and re-calculate the average throughput::

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
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput,verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and re-calculate the average throughput::

      testpmd>stop
      testpmd>port stop 0
      testpmd>port start 0
      testpmd>start tx_first 32
      testpmd>show port stats all

11. Check each RX/TX queue has packets::

      testpmd>stop

Test Case 8: loopback reconnect test with packed ring mergeable path and server mode
===================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput,verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and re-calculate the average throughput::

    testpmd>stop
    testpmd>port stop 0
    testpmd>port start 0
    testpmd>start tx_first 32
    testpmd>show port stats all

11. Check each RX/TX queue has packets::

    testpmd>stop

Test Case 9: loopback reconnect test with packed ring non-mergeable path and server mode
=======================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput,verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and re-calculate the average throughput::

    testpmd>stop
    testpmd>port stop 0
    testpmd>port start 0
    testpmd>start tx_first 32
    testpmd>show port stats all

11. Check each RX/TX queue has packets::

    testpmd>stop

Test Case 10: loopback reconnect test with packed ring inorder mergeable path and server mode
===========================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput,verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and re-calculate the average throughput::

    testpmd>stop
    testpmd>port stop 0
    testpmd>port start 0
    testpmd>start tx_first 32
    testpmd>show port stats all

11. Check each RX/TX queue has packets::

    testpmd>stop

Test Case 11: loopback reconnect test with packed ring inorder non-mergeable path and server mode
===============================================================================================

1. launch vhost as client mode with 2 queues::

    rm -rf vhost-net*
    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start

2. Launch virtio-user as server mode with 2 queues::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

3. Quit vhost side testpmd, check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

4. Relaunch vhost and send packets::

    ./testpmd -c 0xe -n 4 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=vhost \
    --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=2' -- -i --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

5. Check the virtio-user side link status and run below command to get throughput,verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

6. Check each RX/TX queue has packets::

    testpmd>stop

7. Quit virtio-user side testpmd, check the vhost side link status::

    testpmd> show port info 0
    #it should show "down"

8. Relaunch virtio-user and send packets::

    ./testpmd -n 4 -l 5-7 --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,server=1,queues=2,packed_vq=1,mrg_rxbuf=0,in_order=1 \
    -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=2 --txq=2
    >set fwd mac
    >start tx_first 32

9. Check the vhost side link status and run below command to get throughput, verify the loopback throughput is not zero::

    testpmd> show port info 0
    #it should show up"
    testpmd>show port stats all

10. Port restart at vhost side by below command and re-calculate the average throughput::

    testpmd>stop
    testpmd>port stop 0
    testpmd>port start 0
    testpmd>start tx_first 32
    testpmd>show port stats all

11. Check each RX/TX queue has packets::

    testpmd>stop