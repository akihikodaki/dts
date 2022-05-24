.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

==========================================
vhost/virtio-user interrupt mode test plan
==========================================

Virtio-user interrupt need test with l3fwd-power sample, small packets send from traffic generator
to virtio side, check virtio-user cores can be wakeup status, and virtio-user cores should be sleep
status after stop sending packets from traffic generator.This test plan cover both vhost-net and
vhost-user as the backend.

Test Case1: Split ring virtio-user interrupt test with vhost-user as backend
============================================================================

flow: TG --> NIC --> Vhost --> Virtio

1. Bind one NIC port to vfio-pci, launch testpmd with a virtual vhost device as backend::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7c -n 4 --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i  --rxq=1 --txq=1
    testpmd>start

2. Start l3fwd-power with a virtio-user device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -c 0xc000 -n 4 --log-level='user1,7' --no-pci --file-prefix=l3fwd-pwd \
    --vdev=virtio_user0,path=./vhost-net -- -p 1 -P --config="(0,0,14)" --parse-ptype

3. Send packets with packet generator, check the virtio-user related core can be wakeup status.

4. Stop sending packets with packet generator, check virtio-user related core change to sleep status.

5. Restart sending packets with packet generator, check virtio-user related core change to wakeup status again.

Test Case2: Split ring virtio-user interrupt test with vhost-net as backend
===========================================================================

flow: Tap --> Vhost-net --> Virtio

1. Start l3fwd-power with a virtio-user device, vhost-net as backend::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -c 0xc000 -n 4 --log-level='user1,7' --no-pci --file-prefix=l3fwd-pwd \
    --vdev=virtio_user0,path=/dev/vhost-net -- -p 1 -P --config="(0,0,14)" --parse-ptype

2. Vhost-net will generate one tap device, normally, it's TAP0, config it and generate packets on it using pind cmd::

    ifconfig tap0 up
    ifconfig tap0 1.1.1.1
    ping -I tap0 1.1.1.2

3. Check the virtio-user related core can be wake up.

4. Stop sending packets with tap device, check virtio-user related core change to sleep status.

5. Restart sending packets with tap device, check virtio-user related core change to wakeup status again.

Test Case3: LSC event between vhost-user and virtio-user with split ring
========================================================================

flow: Vhost <--> Virtio

1. Start vhost-user side::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3000 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i
    testpmd>set fwd mac
    testpmd>start

2. Start virtio-user side::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc000 -n 4 --no-pci --file-prefix=virtio --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net -- -i --tx-offloads=0x00
    testpmd>set fwd mac
    testpmd>start

3. Check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "up"

4. Quit the vhost-user side with testpmd, then check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"

Test Case4: Packed ring virtio-user interrupt test with vhost-user as backend
=============================================================================

flow: TG --> NIC --> Vhost --> Virtio

1. Bind one NIC port to vfio-pci, launch testpmd with a virtual vhost device as backend::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7c -n 4 --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i  --rxq=1 --txq=1
    testpmd>start

2. Start l3fwd-power with a virtio-user device::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -c 0xc000 -n 4 --log-level='user1,7' --no-pci --file-prefix=l3fwd-pwd \
    --vdev=virtio_user0,path=./vhost-net,packed_vq=1 -- -p 1 -P --config="(0,0,14)" --parse-ptype

3. Send packets with packet generator, check the virtio-user related core can be wakeup status.

4. Stop sending packets with packet generator, check virtio-user related core change to sleep status.

5. Restart sending packets with packet generator, check virtio-user related core change to wakeup status again.

Test Case5: Packed ring virtio-user interrupt test with vhost-net as backend with
=================================================================================

flow: Tap --> Vhost-net --> Virtio

1. Start l3fwd-power with a virtio-user device, vhost-net as backend::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -c 0xc000 -n 4 --log-level='user1,7' --no-pci --file-prefix=l3fwd-pwd \
    --vdev=virtio_user0,path=/dev/vhost-net,packed_vq=1 -- -p 1 -P --config="(0,0,14)" --parse-ptype

2. Vhost-net will generate one tap device, normally, it's TAP0, config it and generate packets on it using pind cmd::

    ifconfig tap0 up
    ifconfig tap0 1.1.1.1
    ping -I tap0 1.1.1.2

3. Check the virtio-user related core can be wake up.

4. Stop sending packets with tap device, check virtio-user related core change to sleep status.

5. Restart sending packets with tap device, check virtio-user related core change to wakeup status again.

Test Case6: LSC event between vhost-user and virtio-user with packed ring
=========================================================================

flow: Vhost <--> Virtio

1. Start vhost-user side::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3000 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1,client=0' -- -i
    testpmd>set fwd mac
    testpmd>start

2. Start virtio-user side::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc000 -n 4 --no-pci --file-prefix=virtio --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1 -- -i --tx-offloads=0x00
    testpmd>set fwd mac
    testpmd>start

3. Check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "up"

4. Quit the vhost-user side with testpmd, then check the virtio-user side link status::

    testpmd> show port info 0
    #it should show "down"
