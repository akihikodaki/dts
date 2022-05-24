.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=====================================================
vhost/virtio-user interrupt mode with cbdma test plan
=====================================================

Virtio-user interrupt need test with l3fwd-power sample, small packets send from traffic generator
to virtio side, check virtio-user cores can be wakeup status, and virtio-user cores should be sleep
status after stop sending packets from traffic generator when CBDMA enabled.This test plan cover 
vhost-user as the backend.

Test Case1: LSC event between vhost-user and virtio-user with split ring and cbdma enabled
==========================================================================================

flow: Vhost <--> Virtio

1. Bind 1 CBDMA channel to vfio-pci driver, then start vhost-user side::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3000 -n 4 -a 00:04.0 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0,dmas=[txq0@00:04.0]' -- -i
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

Test Case2: Split ring virtio-user interrupt test with vhost-user as backend and cbdma enabled
==============================================================================================

flow: TG --> NIC --> Vhost --> Virtio

1. Bind 1 CBDMA channel and 1 NIC port to vfio-pci, launch testpmd with a virtual vhost device as backend::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7c -n 4 --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@00:04.0]' -- -i  --rxq=1 --txq=1
    testpmd> start

2. Start l3fwd-power with a virtio-user device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -c 0xc000 -n 4 --log-level='user1,7' --no-pci --file-prefix=l3fwd-pwd \
    --vdev=virtio_user0,path=./vhost-net -- -p 1 -P --config="(0,0,14)" --parse-ptype

3. Send packets with packet generator, check the virtio-user related core can be wakeup status.

4. Stop sending packets with packet generator, check virtio-user related core change to sleep status.

5. Restart sending packets with packet generator, check virtio-user related core change to wakeup status again.

Test Case3: LSC event between vhost-user and virtio-user with packed ring and cbdma enabled
===========================================================================================

flow: Vhost <--> Virtio

1. Bind one cbdma port to vfio-pci driver, then start vhost-user side::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3000 -n 4 -a 00:04.0 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0,dmas=[txq0@00:04.0]' -- -i
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

Test Case4: Packed ring virtio-user interrupt test with vhost-user as backend and cbdma enabled
================================================================================================

flow: TG --> NIC --> Vhost --> Virtio

1. Bind one cbdma port and one NIC port to vfio-pci, launch testpmd with a virtual vhost device as backend::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7c -n 4 --vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0@00:04.0]' -- -i  --rxq=1 --txq=1
    testpmd> start

2. Start l3fwd-power with a virtio-user device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -c 0xc000 -n 4 --log-level='user1,7' --no-pci --file-prefix=l3fwd-pwd \
    --vdev=virtio_user0,path=./vhost-net,packed_vq=1 -- -p 1 -P --config="(0,0,14)" --parse-ptype

3. Send packets with packet generator, check the virtio-user related core can be wakeup status.

4. Stop sending packets with packet generator, check virtio-user related core change to sleep status.

5. Restart sending packets with packet generator, check virtio-user related core change to wakeup status again.

