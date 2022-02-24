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

======================================
vm2vm vhost-user/virtio-user test plan
======================================

Description
===========

This test plan test several features in VM2VM topo:
1. Split virtqueue vm2vm in-order mergeable, in-order non-mergeable, mergeable, non-mergeable, vector_rx path test.
2. Packed virtqueue vm2vm in-order mergeable, in-order non-mergeable, mergeable, non-mergeable, vectorized path (ringsize not powerof 2) test.
3. Split ring and packed ring vm2vm test when vhost enqueue operation with multi-CBDMA channels.
4. Test indirect descriptor feature. For example, the split ring mergeable inorder path use non-indirect descriptor, the 2000,2000,2000,2000 chain packets will need 4 consequent ring, still need one ring put header.
the split ring mergeable path use indirect descriptor, the 2000,2000,2000,2000 chain packets will only occupy one ring.

Test flow
=========
Virtio-user <-> Vhost-user <-> Testpmd <-> Vhost-user <-> Virtio-user

Test Case 1: packed virtqueue vm2vm mergeable path test
=======================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

5. Start vhost, then send 8k length packets by virtio-user0 again::

    testpmd>stop
    testpmd>set txpkts 2000
    testpmd>start tx_first 1

6. Quit pdump and three testpmd, get 288 packets received by virtio-user1 in pdump-virtio-rx.pcap.

7. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

9. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 5
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 2000
    testpmd>start tx_first 1

10. Quit pdump,vhost received packets in pdump-vhost-rx.pcap, check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 2: packed virtqueue vm2vm inorder mergeable path test
===============================================================

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

5. Start vhost, then quit pdump and three testpmd, get 256 packets received by virtio-user1 in pdump-virtio-rx.pcap.

6. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 5
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap, check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 3: packed virtqueue vm2vm non-mergeable path test
===========================================================

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

5. Start vhost, then quit pdump and three testpmd, get 251 packets received by virtio-user1 in pdump-virtio-rx.pcap.

6. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap, check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 4: packed virtqueue vm2vm inorder non-mergeable path test
===================================================================

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1 \
    -- -i --rx-offloads=0x10 --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,packed_vec=1 \
    -- -i --rx-offloads=0x10 --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

5. Start vhost, then quit pdump and three testpmd, get 251 packets received by virtio-user1 in pdump-virtio-rx.pcap.

6. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,packed_vec=1 \
    -- -i --rx-offloads=0x10 --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap,check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 5: split virtqueue vm2vm mergeable path test
======================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=0,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

5. Start vhost, then send 8k length packets by virtio-user0 again::

    testpmd>stop
    testpmd>set txpkts 2000
    testpmd>start tx_first 1

6. Quit pdump and three testpmd, get 288 packets received by virtio-user1 in pdump-virtio-rx.pcap.

7. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

9. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 5
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 2000
    testpmd>start tx_first 1

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap, check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 6: split virtqueue vm2vm inorder mergeable path test
==============================================================

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=0,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

5. Start vhost, then quit pdump and three testpmd, get 252 packets received by virtio-user1 in pdump-virtio-rx.pcap.

6. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap,check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 7: split virtqueue vm2vm non-mergeable path test
==========================================================

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256 --enable-hw-vlan-strip

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256 --enable-hw-vlan-strip
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

5. Start vhost, then quit pdump and three testpmd, get 251 packets received by virtio-user1 in pdump-virtio-rx.pcap.

6. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256 --enable-hw-vlan-strip
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap,check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 8: split virtqueue vm2vm inorder non-mergeable path test
==================================================================

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

5. Start vhost, then quit pdump and three testpmd, get 251 packets received by virtio-user1 in pdump-virtio-rx.pcap.

6. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap,check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 9: split virtqueue vm2vm vector_rx path test
======================================================

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --txd=256 --rxd=256

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

5. Start vhost, then quit pdump and three testpmd, get 251 packets received by virtio-user1 in pdump-virtio-rx.pcap.

6. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap,check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 10: packed virtqueue vm2vm vectorized path test
=========================================================

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

5. Start vhost, then quit pdump and three testpmd, get 251 packets received by virtio-user1 in pdump-virtio-rx.pcap.

6. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap,check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 11: packed virtqueue vm2vm vectorized path test with ring size is not power of 2
==========================================================================================

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=255 \
    -- -i --nb-cores=1 --txd=255 --rxd=255
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=255 \
    -- -i --nb-cores=1 --txd=255 --rxd=255
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1

5. Start vhost, then quit pdump and three testpmd, get 251 packets received by virtio-user1 in pdump-virtio-rx.pcap.

6. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=255 \
    -- -i --nb-cores=1 --txd=255 --rxd=255
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap,check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 12: split virtqueue vm2vm non-mergeable path multi-queues payload check with cbdma enabled
====================================================================================================

1. bind 4 cbdma port to vfio-pci and launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:80:04.2;txq1@0000:80:04.3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=0,mrg_rxbuf=0,in_order=0,queue_size=4096 \
    -- -i --enable-hw-vlan-strip --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=0,mrg_rxbuf=0,in_order=0,queue_size=4096 \
    -- -i --enable-hw-vlan-strip --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 1
    testpmd>set txpkts 64,128,256,512
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 64
    testpmd>start tx_first 1
    testpmd>stop

5. Start vhost testpmd, check virtio-user1 RX-packets is 566 and RX-bytes is 486016, 502 packets with 960 length and 64 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:80:04.2;txq1@0000:80:04.3]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 1
    testpmd>set txpkts 64,128,256,512
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 64
    testpmd>start tx_first 1
    testpmd>stop

10. Rerun step 5.

Test Case 13: split virtqueue vm2vm mergeable path multi-queues payload check with cbdma enabled
================================================================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=0,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=0,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

5. Start vhost testpmd, check 502 packets and 279232 bytes received by virtio-user1 and 54 packets with 4640 length and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

10. Rerun step 5.

Test Case 14: split virtqueue vm2vm inorder non-mergeable path multi-queues payload check with cbdma enabled
============================================================================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=0,mrg_rxbuf=0,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=0,mrg_rxbuf=0,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

5. Start vhost testpmd, check 448 packets and 28672 bytes received by virtio-user1 and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

10. Rerun step 5.

Test Case 15: split virtqueue vm2vm vectorized path multi-queues payload check with cbdma enabled
==================================================================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=0,mrg_rxbuf=0,in_order=0,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

5. Start vhost testpmd, check 448 packets and 28672 bytes received by virtio-user1 and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

10. Rerun step 5.

Test Case 16: Split virtqueue vm2vm inorder mergeable path test non-indirect descriptor with cbdma enable
=========================================================================================================

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=1,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets(include 251 small packets and 32 8K packets)::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=1,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1
    testpmd>stop

5. Start vhost, then quit pdump and three testpmd, about split virtqueue inorder mergeable path, it use the non-indirect descriptors, the 8k length pkt will occupies 5 ring:2000,2000,2000,2000 will need 4 consequent ring,
still need one ring put header. So check 504 packets and 48128 bytes received by virtio-user1 and 502 packets with 64 length and 2 packets with 8K length in pdump-virtio-rx.pcap.

6. Relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx
    testpmd>vhost enable tx all

7. Rerun step 2-5.

Test Case 17: Split virtqueue vm2vm mergeable path test indirect descriptor with cbdma enable
=============================================================================================

1. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=0,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets(include 251 small packets and 32 8K packets)::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=0,queue_size=256 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1
    testpmd>stop

5. Start vhost, then quit pdump and three testpmd, about split virtqueue mergeable path, it use the indirect descriptors, the 8k length pkt will just occupies one ring.
So check 512 packets and 112128 bytes received by virtio-user1 and 502 packets with 64 length and 10 packets with 8K length in pdump-virtio-rx.pcap.

6. Relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx
    testpmd>vhost enable tx all

7. Rerun step 2-5.

Test Case 18: packed virtqueue vm2vm non-mergeable path multi-queues payload check with cbdma enabled
=====================================================================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:80:04.2;txq1@0000:80:04.3]' \
    --iova=va -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

5. Start vhost testpmd, check virtio-user1 RX-packets is 448 and RX-bytes is 28672, 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:80:04.0;txq1@0000:80:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:80:04.2;txq1@0000:80:04.3]' \
    --iova=pa -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

10. Rerun step 5.

Test Case 19: packed virtqueue vm2vm mergeable path multi-queues payload check with cbdma enabled
=================================================================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

5. Start vhost testpmd, then quit pdump, check 502 packets and 279232 bytes received by virtio-user1 and 54 packets with 4640 length and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=pa -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

10. Rerun step 5.

Test Case 20: packed virtqueue vm2vm inorder mergeable path multi-queues payload check with cbdma enabled
=========================================================================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

5. Start vhost testpmd, then quit pdump, check 502 packets and 279232 bytes received by virtio-user1 and 54 packets with 4640 length and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop

10. Rerun step 5.

Test Case 21: packed virtqueue vm2vm inorder non-mergeable path multi-queues payload check with cbdma enabled
=============================================================================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

5. Start vhost testpmd, then quit pdump, check 448 packets and 28672 bytes received by virtio-user1 and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

10. Rerun step 5.

Test Case 22: packed virtqueue vm2vm vectorized path multi-queues payload check with cbdma enabled
===================================================================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

5. Start vhost testpmd, then quit pdump, check 448 packets and 28672 bytes received by virtio-user1 and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

10. Rerun step 5.

Test Case 23: packed virtqueue vm2vm vectorized path multi-queues payload check with ring size is not power of 2 and cbdma enabled
==================================================================================================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=va -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 7-8 --force-max-simd-bitwidth=512  --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097 \
    -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097
    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

5. Start vhost testpmd, then quit pdump, check 448 packets and 28672 bytes received by virtio-user1 and 448 packets with 64 length in pdump-virtio-rx.pcap.

6. Clear virtio-user1 port stats::

    testpmd>stop
    testpmd>clear port stats all
    testpmd>start

7. Quit and relaunch vhost with iova=pa by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,client=1,dmas=[txq0@0000:00:04.0;txq1@0000:00:04.1]' --vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq0@0000:00:04.2;txq1@0000:00:04.3]' \
    --iova=pa -- -i --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx
    testpmd>vhost enable tx all

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

9. Virtio-user0 send packets::

    testpmd>set burst 32
    testpmd>set txpkts 64
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set burst 1
    testpmd>set txpkts 64,256,2000,64,256,2000
    testpmd>start tx_first 27
    testpmd>stop

10. Rerun step 5.

Test Case 24: packed virtqueue vm2vm vectorized-tx path multi-queues test indirect descriptor
=============================================================================================

1. Launch vhost by below command::

    ./<build_target>/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./<build_target>/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -n 4 -l 5-6 --force-max-simd-bitwidth=512 --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256 \
    -- -i --nb-cores=1 --txd=256 --rxd=256

    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7
    testpmd>stop
    testpmd>set txpkts 2000,2000,2000,2000
    testpmd>start tx_first 1
    testpmd>stop

5. Start vhost, then quit pdump and three testpmd, about packed virtqueue vectorized-tx path, it use the indirect descriptors, the 8k length pkt will just occupies one ring.
So check 256 packets and 56064 bytes received by virtio-user1 and 251 packets with 64 length and 5 packets with 8K length in pdump-virtio-rx.pcap.
