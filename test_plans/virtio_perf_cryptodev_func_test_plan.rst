.. Copyright (c) <2018-2019> Intel Corporation
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

==============================================
Cryptodev virtio Performance Application Tests
==============================================


Description
===========

This document provides the test plan for testing Cryptodev virtio performance by
crypto perf application. The crypto perf application is a DPDK app under
DPDK app folder.

Cryptodev virtio performance supports AESNI MB PMD, VIRTIO PMD

AESNI MB PMD algorithm table
The table below contains AESNI MB algorithms which supported in crypto virtio perf.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm |  Mode             | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| aes       | cbc               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| sha       |                   | sha1, sha2-224, sha2-384, sha2-256, sha2-512                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| hmac      |                   | Support sha implementations sha1, sha2-224, sha2-256,                     |
|           |                   |                                                                           |
|           |                   | sha2-384, sha2-512                                                        |
+-----------+-------------------+---------------------------------------------------------------------------+

VIRTIO PMD algorithm table
The table below contains virtio algorithms which supported in crypto virtio perf.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm |  Mode             | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| aes       | cbc               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| sha       |                   | sha1, sha2-224, sha2-384, sha2-256, sha2-512                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| hmac      |                   | Support sha implementations sha1, sha2-224, sha2-256,                     |
|           |                   |                                                                           |
|           |                   | sha2-384, sha2-512                                                        |
+-----------+-------------------+---------------------------------------------------------------------------+


Prerequisites
=============

qemu version >= 2.12
in qemu enable vhost-user-crypto::

    ./configure --target-list=x86_64-softmmu --enable-vhost-crypto --prefix=/root/qemu-2.12 && make && make install

the bin is in /root/qemu-2.12 folder, which is your specified

Test case setup:
================

    +--------------+
    |  +--------+  |
    |  |   VM   |  |
    |  +--------+  |
    |              |
    |     HOST     |
    +--------------+

In Host:

# Enable config item in dpdk:

      enable CONFIG_RTE_LIBRTE_VHOST in config/common_base

# Build DPDK and app vhost_crypto

# Run the dpdk vhost sample::

    ./examples/vhost_crypto/build/vhost-crypto --socket-mem 2048,0 --legacy-mem --vdev crypto_aesni_mb_pmd_1 -l 8,9,10 -n 4  -- --config "(9,0,0),(10,0,0)" --socket-file 9,/tmp/vm0_crypto0.sock --socket-file=10,/tmp/vm0_crypto1.sock

# bind vf or pf with driver vfio-pci::

    usertools/dpdk-devbind.py --bind=vfio-pci 0000:60:00.0 0000:60:00.1

# Start VM by the qemu::

    taskset -c 11,12,13,14 /root/qemu-2/bin/qemu-system-x86_64  -name vm0
        -enable-kvm -pidfile /tmp/.vm0.pid
        -cpu host -smp 4
        -m 5120 -object memory-backend-file,id=mem,size=5120M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc
        -net nic,vlan=0,macaddr=00:00:00:18:38:11,model=e1000,addr=1f -net user,vlan=0,hostfwd=tcp:10.67.111.126:6000-:22
        -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0
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

# enable config items in dpdk and compile dpdk:

    enable CONFIG_RTE_EAL_IGB_UIO in config/common_base
    enable CONFIG_RTE_LIBRTE_PMD_AESNI_MB in config/common_base

# set virtio device::

    modprobe uio_pci_generic
    echo -n 0000:00:04.0 > /sys/bus/pci/drivers/virtio-pci/unbind
    echo -n 0000:00:05.0 > /sys/bus/pci/drivers/virtio-pci/unbind
    echo "1af4 1054" > /sys/bus/pci/drivers/uio_pci_generic/new_id

Test Case: Cryptodev AESNI_MB test
==================================

command::

      ./build/app/dpdk-test-crypto-perf -c 0xf --vdev crypto_aesni_mb_pmd  \
      -- --ptest throughput --devtype crypto_aesni_mb --optype cipher-then-auth  \
      --cipher-algo aes-cbc --cipher-op encrypt --cipher-key-sz 16 --cipher-iv-sz 16 \
      --auth-algo sha1-hmac --auth-op generate --auth-key-sz 64 --auth-aad-sz 0 \
      --auth-digest-sz 20 --total-ops 10000000 --burst-sz 32 --buffer-sz 1024

Test Case: Cryptodev VIRTIO test
================================

command::

      ./build/app/dpdk-test-crypto-perf -c 0xf  -a 00:05.0 -- --ptest throughput \
      --devtype crypto_virtio --optype cipher-then-auth  --cipher-algo aes-cbc --cipher-op encrypt \
      --cipher-key-sz 16 --cipher-iv-sz 16 --auth-algo sha1-hmac --auth-op generate --auth-key-sz 64 \
      --auth-aad-sz 0 --auth-digest-sz 20 --total-ops 10000000 --burst-sz 32 --buffer-sz 1024
