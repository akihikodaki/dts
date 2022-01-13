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

====================
DPDK IAVF API Tests
====================

Intel Adaptive Virtual Function(IAVF)

Hardwares
=======================
I40E driver NIC (Fortville XXV710, Fortville Spirit, Fortville Eagle)


Prerequisites
=======================
1. Configure PF and VF::

    modprobe uio;
    insmod x86_64-native-linuxapp-gcc/kmod/igb_uio.ko;
    ./usertools/dpdk-devbind.py --bind=igb_uio 08:00.0 08:00.1

    echo 1 > /sys/bus/pci/devices/0000\:08\:00.0/max_vfs
    echo 1 > /sys/bus/pci/devices/0000\:08\:00.1/max_vfs

2. Start testpmd on host to configure VF ports' mac::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 1-5 -n 4  -- -i

    testpmd>set vf mac addr 0 0 00:12:34:56:78:01
    testpmd>set vf mac addr 1 0 00:12:34:56:78:02

3. Pass through VF 09:02.0 and 09:0a.0 to VM0::

    taskset -c 24,25 qemu-system-x86_64  \
    -name vm0 -enable-kvm -pidfile /tmp/.vm0.pid -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
    -device e1000,netdev=nttsip1  -netdev user,id=nttsip1,hostfwd=tcp:10.240.176.247:6000-:22 \
    -device vfio-pci,host=0000:09:02.0,id=pt_0 -device vfio-pci,host=0000:09:0a.0,\
    id=pt_1 -cpu host -smp 2 -m 10240 -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
    -device virtio-serial -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :1 \
    -drive file=/home/image/sriov-fc25-1.img,format=raw,if=virtio,index=0,media=disk

4. Bind VF to igb_uio or vfio-pic in VM::

    ./usertools/dpdk-devbind.py --bind=igb_uio 00:04.0 00:05.0
    or
    ./usertools/dpdk-devbind.py --bind=vfio-pci 00:04.0 00:05.0

Test case: VF basic RX/TX
---------------------------
1. Start testpmd on VM::

      ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x3 -n 1  -- -i

2. Check and verify packets which received and forwarded


Test Cases: VF mac filter
=========================

Start testpmd on VM::

      ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x3 -n 1  -- -i

Test Case: unicast test
------------------------
::

    testpmd>set promisc all off
    testpmd>set allmulti all off
    testpmd>start

    testpmd>mac_addr set 0 00:12:34:56:78:03

disable promisc mode, verify VF packet rx/tx can work fine with the specific mac addr.

Test Case: multicast test
-------------------------
::

    testpmd>set promisc all off
    testpmd>set allmulti all off
    testpmd>start

Send packet with multicast MAC 01:80:C2:00:00:08, and check VF can not receive the packet.
::

    testpmd>set allmulti all on

Send packet with multicast MAC 01:80:C2:00:00:08, and check VF can receive the packet.

Test Case: broadcast test
-------------------------
::

    testpmd>set promisc all off
    testpmd>start

Send packets with broadcast address ff:ff:ff:ff:ff:ff, and check VF can receive the packet

Test Case: promiscuous mode
---------------------------
::

    testpmd>set promisc all on
    testpmd>start

Send packet that different with vf mac, check packets can be received.

Test Cases: VF VLAN feature vlan filter only work with promisc mode off
==========================================================================

Start testpmd on VM::

      ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x3 -n 1  -- -i

Test Case: vlan filter
---------------------------
::

    testpmd>port stop all
    testpmd>set promisc all off
    testpmd>vlan set filter off 0
    testpmd>vlan set filter off 1
    testpmd>vlan set strip off 0
    testpmd>vlan set strip off 1

    testpmd>vlan set filter on 0
    testpmd>set fwd mac
    testpmd>port start all
    testpmd>start

packet with vlan can not be received, packet without vlan packet can be received.

Test Case: rx_vlan
---------------------------
::

    testpmd>port stop all
    testpmd>set promisc all off
    testpmd>vlan set filter off 0
    testpmd>vlan set filter off 1
    testpmd>vlan set strip off 0
    testpmd>vlan set strip off 1

    testpmd>vlan set filter on 0
    testpmd>rx_vlan add 20 0
    testpmd>set fwd mac
    testpmd>port start all
    testpmd>start

packet vlan id equal to 20 can be received, packet vlan id not equal to 20 packet can be not received.

Test Case: tx_vlan
---------------------------
::

    testpmd>port stop all
    testpmd>set promisc all on
    testpmd>set fwd mac
    testpmd>vlan set filter off 0
    testpmd>vlan set filter off 1
    testpmd>vlan set strip off 0
    testpmd>vlan set strip off 1
    testpmd>tx_vlan set 1 20
    testpmd>port start all
    testpmd>start

packet out from VF contain the vlan tag and vlan id equal to 20.

Test Case: vlan strip
---------------------------
::

    testpmd>port stop all
    testpmd>set promisc all on
    testpmd>set fwd mac
    testpmd>vlan set filter off 0
    testpmd>vlan set filter off 1
    testpmd>vlan set strip off 0
    testpmd>vlan set strip off 1
    testpmd>vlan set strip on 0
    testpmd>port start all
    testpmd>start

send a packet with vlan tag, packet out from VF not contain the vlan tag.

Test Case: vlan promisc mode
-----------------------------
::

    testpmd>port stop all
    testpmd>vlan set filter off 0
    testpmd>vlan set filter off 1
    testpmd>vlan set strip off 0
    testpmd>vlan set strip off 1

    testpmd>set promisc all on
    testpmd>set fwd mac
    testpmd>port start all
    testpmd>start

send packet with vlan or without vlan, both can be received and forwarded.

Test Cases: VF jumboframe
==============================

Ensure Tester's ports support sending jumboframe::

    ifconfig 'tester interface' mtu 9000


Test Case: Check that no jumbo frame support
--------------------------------------------
::

    Launch testpmd for VF ports without enabling jumboframe option

        ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1  -- -i

        testpmd>set fwd mac
        testpmd>start

packet less than the standard maximum frame (1518) can be received.
packet more than the standard maximum frame (1518) can not be received.

Test Case: Check that with jumbo frames support
------------------------------------------------
::

    Launch testpmd for VF ports with jumboframe option

        ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1  -- -i --max-pkt-len=3000 --tx-offloads=0x8000

        testpmd>set fwd mac
        testpmd>start

packet lengths greater than the standard maximum frame (1518) and
lower or equal to the maximum frame length can be received.
Check that packets larger than the configured maximum packet length are
dropped by the hardware.

**Note the following was expected!** packet size > 9001,  not forward , but RX-packets: counter increased

Test Cases: VF rss
====================
Start testpmd on VM::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1  -- -i --txq=4 --rxq=4

Test Case: test redirection table config
-------------------------------------------
::

    testpmd>port config 0 rss reta (0,0)
    testpmd>port config 0 rss reta (1,1)
    testpmd>port config 0 rss reta (2,2)
    testpmd>port config 0 rss reta (3,3)
    testpmd>port config 0 rss reta (60,0)
    testpmd>port config 0 rss reta (61,1)
    testpmd>port config 0 rss reta (62,2)
    testpmd>port config 0 rss reta (63,3)

    testpmd> port config all rss (all|ip|tcp|udp|sctp|ether|port|vxlan|geneve|nvgre|none)

send different flow type packets to VF port, check packets received by different queues.

Test Cases:VF offload
=======================
Start testpmd on VM::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 1  -- -i

Test Case: enable HW checksum offload
-------------------------------------------
::

    testpmd>port stop all
    testpmd>csum set ip hw 0
    testpmd>csum set udp hw 0
    testpmd>csum set tcp hw 0
    testpmd>csum set sctp hw 0

    testpmd>csum set ip hw 1
    testpmd>csum set udp hw 1
    testpmd>csum set tcp hw 1
    testpmd>csum set sctp hw 1

    testpmd>set fwd csum
    testpmd>set verbose 1

    testpmd>port start all
    testpmd>start

Send packets with incorrect checksum to VF port, verify that the packets
can be received by VF port and checksum error reported,
the packets forwarded by VF port have the correct checksum value.


Test Case: SW checksum, disable HW checksum offload
---------------------------------------------------
::

    testpmd>port stop all
    testpmd>csum set ip sw 0
    testpmd>csum set udp sw 0
    testpmd>csum set tcp sw 0
    testpmd>csum set sctp sw 0

    testpmd>csum set ip sw 1
    testpmd>csum set udp sw 1
    testpmd>csum set tcp sw 1
    testpmd>csum set sctp sw 1

    testpmd>set fwd csum
    testpmd>set verbose 1
    testpmd>port start all
    testpmd>start

Send packets with incorrect checksum to VF port, verify that the packets
can be received by VF port and checksum error reported, the packets
forwarded by VF port have the correct checksum value.


Test Case: tso
-------------------------------------------
::

    testpmd>port stop all
    testpmd>set verbose 1
    testpmd>csum set ip hw 0
    testpmd>csum set udp hw 0
    testpmd>csum set tcp hw 0
    testpmd>csum set sctp hw 0

    testpmd>csum set ip hw 1
    testpmd>csum set udp hw 1
    testpmd>csum set tcp hw 1
    testpmd>csum set sctp hw 1

    testpmd>tso set 800 1
    testpmd>set fwd csum
    testpmd>port start all
    testpmd>start

Send packet which loading size more than 800.
Verify tcpdump packets send out by VF port is split according to tso size.

Test case:  Rx interrupt
============================

Test case: rx interrupt
-----------------------
::

    build l3fwd-power
        meson configure -Dexamples=l3fwd-power x86_64-native-linuxapp-gcc
        ninja -C x86_64-native-linuxapp-gcc

    enable vfio noiommu
        modprobe -r vfio_iommu_type1
        modprobe -r vfio
        modprobe  vfio enable_unsafe_noiommu_mode=1
        cat /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
        modprobe vfio-pci

    start l3fwd power with one queue per port.
        ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 6,7 -n 4  -- \
        -p 0x3 --config '(0,0,6),(1,0,7)'

    Send one packet to VF0 and VF1, check that thread on core6 and core7 waked up::

    L3FWD_POWER: lcore 6 is waked up from rx interrupt on port 0 queue 0
    L3FWD_POWER: lcore 7 is waked up from rx interrupt on port 0 queue 0

    Check the packet has been normally forwarded.

    After the packet forwarded, thread on core6 and core 7 will return to sleep::

    L3FWD_POWER: lcore 6 sleeps until interrupt triggers
    L3FWD_POWER: lcore 7 sleeps until interrupt triggers

    Send packet flows to VF0 and VF1, check that thread on core1 and core2 will
    keep up awake.


Test Cases:  VF veb
=======================

Test Case: veb performance
--------------------------

create 2 VFs from 1 PF, start testpmd with 2VFs individually, verify throughput.

create 2 VFs from 1 PF, and start PF::

    echo 2 > /sys/bus/pci/devices/0000\:08\:00.0/max_vfs;
    ./usertools/dpdk-devbind.py --bind=vfio-pci 09:02.0 09:0a.0

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1,2 -n 4 --socket-mem=1024,1024 --file-prefix=pf -a 08:00.0 -- -i

    testpmd>set vf mac addr 0 0 00:12:34:56:78:01
    testpmd>set vf mac addr 0 1 00:12:34:56:78:02

start testpmd with 2VFs individually::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 3-5 -n 4 --master-lcore=3 --socket-mem=1024,1024 --file-prefix=vf1 \
      -a 09:02.0 -- -i --txq=2 --rxq=2 --rxd=512 --txd=512 --nb-cores=2 --rss-ip --eth-peer=0,00:12:34:56:78:02

    testpmd>set promisc all off
    testpmd>set fwd mac
    testpmd>start

::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-8 -n 4 --master-lcore=6 --socket-mem=1024,1024 --file-prefix=vf2 \
       -a 09:0a.0 -- -i --txq=2 --rxq=2 --rxd=512 --txd=512 --nb-cores=2 --rss-ip

    testpmd>set promisc all off
    testpmd>set fwd mac
    testpmd>start

send traffic and verify throughput.

Test Case: VF performance
============================

Test Case: vector vf performance
---------------------------------

1. config vector=y in config/common_base, and rebuild dpdk

2. start testpmd for PF::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 --socket-mem=1024,1024 --file-prefix=pf \
       -a 08:00.0 -a 08:00.1 -- -i

       testpmd>set vf mac addr 0 0 00:12:34:56:78:01
       testpmd>set vf mac addr 1 0 00:12:34:56:78:02

3. start testpmd for VF::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0f8 -n 4 --master-lcore=3 --socket-mem=1024,1024 --file-prefix=vf \
        -a 09:0a.0 -a 09:02.0 -- -i --txq=2 --rxq=2 --rxd=512 --txd=512 --nb-cores=4 --rss-ip

     testpmd>set promisc all off
     testpmd>set fwd mac
     testpmd>start

4. send traffic and verify throughput

Test Case: scalar/bulk vf performance
-------------------------------------

1. change CONFIG_RTE_LIBRTE_IAVF_INC_VECTOR=n in config/common_base, and rebuild dpdk.
2. repeat test steps 2-4 in above test case: vector vf performance.
