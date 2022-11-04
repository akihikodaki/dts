.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

======================================
vm2vm vhost-user/virtio-user test plan
======================================

Description
===========

This test plan test several features in VM2VM topo:
1. Split virtqueue vm2vm in-order mergeable, in-order non-mergeable, mergeable, non-mergeable, vector_rx path test.
2. Packed virtqueue vm2vm in-order mergeable, in-order non-mergeable, mergeable, non-mergeable, vectorized path (ringsize not powerof 2) test.
3. Test indirect descriptor feature. For example, the split ring mergeable inorder path use non-indirect descriptor, the 2000,2000,2000,2000 chain packets will need 4 consequent ring, still need one ring put header.
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

Test Case 12: packed virtqueue vm2vm vectorized-tx path multi-queues test indirect descriptor
=============================================================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd/app/dpdk-testpmd -l 1-2 -n 4 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd/app/dpdk-testpmd -n 4 -l 7-8 --no-pci --file-prefix=virtio1 --force-max-simd-bitwidth=512 \
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
