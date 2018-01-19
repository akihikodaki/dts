.. Copyright (c) <2017>, Intel Corporation
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

==========================================================
Niantic ixgbe_get_vf_queue Include Extra Information Tests
==========================================================

Description
===========

VF can get following information in ixgbe driver:

1. Get the TC’s configured by PF for a given VF.
2. Get the User priority to TC mapping information for a given VF.

Prerequisites
=============

1. Hardware:
   Ixgbe
   connect tester to pf with cable.

2. software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. bind the pf to dpdk driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0

   the mac address of 05:00.0 is 00:00:00:00:01:00

4. create 1 vf from pf::

    echo 1 >/sys/bus/pci/devices/0000:05:00.0/max_vfs

5. Detach VF from the host, bind them to pci-stub driver::

    modprobe pci-stub

   using `lspci -nn|grep -i ethernet` got VF device id "8086 10ed", then::

    echo "8086 10ed" > /sys/bus/pci/drivers/pci-stub/new_id
    echo "0000:05:10.0" > /sys/bus/pci/drivers/ixgbevf/unbind
    echo "0000:05:10.0" > /sys/bus/pci/drivers/pci-stub/bind

6. Lauch the VM with the VF PCI passthrough::

    taskset -c 2-5 qemu-system-x86_64 \
    -enable-kvm -m 8192 -smp cores=4,sockets=1 -cpu host -name dpdk1-vm1 \
    -drive file=/home/VM/centOS7_1.img \
    -device pci-assign,host=05:10.0 \
    -netdev tap,id=ipvm1,ifname=tap3,script=/etc/qemu-ifup -device rtl8139,netdev=ipvm1,id=net0,mac=00:00:00:00:00:01 \
    -localtime -vnc :2 -daemonize

7. login VM, get VF's mac adress is 2e:ae:7f:16:6f:e7

Test case 1: DPDK PF, kernel VF, enable DCB mode with TC=4
==========================================================

1. start the testpmd on PF::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 1ffff -n 4 -- -i --rxq=4 --txq=4 --nb-cores=16    
    testpmd> port stop 0
    testpmd> port config 0 dcb vt on 4 pfc off
    testpmd> port start 0

2. check if VF port is linked. if vf port is down, reload the ixgbevf driver::

    rmmod ixgbevf
    modprobe ixgbevf

   then you can see VF information in PF side::

    PMD: VF 0: enabling multicast promiscuous
    PMD: VF 0: disabling multicast promiscuous

3. check VF's queue number::

    ethtool -S ens3

   there is 1 tx queue and 4 rx queues which equals TC number.

4. send packet from tester to VF::

    pkt1 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/Dot1Q(prio=0, vlan=0)/IP()/Raw('x'*20)
    pkt2 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/Dot1Q(prio=1, vlan=0)/IP()/Raw('x'*20)
    pkt3 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/Dot1Q(prio=2, vlan=0)/IP()/Raw('x'*20)
    pkt4 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/Dot1Q(prio=3, vlan=0)/IP()/Raw('x'*20)
    pkt5 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/Dot1Q(prio=4, vlan=0)/IP()/Raw('x'*20)
    pkt6 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/Dot1Q(prio=5, vlan=0)/IP()/Raw('x'*20)
    pkt7 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/Dot1Q(prio=6, vlan=0)/IP()/Raw('x'*20)
    pkt8 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/Dot1Q(prio=7, vlan=0)/IP()/Raw('x'*20)
    pkt9 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/Dot1Q(prio=0, vlan=1)/IP()/Raw('x'*20)
    pkt10 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/IP()/Raw('x'*20)

5. check the packets with different User Priority mapping to TC::

    ethtool -S ens3

   check the NIC statistics to check the packets increasing of different rx queue.
   pkt1 to queue 0, pkt2 to queue 1, pkt3 to queue 2, pkt4 to queue 3,
   pkt5-pkt8 to queue 0, VF can't get pkt9, pkt10 to queue 0.

Test case 2: DPDK PF, kernel VF, disable DCB mode
=================================================

1. start the testpmd on PF::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 1ffff -n 4 -- -i --nb-cores=16

2. check if VF port is linked. if vf port is down, reload the ixgbevf driver::

    rmmod ixgbevf
    modprobe ixgbevf

   then you can see VF information in PF side::

    PMD: VF 0: enabling multicast promiscuous
    PMD: VF 0: disabling multicast promiscuous

3. set vlan insert to vf::

    set vf vlan insert 0 0 1

4. check VF's queue number::

    ethtool -S ens3

   there is 2 tx queues and 2 rx queues as default number.

4. send packet from tester to VF::

    pkt1 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/IP()/Raw('x'*20)
    pkt2 = Ether(dst="2e:ae:7f:16:6f:e7", src="00:02:00:00:00:01")/IP(src="192.168.0.1", dst="192.168.0.3")/UDP(sport=23,dport=24)/Raw('x'*20)

5. check the NIC statistics to verify the different packets mapping to
   different queues according RSS rule::

    ethtool -S ens3

   send 100 pkt1 to VF, all the packets received by queue 0,
   then, send 100 pkt2 to VF, all the packets received by queue 1.
