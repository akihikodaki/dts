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

=======================================
Cryptodev virtio ipsec Application Tests
=======================================


Description
===========

This document provides the test plan for testing Cryptodev virtio ipsec by
crypto ipsec-secgw application. The crypto virtio ipsec application is a DPDK app
under DPDK app folder.

Cryptodev virtio ipsec supports AESNI MB PMD, VIRTIO PMD

AESNI MB PMD algorithm table
The table below contains AESNI MB algorithms which supported in crypto virtio ipsec.
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
The table below contains virtio algorithms which supported in crypto virtio ipsec.
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
in qemu enable vhost-user-crypto:
    ./configure --target-list=x86_64-softmmu --enable-vhost-crypto --prefix=/root/qemu-2.12 && make && make install
the bin is in /root/qemu-2.12 folder, which is your specified

The options of ipsec-secgw is below:

   ./build/ipsec-secgw [EAL options] --
                        -p PORTMASK -P -u PORTMASK -j FRAMESIZE
                        -l -w REPLAY_WINOW_SIZE -e -a
                        --config (port,queue,lcore)[,(port,queue,lcore]
                        --single-sa SAIDX
                        --rxoffload MASK
                        --txoffload MASK
                        -f CONFIG_FILE_PATH

*   The "-f /path/to/config_file" option enables the application read and
    parse the configuration file specified, and configures the application
    with a given set of SP, SA and Routing entries accordingly.

Test case setup:
================

For function test, the DUT forward UDP packets generated by scapy.
After sending single packet from Scapy, crytpoDev function encrypt/decrypt the
payload in packet by using algorithm setting in VM. the packet back to tester.

Use TCPDump to capture the received packet on tester. Then tester parses the payload
and compare the payload with correct answer pre-stored in scripts:

   +----------+              +----------------------------------+
   |          |              |   +--------+        +--------+   |
   |          | -------------|-->|   VM0  | -----> |        |   |
   |  Tester  |              |   +--------+        |   VM1  |   |
   |          | <------------|-------------------> |        |   |
   |          |              |                     +--------+   |
   +----------+              +----------------------------------+

In Host:
# Build DPDK and vhost_crypto app
      enable CONFIG_RTE_LIBRTE_VHOST in config/common_base
      make install -j T=x86_64-native-linuxapp-gcc
      make -C examples/vhost_crypto

# Compile the latest qemu
# Run the dpdk vhost sample
    ./examples/vhost_crypto/build/vhost-crypto --socket-mem 2048,0 --legacy-mem -w 1a:01.0 -w 1c:01.0 -w 1e:01.0 --vdev crypto_scheduler_pmd_1,slave=0000:1a:01.0_qat_sym,slave=0000:1c:01.0_qat_sym,slave=0000:1e:01.0_qat_sym,mode=round-robin,ordering=enable -l 8,9,10,11,12 -n 6  -- --config "(9,0,0),(10,0,0),(11,0,0),(12,0,0)" --socket-file 9,/tmp/vm0_crypto0.sock --socket-file=10,/tmp/vm0_crypto1.sock --socket-file=11,/tmp/vm1_crypto0.sock --socket-file=12,/tmp/vm1_crypto1.sock

# bind vfio-pci
    usertools/dpdk-devbind.py --bind=vfio-pci 0000:60:00.0 0000:60:00.1 0000:3b:00.0 0000:3b:00.1

# Start VM0 by the qemu
    taskset -c 11,12,13,14 /root/qemu-2/bin/qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid
        -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait
        -net nic,vlan=0,macaddr=00:00:00:42:65:aa,model=e1000,addr=1f -net user,vlan=0,hostfwd=tcp:10.67.111.126:6000-:22
        -cpu host -smp 4 -m 5120 -object memory-backend-file,id=mem,size=5120M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc
        -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0
        -vnc :1
        -chardev socket,path=/tmp/vm0_crypto0.sock,id=vm0_crypto0 -object cryptodev-vhost-user,id=cryptodev0,chardev=vm0_crypto0 -device virtio-crypto-pci,id=crypto0,cryptodev=cryptodev0
        -chardev socket,path=/tmp/vm0_crypto1.sock,id=vm0_crypto1 -object cryptodev-vhost-user,id=cryptodev1,chardev=vm0_crypto1 -device virtio-crypto-pci,id=crypto1,cryptodev=cryptodev1
        -drive file=/root/VMs/virtio_crypto_test_710_1.img
        -device vfio-pci,host=0000:3b:00.0,id=pt_0
        -device vfio-pci,host=0000:3b:00.1,id=pt_1

# Start VM1 by the qemu
    taskset -c 15,16,17,18 /root/qemu-2/bin/qemu-system-x86_64  -name vm1 -enable-kvm -pidfile /tmp/.vm1.pid
        -daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait
        -net nic,vlan=0,macaddr=00:00:00:db:2e:f9,model=e1000,addr=1f -net user,vlan=0,hostfwd=tcp:10.67.111.126:6001-:22
        -cpu host -smp 4 -m 5120 -object memory-backend-file,id=mem,size=5120M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc
        -chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial -device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0
        -vnc :2
        -chardev socket,path=/tmp/vm1_crypto0.sock,id=vm1_crypto0 -object cryptodev-vhost-user,id=cryptodev0,chardev=vm1_crypto0 -device virtio-crypto-pci,id=crypto0,cryptodev=cryptodev0
        -chardev socket,path=/tmp/vm1_crypto1.sock,id=vm1_crypto1 -object cryptodev-vhost-user,id=cryptodev1,chardev=vm1_crypto1 -device virtio-crypto-pci,id=crypto1,cryptodev=cryptodev1
        -drive file=/root/VMs/virtio_crypto_test_710_2.img
        -device vfio-pci,host=0000:60:00.0,id=pt_0
        -device vfio-pci,host=0000:60:00.1,id=pt_1

In VM
# set virtio device
    modprobe uio_pci_generic
    echo -n 0000:00:04.0 > /sys/bus/pci/drivers/virtio-pci/unbind
    echo -n 0000:00:05.0 > /sys/bus/pci/drivers/virtio-pci/unbind
    echo "1af4 1054" > /sys/bus/pci/drivers/uio_pci_generic/new_id

# Run the ipsec test cases cmd

    1. AESNI_MB case Command line Eg:
    In vm0:
    ./examples/ipsec-secgw/build/ipsec-secgw --socket-mem 1024,0  -w 0000:00:06.0 -w 0000:00:07.0 --vdev crypto_aesni_mb_pmd_1 --vdev crypto_aesni_mb_pmd_2 -l 1,2,3 -n 4  -- -P  --config "(0,0,2),(1,0,3)" -u 0x1 -p 0x3 -f /root/ipsec_test0.cfg
    In vm1:
    ./examples/ipsec-secgw/build/ipsec-secgw --socket-mem 1024,0  -w 0000:00:06.0 -w 0000:00:07.0 --vdev crypto_aesni_mb_pmd_1 --vdev crypto_aesni_mb_pmd_2 -l 1,2,3 -n 4  -- -P  --config "(0,0,2),(1,0,3)" -u 0x1 -p 0x3 -f /root/ipsec_test1.cfg

    2. VIRTIO case Command line Eg:
    In vm0:
    ./examples/ipsec-secgw/build/ipsec-secgw --socket-mem 1024,0  -w 0000:00:06.0 -w 0000:00:07.0 -w 00:04.0 -w 00:05.0 -l 1,2,3 -n 4  -- -P  --config "(0,0,2),(1,0,3)" -u 0x1 -p 0x3 -f /root/ipsec_test0.cfg
    In vm1:
    ./examples/ipsec-secgw/build/ipsec-secgw --socket-mem 1024,0  -w 0000:00:06.0 -w 0000:00:07.0 -w 00:04.0 -w 00:05.0 -l 1,2,3 -n 4  -- -P  --config "(0,0,2),(1,0,3)" -u 0x1 -p 0x3 -f /root/ipsec_test1.cfg
