.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2018 Intel Corporation

===================
Vhost MTU Test Plan
===================

The feature test the setting of MTU value of virtio-net and kernel driver.

Prerequisites:
==============

The guests kernel should grand than 4.10
The qemu version should greater or equal to 2.9

Test Case: Test the MTU in virtio-net
=====================================
1. Launch the testpmd by below commands on host, and config mtu::

    ./<build_target>/app/dpdk-testpmd -c 0xc -n 4 \
    --vdev 'net_vhost0,iface=vhost-net,queues=1' \
    -- -i --txd=512 --rxd=128 --nb-cores=1 --port-topology=chained
    testpmd> set fwd mac
    testpmd> start

2. Launch VM::

    Use the qemu_2.9 or qemu 2.10 to start the VM and the VM kernel should
    grand than 4.10, set the mtu value to 9000

    qemu-system-x86_64 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mrg_rxbuf=on,host_mtu=9000

3. Check the MTU value in VM::

    Use the ifconfig command to check the MTU value of
    virtio kernel driver is 9000 in VM.

4. Bind the virtio driver to igb_uio, launch testpmd in VM, and verify 
   the mtu in port info is 9000::
 
    ./<build_target>/app/dpdk-testpmd -c 0x03 -n 3 \
    -- -i --txd=512 --rxd=128 --tx-offloads=0x0 --enable-hw-vlan-strip
    testpmd> set fwd mac
    testpmd> start
    testpmd> show port info 0

5. Check the MTU value of virtio in testpmd on host is 9000::
    testpmd> show port info 1

6. Repeat the step 2 ~ 5, change the mtu value to 68, 65535(the minimal value
   and maximum value), verify the value is changed.
