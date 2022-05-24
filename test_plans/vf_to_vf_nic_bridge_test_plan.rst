.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2015-2017 Intel Corporation

=====================
VF to VF Bridge Tests
=====================

This test suite aims to validate the bridge function on physical functional
for virtual functional to virtual functional communication. Cases of the
suite based on the vm to vm test scenario, echo vm needs on vf, and both of
the vfs generated from the same pf port.

Prerequisites:
==============

On host:

* Guest: two img with os for kvm qemu

* NIC: one pf port

On Guest:

* Stream Source end: scapy pcpay


Set up basic virtual scenario:
==============================

Step 1: generate two vfs on the target pf port (i.e. 0000:85:00.0)::

        echo 2 > /sys/bus/pci/devices/0000\:85\:00.0/sriov_numvfs

Step 2: bind the two vfs to vfio-pci::

        modprobe vfio-pci
        ./dpdk/usertools/dpdk-devbind.py -b vfio-pci 0000:85:02.0 0000:85:02.1

Step 3: passthrough vf 0 to vm0 and start vm0::

        taskset -c 20,21,22,23 /usr/local/qemu-2.4.0/x86_64-softmmu/qemu-system-x86_64 \
        -name vm0 -enable-kvm -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
        -device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 \
        -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
        -net nic,vlan=0,macaddr=00:00:00:e2:4f:fb,addr=1f \
        -net user,vlan=0,hostfwd=tcp:10.239.128.125:6064-:22 \
        -device vfio-pci,host=85:10.0,id=pt_0 -cpu host -smp 4 -m 6144 \
        -object memory-backend-file,id=mem,size=6144M,mem-path=/mnt/huge,share=on \
        -numa node,memdev=mem -mem-prealloc -drive file=/home/img/vm0.img -vnc :4

Step 4: passthrough vf 1 to vm1 and start vm1::

        taskset -c 30,31,32,33 /usr/local/qemu-2.4.0/x86_64-softmmu/qemu-system-x86_64  \
        -name vm1 -enable-kvm -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 \
        -device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 \
        -daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait \
        -net nic,vlan=0,macaddr=00:00:00:7b:d5:cb,addr=1f \
        -net user,vlan=0,hostfwd=tcp:10.239.128.125:6126-:22 \
        -device vfio-pci,host=85:10.2,id=pt_0 -cpu host -smp 4 -m 6144 \
        -object memory-backend-file,id=mem,size=6144M,mem-path=/mnt/huge,share=on \
        -numa node,memdev=mem -mem-prealloc -drive file=/home/img/vm1.img -vnc :5


Test Case1: test_2vf_d2d_testpmd_stream
=======================================

both vfs in the two vms using the dpdk driver, send stream from vf1 in vm1 by
dpdk testpmd to vf in vm0, and verify the vf on vm0 can receive stream.

Step 1: run testpmd on vm0::

        ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 1  -- -i

Step 2: set rxonly and start on vm0::

        set fwd rxonly
        start

Step 3: run testpmd on vm1::

        ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 1  -- -i

Step 4: Set forward, specifying that the opposing MAC sends 100 packets on vm1::

        set fwd mac
        set eth-peer 0 52:54:12:45:67:10(vm0_mac)
        set burst 50
        start tx_first 2

Step 5: verify vf 0 receive status on vm0: Rx-packets equal to send packets count, 100::

        show port stats 0
        ######################## NIC statistics for port 0  ########################
        RX-packets: 100  RX-missed: 0          RX-bytes:  6000
        RX-errors: 0
        RX-nombuf:  0
        TX-packets: 0          TX-errors: 0          TX-bytes:  0
        ############################################################################

Test Case2: test_2vf_d2k_testpmd_stream
=======================================

Step 1: bind vf to kernel driver on vm0

Step 2: start up vf interface and using tcpdump to capture received packets::

        tcpdump -i vm0_vf ether dst vm0_mac -w m.pcap

Step 3: Set forward, specifying that the opposing MAC sends 100 packets on vm1::

        set fwd mac
        set eth-peer 0 52:54:12:45:67:10(vm0_mac)
        set burst 50
        start tx_first 2

Step 4: verify vf 0 receive status on vm0: packet captured equal to send packets count, 100

Test Case3: test_2vf_k2d_scapy_stream
=====================================

Step 1: run testpmd on vm0::

        ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x7 -n 1  -- -i

Step 2: set rxonly and start on vm0::

        set fwd rxonly
        start

Step 3: bind vf to kernel driver on vm0

Step 4: using scapy to send packets on vm1::

        sendp([Ether(dst="vm0_mac", src="vm1_mac"") / IP() / Raw(load="X" * 46)], iface="ens4", count=100)

Step 5:verify vf 0 receive status on vm0: Rx-packets equal to send packets count, 100::

        show port stats 0
        ######################## NIC statistics for port 0  ########################
        RX-packets: 100  RX-missed: 0          RX-bytes:  6000
        RX-errors: 0
        RX-nombuf:  0
        TX-packets: 0          TX-errors: 0          TX-bytes:  0
        ############################################################################
