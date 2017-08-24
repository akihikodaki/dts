.. Copyright (c) <2015-2017>, Intel Corporation
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

=================
VF PF Reset Tests
=================


Prerequisites
=============

1. Hardware:

   * Fortville 4*10G NIC (driver: i40e)
   * tester: ens3f0
   * dut: ens5f0(pf0), ens5f1(pf1)
   * ens3f0 connect with ens5f0 by cable
   * the status of ens5f1 is linked

2. Added command::

     testpmd> port reset (port_id|all)
     "Reset all ports or port_id"


Test Case 1: vf reset -- create two vfs on one pf
=================================================

1. Got the pci device id of DUT, for example::

     ./dpdk_nic_bind.py --st

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens5f0 drv=i40e
     0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens5f1 drv=i40e

2. Create 2 VFs from 1 PF,and set the VF MAC address at PF0::

     echo 2 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
     ./dpdk_nic_bind.py --st

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens5f0 drv=i40e
     0000:81:02.0 'XL710/X710 Virtual Function' unused=
     0000:81:02.1 'XL710/X710 Virtual Function' unused=
     ip link set ens5f0 vf 0 mac 00:11:22:33:44:11
     ip link set ens5f0 vf 1 mac 00:11:22:33:44:12

3. Bind the VFs to dpdk driver::

     ./tools/dpdk-devbind.py -b vfio-pci 81:02.0 81:02.1

4. Set the VLAN id of VF1 and VF2::

     ip link set ens5f0 vf 0 vlan 1
     ip link set ens5f0 vf 1 vlan 1

5. Run testpmd::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x0f -n 4 -- -i \
     --portmask=0x3 --txqflags=0 --crc-strip
     testpmd> set fwd mac
     testpmd> start
     testpmd> set allmulti all on
     testpmd> set promisc all off
     testpmd> show port info all

     Promiscuous mode: disabled
     Allmulticast mode: enabled

   the status are not different from the default value.

6. Get mac address of one VF and use it as dest mac, using scapy to
   send 1000 random packets from tester, verify the packets can be received
   by one VF and can be forward to another VF correctly::

     scapy
     >>>sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*40)], \
     iface="ens3f0",count=1000)

7. Reset pf::

     ifconfig ens5f0 promisc

   or::

     ifconfig ens5f0 -promisc

8. Vf receive a pf reset message::

     Event type: RESET interrupt on port 0
     Event type: RESET interrupt on port 1

   if don't reset the vf, send the same 1000 packets with scapy from tester,
   the vf cannot receive any packets, including vlan=0 and vlan=1

9. Reset the vfs, run the command::

     testpmd> stop
     testpmd> port reset 0
     testpmd> port reset 1
     testpmd> start

   or just run the command "port reset all"
   send the same 1000 packets with scapy from tester, verify the packets can be
   received by one VF and can be forward to another VF correctly,
   check the port info::

     testpmd> show port info all

     ********************* Infos for port 0  *********************
     MAC address: 00:11:22:33:44:11
     Promiscuous mode: disabled
     Allmulticast mode: enabled

     ********************* Infos for port 1  *********************
     MAC address: 00:11:22:33:44:12
     Promiscuous mode: disabled
     Allmulticast mode: enabled

   the info status is consistent to the status before reset.

Test Case 2: vf reset -- create two vfs on one pf, run testpmd separately
=========================================================================

1. Execute step1-step3 of test case 1

2. Start testpmd on two vf ports::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4  \
     --socket-mem 1024,1024 -w 81:02.0 --file-prefix=test1  \
     -- -i --crc-strip --eth-peer=0,00:11:22:33:44:12  \

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf0 -n 4  \
     --socket-mem 1024,1024 -w 81:02.1 --file-prefix=test2  \
     -- -i --crc-strip

3. Set fwd mode on vf0::

     testpmd> set fwd mac
     testpmd> start

4. Set rxonly mode on vf1::

     testpmd> set fwd rxonly
     testpmd> start

5. Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 can forward the packets to vf1.

6. Reset pf, don't reset vf0 and vf1, send the packets,
   vf0 and vf1 cannot receive any packets.

7. Reset vf0 and vf1, send the packets,
   vf0 can forward the packet to vf1.


Test Case 3: vf reset -- create one vf on each pf
=================================================

1. Create vf0 from pf0, create vf1 from pf1::

     echo 1 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
     echo 1 > /sys/bus/pci/devices/0000\:81\:00.1/sriov_numvfs
     ip link set ens5f0 vf 0 mac 00:11:22:33:44:11
     ip link set ens5f1 vf 0 mac 00:11:22:33:44:12

2. Bind the two vfs to vfio-pci::

     ./usertools/dpdk-devbind.py -b vfio-pci 81:02.0 81:06.0

3. Start one testpmd on two vf ports::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x0f -n 4 -- -i \
     --portmask=0x3 --txqflags=0 --crc-strip

4. Start forwarding::

     testpmd> set fwd mac
     testpmd> start

5. Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can fwd the packets normally.

6. Reset pf0 and pf1, don't reset vf0 and vf1, send the packets,
   vfs cannot receive any packets.

7. Reset vf0 and vf1, send the packets,
   vfs can fwd the packets normally.


Test Case 4: vlan rx restore -- vf reset all ports
==================================================

1. Execute the step1-step3 of test case 1, then start the testpmd::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x0f -n 4 -- -i \
     --portmask=0x3 --txqflags=0 --crc-strip
     testpmd> set fwd mac

2. Add vlan on both ports::

     testpmd> rx_vlan add 1 0
     testpmd> rx_vlan add 1 1
     testpmd> start

   send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can receive the packets and forward it.
   send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=2)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 cannot receive any packets.

3. Reset pf, don't reset vf, send the packets in step2 from tester,
   the vfs cannot receive any packets.

4. Reset both vfs::

     testpmd> stop
     testpmd> port reset all
     testpmd> start

   send the packets in step2 from tester
   vfs can receive the packets and forward it.
   send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=2)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 cannot receive any packets.


test Case 5: vlan rx restore -- vf reset one port
=================================================

1. Execute the step1-step3 of test case 1, then start the testpmd::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x0f -n 4 -- -i  \
     --portmask=0x3 --txqflags=0 --crc-strip
     testpmd> set fwd mac

2. Add vlan on both ports::

     testpmd> rx_vlan add 1 0
     testpmd> rx_vlan add 1 1
     testpmd> start

   send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can receive the packets and forward it.

3. Pf reset, then reset vf0, send packets from tester::

     testpmd> stop
     testpmd> port reset 0
     testpmd> start
     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 can receive the packets, but vf1 can't transmit the packets.
   send packets from tester::

     sendp([Ether(dst="00:11:22:33:44:12")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf1 cannot receive the packets.

4. Reset vf1::

     testpmd> stop
     testpmd> port reset 1
     testpmd> start
     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can receive and forward the packets.


Test Case 6: vlan rx restore -- create one vf on each pf
========================================================

1. Execute the step1-step3 of test case 3

2. Add vlan on both ports::

     testpmd> rx_vlan add 1 0
     testpmd> rx_vlan add 1 1

3. Set forward and start::

     testpmd> set fwd mac
     testpmd> start

4. Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can forward the packets normally.
   send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=2)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 cannot receive any packets.
   remove vlan 0 on vf1::

     testpmd> rx_vlan rm 0 1
     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 can receive the packets, but vf1 can't transmit the packets.

5. Reset pf, don't reset vf, send packets from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   the vfs cannot receive any packets.

4. Reset both vfs, send packets from tester::

     testpmd> stop
     testpmd> port reset all
     testpmd> start
     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 can receive the packets, but vf1 can't transmit the packets.
   send packets from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can forward the packets normally.


Test Case 7: vlan tx restore
============================

1. Execute the step1-step3 of test case 1

2. Run testpmd::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x0f -n 4 -- -i \
     --portmask=0x3 --txqflags=0 --crc-strip

2. Add tx vlan offload on VF1 port, take care the first param is port,
   start forwarding::

     testpmd> set fwd mac
     testpmd> vlan set filter on 0
     testpmd> set promisc all off
     testpmd> vlan set strip off 0
     testpmd> set nbport 2
     testpmd> tx_vlan set 1 51
     testpmd> start

3. Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*18)], \
     iface="ens3f0",count=1)

4. Listening the port ens3f0::

     tcpdump -i ens3f0 -n -e -x -v

  check the packet received, the packet is configured with vlan 51

5. Reset the pf, then reset the two vfs,
   send the same packet with no vlan tag,
   check packets received by tester, the packet is configured with vlan 51.


test Case 8: MAC address restore
================================

1. Create vf0 from pf0, create vf1 from pf1::

     echo 1 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
     echo 1 > /sys/bus/pci/devices/0000\:81\:00.1/sriov_numvfs

2. Bind the two vfs to vfio-pci::

     ./usertools/dpdk-devbind.py -b vfio-pci 81:02.0 81:06.0

3. Start testpmd on two vf ports::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x0f -n 4  \
     -- -i --portmask=0x3 --txqflags=0 --crc-strip

4. Add MAC address to the vf0 ports::

     testpmd> mac_addr add 0 00:11:22:33:44:11
     testpmd> mac_addr add 0 00:11:22:33:44:12

5. Start forwarding::

     testpmd> set fwd mac
     testpmd> start

6. Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

  vfs can forward both of the two type packets.

7. Reset pf0 and pf1, don't reset vf0 and vf1, send the two packets,
   vf0 and vf1 cannot receive any packets.

8. Reset vf0 and vf1, send the two packets,
   vfs can forward both of the two type packets.


test Case 9: vf reset (two vfs passed through to one VM)
========================================================

1. Create 2 VFs from 1 PF,and set the VF MAC address at PF0::

     echo 2 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
     ./dpdk_nic_bind.py --st

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens5f0 drv=i40e
     0000:81:02.0 'XL710/X710 Virtual Function' unused=
     0000:81:02.1 'XL710/X710 Virtual Function' unused=

2. Detach VFs from the host, bind them to pci-stub driver::

     modprobe pci-stub
     ./tools/dpdk_nic_bind.py --bind=pci_stub 81:02.0 81:02.1

   or using the following way::

     virsh nodedev-detach pci_0000_81_02_0;
     virsh nodedev-detach pci_0000_81_02_1;

     ./dpdk_nic_bind.py --st

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens5f0 drv=i40e
     0000:81:02.0 'XL710/X710 Virtual Function' if= drv=pci-stub unused=
     0000:81:02.1 'XL710/X710 Virtual Function' if= drv=pci-stub unused=

   it can be seen that VFs 81:02.0 & 81:02.1 's drv is pci-stub.

3. Passthrough VFs 81:02.0 & 81:02.1 to vm0, and start vm0::

     /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
     -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-1.img -vnc :1 \
     -device pci-assign,host=81:02.0,id=pt_0 \
     -device pci-assign,host=81:02.1,id=pt_1

4. Login vm0, got VFs pci device id in vm0, assume they are 00:05.0 & 00:05.1,
   bind them to igb_uio driver,and then start testpmd::

     ./tools/dpdk_nic_bind.py --bind=igb_uio 00:05.0 00:05.1
     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0x0f -n 4 \
     -w 00:05.0 -w 00:05.1 -- -i --portmask=0x3 --txqflags=0

5. Add MAC address to the vf0 ports, set it in mac forward mode::

     testpmd> mac_addr add 0 00:11:22:33:44:11
     testpmd> mac_addr add 0 00:11:22:33:44:12
     testpmd> set fwd mac
     testpmd> start

6. Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can forward both of the two type packets.

7. Reset pf0 and pf1, don't reset vf0 and vf1, send the two packets,
   vf0 and vf1 cannot receive any packets.

8. Reset vf0 and vf1, send the two packets,
   vfs can forward both of the two type packets.


test Case 10: vf reset (two vfs passed through to two VM)
=========================================================

1. Create 2 VFs from 1 PF,and set the VF MAC address at PF::

     echo 2 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
     ./dpdk_nic_bind.py --st

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens5f0 drv=i40e
     0000:81:02.0 'XL710/X710 Virtual Function' unused=
     0000:81:02.1 'XL710/X710 Virtual Function' unused=

2. Detach VFs from the host, bind them to pci-stub driver::

     modprobe pci-stub

   using `lspci -nn|grep -i ethernet` got VF device id, for example "8086 154c"::

     echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
     echo "0000:82:02.0" > /sys/bus/pci/drivers/i40evf/unbind
     echo "0000:82:02.0" > /sys/bus/pci/drivers/pci-stub/bind

     echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
     echo "0000:82:02.1" > /sys/bus/pci/drivers/i40evf/unbind
     echo "0000:82:02.1" > /sys/bus/pci/drivers/pci-stub/bind

3. Pass through VF0 81:02.0 to vm0, VF1 81:02.1 to vm1::

     taskset -c 20-21 qemu-system-x86_64 \
     -enable-kvm -m 2048 -smp cores=2,sockets=1 -cpu host -name dpdk1-vm0 \
     -device pci-assign,host=0000:81:02.0 \
     -drive file=/home/img/vm1/f22.img \
     -netdev tap,id=ipvm0,ifname=tap1,script=/etc/qemu-ifup \
     -device rtl8139,netdev=ipvm0,id=net1,mac=00:11:22:33:44:11 \
     -vnc :1 -daemonize

     taskset -c 18-19 qemu-system-x86_64 \
     -enable-kvm -m 2048 -smp cores=2,sockets=1 -cpu host -name dpdk1-vm1 \
     -device pci-assign,host=0000:81:02.1 \
     -drive file=/home/img/vm1/f22.img \
     -netdev tap,id=ipvm1,ifname=tap2,script=/etc/qemu-ifup \
     -device rtl8139,netdev=ipvm1,id=net2,mac=00:11:22:33:44:12 \
     -vnc :2 -daemonize

4. Login vm0, got VF0 pci device id in vm0, assume it's 00:05.0,
   bind the port to igb_uio, then start testpmd on vf0 port::

     ./tools/dpdk_nic_bind.py --bind=igb_uio 00:05.0
     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4  \
     -- -i --crc-strip --eth-peer=0,vf1port_macaddr  \

   login vm1, got VF1 pci device id in vm1, assume it's 00:06.0,
   bind the port to igb_uio, then start testpmd on vf1 port::

     ./tools/dpdk_nic_bind.py --bind=igb_uio 00:06.0
     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf0 -n 4  \
     -- -i --crc-strip

5. Add vlan on vf0 in vm0, and set fwd mode::

     testpmd> rx_vlan add 1 0
     testpmd> set fwd mac
     testpmd> start

   add vlan on vf1 in vm1, set rxonly mode::

    testpmd> rx_vlan add 1 0
    testpmd> set fwd rxonly
    testpmd> start

6. Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

  vf0 can forward the packets to vf1.

7. Reset pf, don't reset vf0 and vf1, send the two packets,
   vf0 and vf1 cannot receive any packets.

8. Reset vf0 and vf1, send the two packets,
   vf0 can forward both of the two type packets to VF1.
