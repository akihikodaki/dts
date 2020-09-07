.. Copyright (c) <2018>, Intel Corporation
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

    ./testpmd -c 0xc -n 4 \
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
 
    ./testpmd -c 0x03 -n 3 \
    -- -i --txd=512 --rxd=128 --tx-offloads=0x0 --enable-hw-vlan-strip
    testpmd> set fwd mac
    testpmd> start
    testpmd> show port info 0

5. Check the MTU value of virtio in testpmd on host is 9000::
    testpmd> show port info 1

6. Repeat the step 2 ~ 5, change the mtu value to 68, 65535(the minimal value
   and maximum value), verify the value is changed.
