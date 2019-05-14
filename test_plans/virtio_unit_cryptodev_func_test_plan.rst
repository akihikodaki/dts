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

===========================
CryptoDev virtio unit Tests
===========================

Description
===========

This document provides the plan for testing Cryptodev virtio API via Cryptodev unit tests.
Unit tests include supported Hardware and Software PMD(polling mode device) and supported algorithms.

This test suite will run all cryptodev virtio related unit test cases. Alternatively, you could execute
the unit tests manually by app/test DPDK application.

Unit Test List
==============

- cryptodev_virtio_autotest

Prerequisites
=============

qemu version >= 2.12
in qemu enable vhost-user-crypto:

./configure --target-list=x86_64-softmmu --enable-vhost-crypto --prefix=/root/qemu-2.12 && make && make install

the bin is in /root/qemu-2.12 folder, which is your specified

Test Case Setup
===============

    +--------------+
    |  +--------+  |
    |  |   VM   |  |
    |  +--------+  |
    |              |
    |     HOST     |
    +--------------+

In Host:

# Build DPDK and vhost_crypto app

      enable CONFIG_RTE_LIBRTE_VHOST in config/common_base
      make install -j T=x86_64-native-linuxapp-gcc
      make -C examples/vhost_crypto

# Run the dpdk vhost sample

      ./examples/vhost_crypto/build/vhost-crypto --file-prefix="vhost_crypto_1"
          [EAL options]
          [Cryptodev PMD]
          -- --cdev-queue-id 0
          --socket-file THE PATH OF SOCKET FILE

# bind vfio-pci

      usertools/dpdk-devbind.py --bind=vfio-pci 0000:60:00.0 0000:60:00.1

# Start VM by the qemu

      taskset -c 11,12,13,14 /root/qemu-2.12/bin/qemu-system-x86_64  -name vm0
          -enable-kvm -pidfile /tmp/.vm0.pid
          -cpu host -smp 4
          -m 5120 -object memory-backend-file,id=mem,size=5120M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc
          -net nic,vlan=0,macaddr=00:00:00:18:38:11,model=e1000,addr=1f -net user,vlan=0,hostfwd=tcp:10.67.111.126:6000-:22
          -device virtio-serial
          -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0
          -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait
          -vnc :1
          -chardev socket,path=/tmp/vm0_crypto0.sock,id=vm0_crypto0 -object cryptodev-vhost-user,id=cryptodev0,chardev=vm0_crypto0 -device virtio-crypto-pci,id=crypto0,cryptodev=cryptodev0
          -chardev socket,path=/tmp/vm0_crypto1.sock,id=vm0_crypto1 -object cryptodev-vhost-user,id=cryptodev1,chardev=vm0_crypto1 -device virtio-crypto-pci,id=crypto1,cryptodev=cryptodev1
          -drive file=/root/VMs/virtio_crypto_test_710_1.img
          -device vfio-pci,host=0000:60:00.0,id=pt_0
          -device vfio-pci,host=0000:60:00.1,id=pt_1

In VM:

# set virtio device

      modprobe uio_pci_generic
      echo -n 0000:00:04.0 > /sys/bus/pci/drivers/virtio-pci/unbind
      echo -n 0000:00:05.0 > /sys/bus/pci/drivers/virtio-pci/unbind
      echo "1af4 1054" > /sys/bus/pci/drivers/uio_pci_generic/new_id

# Build the guest DPDK and app/test

# Manually verify the app/test by this command, as example, in your build folder:

      ./app/test -c 1 -n 1
      RTE>> cryptodev_virtio_autotest

Expected all tests could pass in testing.
