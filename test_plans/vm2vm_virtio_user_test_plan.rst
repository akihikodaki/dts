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

======================================
vm2vm vhost-user/virtio-user test plan
======================================

Description
===========

This test plan includes split virtqueue vm2vm in-order mergeable, in-order non-mergeable, mergeable, non-mergeable, vector_rx path test, and packed virtqueue vm2vm in-order mergeable, in-order non-mergeable, mergeable, non-mergeable path test. This plan also check the payload of packets is accurate. For packed virtqueue test, need using qemu version > 4.2.0.

Prerequisites
=============

Enable pcap lib in dpdk code and recompile::

    --- a/config/common_base
    +++ b/config/common_base
    @@ -492,7 +492,7 @@ CONFIG_RTE_LIBRTE_PMD_NULL=y
     #
     # Compile software PMD backed by PCAP files
     #
    -CONFIG_RTE_LIBRTE_PMD_PCAP=n
    +CONFIG_RTE_LIBRTE_PMD_PCAP=y

Then build DPDK.

Test flow
=========
Virtio-user <-> Vhost-user <-> Testpmd <-> Vhost-user <-> Virtio-user

Test Case 1: packed virtqueue vm2vm mergeable path test
=======================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
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

6. Quit pdump and three testpmd, get 284 packets received by virtio-user1 in pdump-virtio-rx.pcap.

7. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

9. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 7-8 --socket-mem 1024,1024 --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0 \
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
    testpmd>stop
    testpmd>set burst 32
    testpmd>set txpkts 2000
    testpmd>start tx_first 1

10. Quit pdump,vhost received packets in pdump-vhost-rx.pcap, check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 2: packed virtqueue vm2vm inorder mergeable path test
===============================================================

1. Launch testpmd by below command::

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=1 \
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

5. Start vhost, then quit pdump and three testpmd, get 252 packets received by virtio-user1 in pdump-virtio-rx.pcap.

6. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=1 \
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

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap, check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 3: packed virtqueue vm2vm non-mergeable path test
===========================================================

1. Launch testpmd by below command::

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
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

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
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

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1 \
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

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=1,mrg_rxbuf=0,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap,check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 5: split virtqueue vm2vm mergeable path test
======================================================

1. Launch vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=1,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=./pdump-virtio-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
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

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

8. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

9. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
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

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=1,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
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

5. Start vhost, then quit pdump and three testpmd, get 256 packets received by virtio-user1 in pdump-virtio-rx.pcap.

6. Launch testpmd by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=1,in_order=1 \
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

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap,check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.

Test Case 7: split virtqueue vm2vm non-mergeable path test
==========================================================

1. Launch testpmd by below command::

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256 --enable-hw-vlan-strip

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
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

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
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

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=1 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set fwd rxonly
    testpmd>start

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
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

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
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

    ./testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1' --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx

2. Launch virtio-user1 by below command::

    ./testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio1 \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256

3. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=virtio1 -- --pdump 'device_id=net_virtio_user1,queue=*,rx-dev=/root/pdump-rx.pcap,mbuf-size=8000'

4. Launch virtio-user0 and send 8k length packets::

    ./testpmd -n 4 -l 5-6 --socket-mem 1024,1024 \
    --no-pci --file-prefix=virtio \
    --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=0 \
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

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-2 -n 4 --socket-mem 1024,1024 --no-pci --file-prefix=vhost  \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' -- \
    -i --nb-cores=1 --no-flush-rx
    testpmd>set fwd rxonly
    testpmd>start

7. Attach pdump secondary process to primary process by same file-prefix::

    ./x86_64-native-linuxapp-gcc/app/dpdk-pdump -v --file-prefix=vhost -- --pdump 'port=0,queue=*,rx-dev=/root/pdump-vhost-rx.pcap,mbuf-size=8000'

8. Launch virtio-user1 by below command::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -l 7-8 --socket-mem 1024,1024 \
    --no-pci \
    --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,packed_vq=0,mrg_rxbuf=0,in_order=0 \
    -- -i --nb-cores=1 --txd=256 --rxd=256
    testpmd>set burst 1
    testpmd>start tx_first 27
    testpmd>stop
    testpmd>set burst 32
    testpmd>start tx_first 7

9. Quit pdump,vhost received packets in pdump-vhost-rx.pcap,check headers and payload of all packets in pdump-virtio-rx.pcap and pdump-vhost-rx.pcap and ensure the content are same.