.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2015-2019 Intel Corporation

=================
VF PF Reset Tests
=================

   The scenario is kernel PF + DPDK VF
   The suit support NIC: Intel® Ethernet 700 Series, Intel® Ethernet 800 Series

Prerequisites
=============

1. Hardware:

   * Intel® Ethernet 700 Series 4*10G NIC (driver: i40e)
   * tester: ens3f0
   * dut: ens5f0(pf0), ens5f1(pf1)
   * ens3f0 connect with ens5f0 by cable
   * the status of ens5f1 is linked

2. Added command::

     testpmd> port reset (port_id|all)
     "Reset all ports or port_id"

3. Enable pf private flags::

     ethtool --set-priv-flags ens5f0 link-down-on-close on
     ethtool --set-priv-flags ens5f1 link-down-on-close on


Test Case 1: vf reset -- create two vfs on one pf
=================================================

1. Get the pci device id of DUT, for example::

     ./usertools/dpdk-devbind.py -s

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens5f0 drv=i40e
     0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens5f1 drv=i40e

2. Create 2 VFs from 1 PF,and set the VF MAC address at PF0::

     echo 2 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
     ./usertools/dpdk-devbind.py -s

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens5f0 drv=i40e
     0000:81:02.0 'XL710/X710 Virtual Function' unused=
     0000:81:02.1 'XL710/X710 Virtual Function' unused=
     ip link set ens5f0 vf 0 mac 00:11:22:33:44:11
     ip link set ens5f0 vf 1 mac 00:11:22:33:44:12

3. Bind the VFs to dpdk driver::

     ./usertools/dpdk-devbind.py -b vfio-pci 81:02.0 81:02.1

4. Set the VLAN id of VF1 and VF2::

     ip link set ens5f0 vf 0 vlan 1
     ip link set ens5f0 vf 1 vlan 1

5. Run testpmd::

     ./<build_target>/app/dpdk-testpmd -c 0x0f -n 4 -- -i \
     --portmask=0x3
     testpmd> set fwd mac
     testpmd> start
     testpmd> set allmulti all on
     testpmd> set promisc all off
     testpmd> show port info all

     Promiscuous mode: disabled
     Allmulticast mode: enabled

   The status are not different from the default value.

6. Get mac address of one VF and use it as dest mac, using scapy to
   send 1000 random packets from tester, verify the packets can be received
   by one VF and can be forward to another VF correctly::

     scapy
     >>>sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*40)], \
     iface="ens3f0",count=1000)

7. Set pf down::

     ifconfig ens5f0 down

   Send the same 1000 packets with scapy from tester,
   the vf cannot receive any packets, including vlan=0 and vlan=1

8. Set pf up::

     ifconfig ens5f0 up

   Send the same 1000 packets with scapy from tester, verify the packets can be
   received by one VF and can be forward to another VF correctly.

9. Reset the vfs, run the command::

     testpmd> stop
     testpmd> port stop all
     testpmd> port reset all
     testpmd> port start all
     testpmd> start

   Send the same 1000 packets with scapy from tester, verify the packets can be
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

   The info status is consistent to the status before reset.


Test Case 2: vf reset -- create two vfs on one pf, run testpmd separately
=========================================================================

1. Execute step1-step3 of test case 1

2. Start testpmd on two vf ports::

     ./<build_target>/app/dpdk-testpmd -c 0xf -n 4  \
     --socket-mem 1024,1024 -a 81:02.0 --file-prefix=test1  \
     -- -i --eth-peer=0,00:11:22:33:44:12  \

     ./<build_target>/app/dpdk-testpmd -c 0xf0 -n 4  \
     --socket-mem 1024,1024 -a 81:02.1 --file-prefix=test2  \
     -- -i

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
   vf0 can forward the packet to vf1.

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

     ./<build_target>/app/dpdk-testpmd -c 0x0f -n 4 -- -i \
     --portmask=0x3

4. Start forwarding::

     testpmd> set fwd mac
     testpmd> start

5. Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can fwd the packets normally.

6. Reset pf0 and pf1, don't reset vf0 and vf1, send the packets,
   vfs can fwd the packets normally.

7. Reset vf0 and vf1, send the packets,
   vfs can fwd the packets normally.


Test Case 4: vlan rx restore -- vf reset all ports
==================================================

1. Execute the step1-step3 of test case 1, then start the testpmd::

     ./<build_target>/app/dpdk-testpmd -c 0x0f -n 4 -- -i \
     --portmask=0x3
     testpmd> set fwd mac

2. Add vlan on both ports::

     testpmd> rx_vlan add 1 0
     testpmd> rx_vlan add 1 1
     testpmd> start

   Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can receive the packets and forward it.
   Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=2)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 cannot receive any packets.

3. Reset pf, don't reset vf, send the packets in step2 from tester,
   vfs can receive the packets and forward it.

4. Reset both vfs::

     testpmd> stop
     testpmd> port stop all
     testpmd> port reset all
     testpmd> port start all
     testpmd> start

   Send the packets in step2 from tester,
   vfs can receive the packets and forward it.
   Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=2)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 cannot receive any packets.


test Case 5: vlan rx restore -- vf reset one port
=================================================

1. Execute the step1-step3 of test case 1, then start the testpmd::

     ./<build_target>/app/dpdk-testpmd -c 0x0f -n 4 -- -i  \
     --portmask=0x3
     testpmd> set fwd mac

2. Add vlan on both ports::

     testpmd> rx_vlan add 1 0
     testpmd> rx_vlan add 1 1
     testpmd> start

   Send packets with scapy from tester::

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
     testpmd> port stop 0
     testpmd> port reset 0
     testpmd> port start 0
     testpmd> start
     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can receive and forward the packets.
   Send packets from tester::

     sendp([Ether(dst="00:11:22:33:44:12")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can receive and forward the packets.

4. Reset vf1::

     testpmd> stop
     testpmd> port stop 1
     testpmd> port reset 1
     testpmd> port start 1
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
   Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=2)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 cannot receive any packets.
   Remove vlan 0 on vf1::

     testpmd> rx_vlan rm 0 1
     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 can receive the packets, but vf1 can't transmit the packets.

5. Reset pf, don't reset vf, send packets from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 can receive the packets, but vf1 can't transmit the packets.
   Send packets from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can forward the packets normally.

4. Reset both vfs, send packets from tester::

     testpmd> stop
     testpmd> port stop all
     testpmd> port reset all
     testpmd> port start all
     testpmd> start
     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vf0 can receive the packets, but vf1 can't transmit the packets.
   Send packets from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/Dot1Q(vlan=1)/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

   vfs can forward the packets normally.


Test Case 7: vlan tx restore
============================

.. note::

   ice nic need set dut tx vf port spoofchk off: ip link set dev {pf_interface} vf {tx_vf} spoofchk off

1. Execute the step1-step3 of test case 1

2. Run testpmd::

     ./<build_target>/app/dpdk-testpmd -c 0x0f -n 4 -- -i \
     --portmask=0x3

3. Add tx vlan offload on VF1 port, take care the first param is port,
   start forwarding::

     testpmd> set fwd mac
     testpmd> vlan set filter on 0
     testpmd> set promisc all off
     testpmd> vlan set strip off 0
     testpmd> set nbport 2
     testpmd> tx_vlan set 1 51
     testpmd> start

4. Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*18)], \
     iface="ens3f0",count=1)

5. Listening the port ens3f0::

     tcpdump -i ens3f0 -n -e -x -v

  check the packet received, the packet is configured with vlan 51

6. Reset the pf, then reset the two vfs,
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

     ./<build_target>/app/dpdk-testpmd -c 0x0f -n 4  \
     -- -i --portmask=0x3

4. Add MAC address to the vf0 ports::

     testpmd> mac_addr add 0 00:11:22:33:44:11
     testpmd> mac_addr add 0 00:11:22:33:44:12

5. Start forwarding::

     testpmd> set promisc all off
     testpmd> set fwd mac
     testpmd> start

6. Send packets with scapy from tester::

     sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)
     sendp([Ether(dst="00:11:22:33:44:12")/IP()/Raw('x'*1000)], \
     iface="ens3f0",count=1000)

  vfs can forward both of the two type packets.

7. Reset pf0 and pf1, don't reset vf0 and vf1, send the two packets,
   vfs can forward both of the two type packets.

8. Reset vf0 and vf1, send the two packets,
   vfs can forward both of the two type packets.


test Case 9: vf reset (two vfs passed through to one VM)
========================================================

1. Create 2 VFs from 1 PF,and set the VF MAC address at PF0::

     echo 2 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
     ./usertools/dpdk-devbind.py -s

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens5f0 drv=i40e
     0000:81:02.0 'XL710/X710 Virtual Function' unused=
     0000:81:02.1 'XL710/X710 Virtual Function' unused=

2. Detach VFs from the host, bind them to pci-stub driver::

     modprobe pci-stub
     ./usertools/dpdk-devbind.py -b pci_stub 81:02.0 81:02.1

   or using the following way::

     virsh nodedev-detach pci_0000_81_02_0;
     virsh nodedev-detach pci_0000_81_02_1;

     ./usertools/dpdk-devbind.py -s

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

     ./usertools/dpdk-devbind.py -b igb_uio 00:05.0 00:05.1
     ./<build_target>/app/dpdk-testpmd -c 0x0f -n 4 \
     -a 00:05.0 -a 00:05.1 -- -i --portmask=0x3

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
   vfs can forward both of the two type packets.

8. Reset vf0 and vf1, send the two packets,
   vfs can forward both of the two type packets.


test Case 10: vf reset (two vfs passed through to two VM)
=========================================================

1. Create 2 VFs from 1 PF,and set the VF MAC address at PF::

     echo 2 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
     ./usertools/dpdk-devbind.py -s

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens5f0 drv=i40e
     0000:81:02.0 'XL710/X710 Virtual Function' unused=
     0000:81:02.1 'XL710/X710 Virtual Function' unused=

2. Detach VFs from the host, bind them to pci-stub driver::

     modprobe pci-stub

   using `lspci -nn|grep -i ethernet` got VF device id, for example "8086 154c"::

     echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
     echo "0000:82:02.0" > /sys/bus/pci/drivers/iavf/unbind
     echo "0000:82:02.0" > /sys/bus/pci/drivers/pci-stub/bind

     echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
     echo "0000:82:02.1" > /sys/bus/pci/drivers/iavf/unbind
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
     ./<build_target>/app/dpdk-testpmd -c 0xf -n 4  \
     -- -i --eth-peer=0,vf1port_macaddr  \

   login vm1, got VF1 pci device id in vm1, assume it's 00:06.0,
   bind the port to igb_uio, then start testpmd on vf1 port::

     ./tools/dpdk_nic_bind.py --bind=igb_uio 00:06.0
     ./<build_target>/app/dpdk-testpmd -c 0xf0 -n 4  \
     -- -i

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
   vf0 can forward both of the two type packets to VF1.

8. Reset vf0 and vf1, send the two packets,
   vf0 can forward both of the two type packets to VF1.

test case 11: pf reset trigger vf reset
=======================================

1. Execute step1-step6 of test case 1.

2. Reset PF::

     echo 1 > /sys/bus/pci/devices/0000:81:00.0/reset

3. Testpmd shows::

     Port 0: reset event
     Port 1: reset event

4. Reset the vfs::

     testpmd> stop
     testpmd> port stop all
     testpmd> port reset all
     testpmd> port start all
     testpmd> start

   Send the same 1000 packets with scapy from tester, verify the packets can be
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

   The info status is consistent to the status before reset.
