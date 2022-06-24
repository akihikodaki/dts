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

    taskset -c 32 qemu-system-x86_64  -name vm0 \
    -enable-kvm -pidfile /tmp/.vm0.pid -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 -device e1000,netdev=nttsip1  \
    -chardev socket,id=char0,path=vhost-net -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,host_mtu=9000 -cpu host -smp 8 \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on -numa node,memdev=mem \
    -mem-prealloc -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :4 -drive file=/home/image/ubuntu2004.img

3. Use the ifconfig command to check the MTU value of virtio kernel driver is 9000 in VM.

4. Check the MTU value of virtio in testpmd on host is 9000::
    testpmd> show port info 1

5. Repeat the step 2 ~ 4, change the mtu value to 68, 65535(the minimal value
   and maximum value), verify the value is changed.

