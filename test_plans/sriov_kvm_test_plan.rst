.. Copyright (c) <2013-2017>, Intel Corporation
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

=====================================
SRIOV and InterVM Communication Tests
=====================================

Some applications such as pipelining of virtual appliances to virtual appliances
require the high performance InterVM communications.

The testpmd application is used to configure PF VM receive mode, PFUTA hash table
and control traffic to a VF for inter-VM communication.

Prerequisites for all 2VMs cases/Mirror 2VMs cases
==================================================

Create two VF interface VF0 and VF1 from one PF interface and then attach them
to VM0 and VM1. Suppose PF is 0000:08:00.0.Below are commands which can be
used to generate 2VFs and make them in pci-stub modes.::

    ./tools/pci_unbind.py --bind=igb_uio 0000:08:00.0
    echo 2 > /sys/bus/pci/devices/0000\:08\:00.0/max_vfs
    echo "8086 10ed" > /sys/bus/pci/drivers/pci-stub/new_id
    echo 0000:08:10.0 >/sys/bus/pci/devices/0000\:08\:10.0/driver/unbind
    echo 0000:08:10.2 >/sys/bus/pci/devices/0000\:08\:10.2/driver/unbind
    echo 0000:08:10.0 >/sys/bus/pci/drivers/pci-stub/bind
    echo 0000:08:10.2 >/sys/bus/pci/drivers/pci-stub/bind

Start PF driver on the Host and skip the VFs.::

    ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f \
       -n 4 -b 0000:08:10.0  -b 0000:08:10.2 --  -i

For VM0 start up command, you can refer to below command.::

    qemu-system-x86_64 -name vm0 -enable-kvm -m 2048 -smp 4 -cpu host \
        -drive file=/root/Downloads/vm0.img -net nic,macaddr=00:00:00:00:00:01 \
        -net tap,script=/etc/qemu-ifup \
        -device pci-assign,host=08:10.0 -vnc :1 --daemonize

The /etc/qemu-ifup can be below script, need you to create first::

    #!/bin/sh
    set -x
    switch=br0
    if [ -n "$1" ];then
        /usr/sbin/tunctl -u `whoami` -t $1
        /sbin/ip link set $1 up
        sleep 0.5s
        /usr/sbin/brctl addif $switch $1
        exit 0
    else
        echo "Error: no interface specified"
    exit 1
    fi

Similar for VM0, please refer to below command for VM1::

    qemu-system-x86_64 -name vm1 -enable-kvm -m 2048 -smp 4 -cpu host \
       -drive file=/root/Downloads/vm1.img \
       -net nic,macaddr=00:00:00:00:00:02 \
       -net tap,script=/etc/qemu-ifup \
       -device pci-assign,host=08:10.2 -vnc :4 -daemonize

If you want to run all common 2VM cases, please run testpmd on VM0 and VM1 and
start traffic forward on the VM hosts. Some specific prerequisites need to be
set up in each case::

    VF0 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  -i
    VF0 testpmd-> set fwd rxonly
    VF0 testpmd-> start

    VF1 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  -i
    VF1 testpmd-> set fwd mac
    VF1 testpmd-> start

Test Case: InterVM communication test on 2VMs
==============================================

Set the VF0 destination mac address to VF1 mac address, packets send from VF0
will be forwarded to VF1 and then send out::

    VF1 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  -i
    VF1 testpmd-> show port info 0
    VF1 testpmd-> set fwd mac
    VF1 testpmd-> start

    VF0 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  --eth-peer=0,"VF1 mac" -i
    VF0 testpmd-> set fwd mac
    VF0 testpmd-> start

Send 10 packets with VF0 mac address and make sure the packets will be
forwarded by VF1.

Test Case: Add Multi exact MAC address on VF
=============================================

Add an exact destination mac address on VF0::

    PF testpmd-> mac_addr add port 0 vf 0 00:11:22:33:44:55

Send 10 packets with dst mac 00:11:22:33:44:55 to VF0 and make sure VF0 will
receive the packets.

Add another exact destination mac address on VF0::

    PF testpmd-> mac_addr add port 0 vf 0 00:55:44:33:22:11

Send 10 packets with dst mac 00:55:44:33:22:11 to VF0 and make sure VF0 will
receive the packets.

After test need restart PF and VF for clear exact mac addresses, first quit VF,
then quit PF.

Test Case: Enable/Disable one uta MAC address on VF
=====================================================

Enable PF promisc mode and enable VF0 accept uta packets::

    PF testpmd-> set promisc 0 on
    PF testpmd-> set port 0 vf 0 rxmode ROPE on

Add an uta destination mac address on VF0::

    PF testpmd-> set port 0 uta 00:11:22:33:44:55 on

Send 10 packets with dst mac 00:11:22:33:44:55 to VF0 and make sure VF0 will
the packets.

Disable PF promisc mode, repeat step3, check VF0 should not accept uta packets::

    PF testpmd-> set promisc 0 off
    PF testpmd-> set port 0 vf 0 rxmode ROPE off

Test Case: Add Multi uta MAC addresses on VF
==============================================

Add 2 uta destination mac address on VF0::

    PF testpmd-> set port 0 uta 00:55:44:33:22:11 on
    PF testpmd-> set port 0 uta 00:55:44:33:22:66 on

Send 2 flows, first 10 packets with dst mac 00:55:44:33:22:11, another 100
packets with dst mac 00:55:44:33:22:66 to VF0 and make sure VF0 will receive
all the packets.

Test Case: Add/Remove uta MAC address on VF
=============================================

Add one uta destination mac address on VF0::

    PF testpmd-> set port 0 uta 00:55:44:33:22:11 on

Send 10 packets with dst mac 00:55:44:33:22:11 to VF0 and make sure VF0 will
receive the packets.

Remove the uta destination mac address on VF0::

    PF testpmd-> set port 0 uta 00:55:44:33:22:11 off

Send 10 packets with dst mac 00:11:22:33:44:55 to VF0 and make sure VF0 will
not receive the packets.

Add an uta destination mac address on VF0 again::

    PF testpmd-> set port 0 uta 00:11:22:33:44:55 on

Send packet with dst mac 00:11:22:33:44:55 to VF0 and make sure VF0 will
receive again and forwarded the packet. This step is to make sure the on/off
switch is working.

Test Case: Pause RX Queues
============================

Pause RX queue of VF0 then send 10 packets to VF0 and make sure VF0 will not
receive the packets::

    PF testpmd-> set port 0 vf 0 rx off

Enable RX queue of VF0 then send 10 packets to VF0 and make sure VF0 will
receive the packet::

    PF testpmd-> set port 0 vf 0 rx on

Repeat the off/on twice to check the switch capability, and ensure on/off can
work stable.

Test Case: Pause TX Queues
============================

Pause TX queue of VF0 then send 10 packets to VF0 and make sure VF0 will not
forward the packet::

    PF testpmd-> set port 0 vf 0 tx off

Enable RX queue of VF0 then send 10 packets to VF0 and make sure VF0 will
forward the packet::

    PF testpmd-> set port 0 vf 0 tx on

Repeat the off/on twice to check the switch capability, and ensure on/off can
work stable.

Test Case: Prevent Rx of Broadcast on VF
==========================================

Disable VF0 rx broadcast packets then send broadcast packet to VF0 and make
sure VF0 will not receive the packet::

    PF testpmd-> set port 0 vf 0 rxmode  BAM off

Enable VF0 rx broadcast packets then send broadcast packet to VF0 and make sure
VF0 will receive and forward the packet::

    PF testpmd-> set port 0 vf 0 rxmode  BAM on

Repeat the off/on twice to check the switch capability, and ensure on/off can
work stable.

Prerequisites for Scaling 4VFs per 1PF
======================================

Create 4VF interface VF0, VF1, VF2, VF3 from one PF interface and then attach
them to VM0, VM1, VM2 and VM3.Start PF driver on the Host and skip the VF
driver will has been already attached to VMs::

    On PF ./tools/pci_unbind.py --bind=igb_uio 0000:08:00.0
    echo 4 > /sys/bus/pci/devices/0000\:08\:00.0/max_vfs
    ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 -b 0000:08:10.0 -b 0000:08:10.2 -b 0000:08:10.4 -b 0000:08:10.6 --  -i

If you want to run all common 4VM cases, please run testpmd on VM0, VM1, VM2
and VM3 and start traffic forward on the VM hosts. Some specific prerequisites
are set up in each case::

    VF0 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  -i
    VF1 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  -i
    VF2 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  -i
    VF3 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  -i

Test Case: Scaling InterVM communication on 4VFs
==================================================

Set the VF0 destination mac address to VF1 mac address, packets send from VF0
will be forwarded to VF1 and then send out. Similar for VF2 and VF3::

    VF1 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  -i
    VF1 testpmd-> show port info 0
    VF1 testpmd-> set fwd mac
    VF1 testpmd-> start

    VF0 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  --eth-peer=0,"VF1 mac" -i
    VF0 testpmd-> set fwd mac
    VF0 testpmd-> start

    VF3 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  -i
    VF3 testpmd-> show port info 0
    VF3 testpmd-> set fwd mac
    VF3 testpmd-> start

    VF2 ./x86_64-default-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 --  --eth-peer=0,"VF3 mac" -i
    VF2 testpmd-> set fwd mac
    VF2 testpmd-> start

Send 2 flows, one with VF0 mac address and make sure the packets will be
forwarded by VF1, another with VF2 mac address and make sure the packets will
be forwarded by VF3.
