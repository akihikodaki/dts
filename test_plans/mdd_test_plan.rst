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

======================================
Malicious Driver Detection (MDD) Tests
======================================

Malicious Driver Detection (MDD) support sagevill and i350 nic, dpdk2.3+ only
support sagevill NIC. ixgbe supports disable MDD from version 4.2.3
so this test must run dpdk2.3+
and used ixgbe 4.2.3+ in host.

Notice: use command ``insmod ixgbe.ko MDD=0,0`` to disable MDD. Each "0" in the
command refers to a port. For example, if there are 6 ixgbe ports, the command
should be changed to ``insmod ixgbe.ko MDD=0,0,0,0,0,0``

Test Case 1: enable_mdd_dpdk_disable
====================================
1. enable the MDD::

    rmmod ixgbe
    modprobe ixgbe MDD=1,1
    ifconfig ens865f1 up
    ifconfig ens865f0 up

2. pf_port0 virtualizes a vf0 and pf_port1 virtualizes a vf1::

    echo 1 > /sys/bus/pci/devices/0000\:03\:00.0/sriov_numvfs
    echo 1 > /sys/bus/pci/devices/0000\:03\:00.1/sriov_numvfs

3. passthrough vf0 and vf1 to vm0 and start vm0::

    taskset -c 4,5,6,7 qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
    -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device vfio-pci,host=0000:03:10.0,id=pt_0 \
    -device vfio-pci,host=0000:03:10.1,id=pt_1 -cpu host -smp 4 -m 10240 \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :1 \
    -drive file=/home/image/ubuntu16-0.img,format=qcow2,if=virtio,index=0,media=disk

4. login vm0, got VFs pci device id in vm0, assume they are 00:06.0 & 00:07.0, bind them to igb_uio driver::

    modprobe uio
    insmod igb_uio.ko
    ./tools/dpdk_nic_bind.py --bind=igb_uio 00:06.0 00:07.0

5. Turn on testpmd and set mac forwarding mode::

    ./testpmd -c 0x0f -n 4 -- -i --portmask=0x3 --tx-offloads=0x1

    testpmd> set fwd mac
    testpmd> start

6. get mac address of VF0 and use it as dest mac, using scapy to send 2000 packets from tester::

    sendp(Ether(src='tester_mac', dst='vm_port0_mac')/IP()/UDP()/Raw(load='XXXXXXXXXXXXXXXXXX'), iface="tester_nic")

7. verify the packets can't be received by VF1,As follows::

    ######################## NIC statistics for port 0  ########################
    RX-packets: 2000       RX-missed: 0          RX-bytes:  120000
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 0          TX-errors: 0          TX-bytes:  0

    Throughput (since last show)
    Rx-pps:          634
    Tx-pps:            0
    ############################################################################
    ######################## NIC statistics for port 1  ########################
    RX-packets: 0          RX-missed: 0          RX-bytes:  0
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 0          TX-errors: 0          TX-bytes:  0

    Throughput (since last show)
    Rx-pps:            0
    Tx-pps:            0
    ############################################################################

8. You can see "ixgbe 0000:03:00.0: Malicious event on VF 0 tx:100000 rx:0" by using the "dmesg -c" command on the host::

    dmesg -c | grep 'event'

Test Case 2: enable_mdd_dpdk_enable
===================================
1. enable the MDD::

    rmmod ixgbe
    modprobe ixgbe MDD=1,1
    ifconfig ens865f1 up
    ifconfig ens865f0 up

2. pf_port0 virtualizes a vf0 and pf_port1 virtualizes a vf1::

    echo 1 > /sys/bus/pci/devices/0000\:03\:00.0/sriov_numvfs
    echo 1 > /sys/bus/pci/devices/0000\:03\:00.1/sriov_numvfs

3. passthrough vf0 and vf1 to vm0 and start vm0::

    taskset -c 4,5,6,7 qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
    -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device vfio-pci,host=0000:03:10.0,id=pt_0 \
    -device vfio-pci,host=0000:03:10.1,id=pt_1 -cpu host -smp 4 -m 10240 \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :1 \
    -drive file=/home/image/ubuntu16-0.img,format=qcow2,if=virtio,index=0,media=disk

4. login vm0, got VFs pci device id in vm0, assume they are 00:06.0 & 00:07.0, bind them to igb_uio driver::

    modprobe uio
    insmod igb_uio.ko
    ./tools/dpdk_nic_bind.py --bind=igb_uio 00:06.0 00:07.0

5. Turn on testpmd and set mac forwarding mode::

    ./testpmd -c 0x0f -n 4 -- -i --portmask=0x3 --tx-offloads=0x0

    testpmd> set fwd mac
    testpmd> start

6. get mac address of VF0 and use it as dest mac, using scapy to send 2000 packets from tester::

    sendp(Ether(src='tester_mac', dst='vm_port0_mac')/IP()/UDP()/Raw(load='XXXXXXXXXXXXXXXXXX'), iface="tester_nic")

7. verify the packets can't be received by VF1,As follows::

    ######################## NIC statistics for port 0  ########################
    RX-packets: 2000       RX-missed: 0          RX-bytes:  120000
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 0          TX-errors: 0          TX-bytes:  0

    Throughput (since last show)
    Rx-pps:          634
    Tx-pps:            0
    ############################################################################
    ######################## NIC statistics for port 1  ########################
    RX-packets: 0          RX-missed: 0          RX-bytes:  0
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 0          TX-errors: 0          TX-bytes:  0

    Throughput (since last show)
    Rx-pps:            0
    Tx-pps:            0
    ############################################################################

8. You can see "ixgbe 0000:03:00.0: Malicious event on VF 0 tx:100000 rx:0" by using the "dmesg -c" command on the host::

    dmesg -c | grep 'event'

Test Case 3: disable_mdd_dpdk_disable
=====================================
1. disable the MDD::

    rmmod ixgbe
    modprobe ixgbe MDD=0,0
    ifconfig ens865f1 up
    ifconfig ens865f0 up

2. pf_port0 virtualizes a vf0 and pf_port1 virtualizes a vf1::

    echo 1 > /sys/bus/pci/devices/0000\:03\:00.0/sriov_numvfs
    echo 1 > /sys/bus/pci/devices/0000\:03\:00.1/sriov_numvfs

3. passthrough vf0 and vf1 to vm0 and start vm0::

    taskset -c 4,5,6,7 qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
    -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device vfio-pci,host=0000:03:10.0,id=pt_0 \
    -device vfio-pci,host=0000:03:10.1,id=pt_1 -cpu host -smp 4 -m 10240 \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :1 \
    -drive file=/home/image/ubuntu16-0.img,format=qcow2,if=virtio,index=0,media=disk

4. login vm0, got VFs pci device id in vm0, assume they are 00:06.0 & 00:07.0, bind them to igb_uio driver::

    modprobe uio
    insmod igb_uio.ko
    ./tools/dpdk_nic_bind.py --bind=igb_uio 00:06.0 00:07.0

5. Turn on testpmd and set mac forwarding mode::

    ./testpmd -c 0xf -n 4 -- -i --portmask=0x3 --tx-offloads=0x1

    testpmd> set fwd mac
    testpmd> start

6. get mac address of VF0 and use it as dest mac, using scapy to send 2000 packets from tester::

    sendp(Ether(src='tester_mac', dst='vm_port0_mac')/IP()/UDP()/Raw(load='XXXXXXXXXXXXXXXXXX'), iface="tester_nic")

7. verify the packets can be received by VF1,As follows::

    ######################## NIC statistics for port 0  ########################
    RX-packets: 2000       RX-missed: 0          RX-bytes:  120000
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 0          TX-errors: 0          TX-bytes:  0

    Throughput (since last show)
    Rx-pps:          634
    Tx-pps:            0
    ############################################################################
    ######################## NIC statistics for port 1  ########################
    RX-packets: 0          RX-missed: 0          RX-bytes:  0
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 2000       TX-errors: 0          TX-bytes:  120000

    Throughput (since last show)
    Rx-pps:            0
    Tx-pps:          618
    ############################################################################

8. You cannot see "ixgbe 0000:03:00.0: Malicious event on VF 0 tx:100000 rx:0" by using the "dmesg -c" command on the host::

    dmesg -c | grep 'event'

Test Case 4: disable_mdd_dpdk_enable
====================================
1. disable the MDD::

    rmmod ixgbe
    modprobe ixgbe MDD=0,0
    ifconfig ens865f1 up
    ifconfig ens865f0 up

2. pf_port0 virtualizes a vf0 and pf_port1 virtualizes a vf1::

    echo 1 > /sys/bus/pci/devices/0000\:03\:00.0/sriov_numvfs
    echo 1 > /sys/bus/pci/devices/0000\:03\:00.1/sriov_numvfs

3. passthrough vf0 and vf1 to vm0 and start vm0::

    taskset -c 4,5,6,7 qemu-system-x86_64  -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid \
    -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 -device vfio-pci,host=0000:03:10.0,id=pt_0 \
    -device vfio-pci,host=0000:03:10.1,id=pt_1 -cpu host -smp 4 -m 10240 \
    -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :1 \
    -drive file=/home/image/ubuntu16-0.img,format=qcow2,if=virtio,index=0,media=disk

4. login vm0, got VFs pci device id in vm0, assume they are 00:06.0 & 00:07.0, bind them to igb_uio driver::

    modprobe uio
    insmod igb_uio.ko
    ./tools/dpdk_nic_bind.py --bind=igb_uio 00:06.0 00:07.0

5. Turn on testpmd and set mac forwarding mode::

    ./testpmd -c 0xf -n 4 -- -i --portmask=0x3 --tx-offloads=0x0

    testpmd> set fwd mac
    testpmd> start

6. get mac address of VF0 and use it as dest mac, using scapy to send 2000 packets from tester::

    sendp(Ether(src='tester_mac', dst='vm_port0_mac')/IP()/UDP()/Raw(load='XXXXXXXXXXXXXXXXXX'), iface="tester_nic")

7. verify the packets can be received by VF1,As follows::

    ######################## NIC statistics for port 0  ########################
    RX-packets: 2000       RX-missed: 0          RX-bytes:  120000
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 0          TX-errors: 0          TX-bytes:  0

    Throughput (since last show)
    Rx-pps:          634
    Tx-pps:            0
    ############################################################################
    ######################## NIC statistics for port 1  ########################
    RX-packets: 0          RX-missed: 0          RX-bytes:  0
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 2000       TX-errors: 0          TX-bytes:  120000

    Throughput (since last show)
    Rx-pps:            0
    Tx-pps:          618
    ############################################################################

8. You cannot see "ixgbe 0000:03:00.0: Malicious event on VF 0 tx:100000 rx:0" by using the "dmesg -c" command on the host::

    dmesg -c | grep 'event'
