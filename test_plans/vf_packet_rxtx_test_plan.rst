.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2015-2017 Intel Corporation

====================
VF Packet RxTX Tests
====================



Test Case 1: VF_packet_IO_kernel_PF_dpdk_VF
===========================================

1. Got the pci device id of DUT, for example::

      ./usertools/dpdk-devbind.py -s

      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=

2. Create 2 VFs from 2 PFs::

      echo 1 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
      echo 1 > /sys/bus/pci/devices/0000\:81\:00.1/sriov_numvfs
      ./usertools/dpdk-devbind.py -s

      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=
      0000:81:02.0 'XL710/X710 Virtual Function' unused=
      0000:81:0a.0 'XL710/X710 Virtual Function' unused=

3. Detach VFs from the host, bind them to pci-stub driver::

      /sbin/modprobe pci-stub

      using `lspci -nn|grep -i ethernet` got VF device id, for example "8086 154c",

      echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
      echo 0000:81:02.0 > /sys/bus/pci/devices/0000:08:02.0/driver/unbind
      echo 0000:81:02.0 > /sys/bus/pci/drivers/pci-stub/bind

      echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
      echo 0000:81:0a.0 > /sys/bus/pci/devices/0000:08:0a.0/driver/unbind
      echo 0000:81:0a.0 > /sys/bus/pci/drivers/pci-stub/bind

   or using the following more easy way::

      virsh nodedev-detach pci_0000_81_02_0;
      virsh nodedev-detach pci_0000_81_0a_0;

      ./usertools/dpdk-devbind.py -s

      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=
      0000:81:02.0 'XL710/X710 Virtual Function' if= drv=pci-stub unused=
      0000:81:0a.0 'XL710/X710 Virtual Function' if= drv=pci-stub unused=

   it can be seen that VFs 81:02.0 & 81:0a.0 's drv is pci-stub.

4. Passthrough VFs 81:02.0 & 81:0a.0 to vm0, and start vm0::

      /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
      -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-1.img -vnc :1 \
      -device pci-assign,host=81:02.0,id=pt_0 \
      -device pci-assign,host=81:0a.0,id=pt_1

5. Login vm0, got VFs pci device id in vm0, assume they are 00:06.0 & 00:07.0, bind them to igb_uio driver,
   and then start testpmd, set it in mac forward mode::

      ./usertools/dpdk-devbind.py -s --bind=igb_uio 00:06.0 00:07.0
      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0f -n 4 -a 00:06.0 -a 00:07.0 \
                                               -- -i --portmask=0x3

      testpmd> set fwd mac
      testpmd> start

6. Get mac address of one VF and use it as dest mac, using scapy to send 2000 random packets from tester,
   verify the packets can be received by one VF and can be forward to another VF correctly.



Test Case 2: VF_packet_IO_dpdk_PF_dpdk_VF
===========================================

1. Got the pci device id of DUT, for example::

      ./usertools/dpdk-devbind.py -s

      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=

2. bind pf to igb_uio and Create 2 VFs from 2 PFs::

      ./usertools/dpdk-devbind.py --bind=igb_uio 0000:81:00.0 0000:81:00.1
      echo 1 > /sys/bus/pci/devices/0000\:81\:00.0/max_vfs
      echo 1 > /sys/bus/pci/devices/0000\:81\:00.1/max_vfs

3. Detach VFs from the host, bind them to pci-stub driver::

      /sbin/modprobe pci-stub

      using `lspci -nn|grep -i ethernet` got VF device id, for example "8086 154c",

      echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
      echo 0000:81:02.0 > /sys/bus/pci/devices/0000:08:02.0/driver/unbind
      echo 0000:81:02.0 > /sys/bus/pci/drivers/pci-stub/bind

      echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
      echo 0000:81:0a.0 > /sys/bus/pci/devices/0000:08:0a.0/driver/unbind
      echo 0000:81:0a.0 > /sys/bus/pci/drivers/pci-stub/bind

   or using the following more easy way::

      virsh nodedev-detach pci_0000_81_02_0;
      virsh nodedev-detach pci_0000_81_0a_0;

      ./usertools/dpdk-devbind.py -s

      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=
      0000:81:02.0 'XL710/X710 Virtual Function' if= drv=pci-stub unused=
      0000:81:0a.0 'XL710/X710 Virtual Function' if= drv=pci-stub unused=

   it can be seen that VFs 81:02.0 & 81:0a.0 's drv is pci-stub.
4. Start testpmd on host::

       ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3e -n 4 -b 0000:81:02.0 -b 0000:81:0a.0 -- -i

5. Passthrough VFs 81:02.0 & 81:0a.0 to vm0, and start vm0::

      /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
      -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-1.img -vnc :1 \
      -device pci-assign,host=81:02.0,id=pt_0 \
      -device pci-assign,host=81:0a.0,id=pt_1

6. Login vm0, got VFs pci device id in vm0, assume they are 00:06.0 & 00:07.0, bind them to igb_uio driver,
   and then start testpmd, set it in mac forward mode::

      ./usertools/dpdk-devbind.py --bind=igb_uio 00:06.0 00:07.0
      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0f -n 4 -a 00:06.0 -a 00:07.0 \
                                               -- -i

      testpmd> set fwd mac
      testpmd> start

7. Get mac address of one VF and use it as dest mac, using scapy to send 2000 random packets from tester,
   verify the packets can be received by one VF and can be forward to another VF correctly.

Test Case 3: pf dpdk vf reset
===========================================
this case pf in dpdk
===========================================

1. Got the pci device id of DUT, for example::

      ./usertools/dpdk-devbind.py -s

      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=

2. bind pf to igb_uio and Create 3 VFs from pf0::

      ./usertools/dpdk-devbind.py --bind=igb_uio 0000:81:00.0
      echo 3 > /sys/bus/pci/devices/0000\:81\:00.0/max_vfs


3. Detach VFs from the host, bind them to pci-stub driver::

      /sbin/modprobe pci-stub

      using `lspci -nn|grep -i ethernet` got VF device id, for example "8086 154c",

      echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
      echo 0000:81:02.0 > /sys/bus/pci/devices/0000:08:02.0/driver/unbind
      echo 0000:81:02.0 > /sys/bus/pci/drivers/pci-stub/bind

      echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
      echo 0000:81:02.1 > /sys/bus/pci/devices/0000:08:02.1/driver/unbind
      echo 0000:81:02.1 > /sys/bus/pci/drivers/pci-stub/bind

      echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
      echo 0000:81:02.2 > /sys/bus/pci/devices/0000:08:02.2/driver/unbind
      echo 0000:81:02.2 > /sys/bus/pci/drivers/pci-stub/bind


   it can be seen that VFs 81:02.0 & 81:02.1 & 81:02.2 's drv is pci-stub.
4. Start testpmd on host::

       ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x600000000006 -n 4 -b 0000:81:02.0 -b 0000:81:02.1 -b 0000:81:02.2 -- -i

5. Passthrough VFs 81:02.0 & 81:02.1 to vm0, and start vm0::

      /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
      -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-1.img -vnc :1 \
      -device pci-assign,host=81:02.0,id=pt_0 \
      -device pci-assign,host=81:02.1,id=pt_1
6. Passthrough VFs 81:02.2  to vm1, and start vm1::

      /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
      -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-2.img -vnc :2 \
      -device pci-assign,host=81:02.2,id=pt_0

7. Login vm0 and vm1, got VFs pci device id in vm0 and vm1, assume they are 00:04.0 & 00:05.0 on vm0,00:04.0 on vm1, bind them to igb_uio driver,for vm0::

      ./usertools/dpdk-devbind.py --bind=igb_uio 00:04.0 00:05.0
      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 1  -- -i
      testpmd> set fwd mac
      testpmd> start
8. On vm 1::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 1  -- -i

9. On vm0::

      testpmd>clear port stats all

10. Tester loop send packet to vf0 on vm0

11. On vm1 loop start stop port 1000 times::

      testpmd>port stop all
      testpmd>port start all

12. Tester stop send packet

13. On vm0,check port stats,verify vf0 vf1 can receive packet ,no error


Test Case 4: pf kernel vf reset
===========================================
this case pf in kernel
===========================================

1. Got the pci device id of DUT, for example::

      ./usertools/dpdk-devbind.py -s

      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=

2. bind pf to igb_uio and Create 3 VFs from pf0::

      echo 3 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_nums


3. Detach VFs from the host, bind them to pci-stub driver::

      /sbin/modprobe pci-stub

      using `lspci -nn|grep -i ethernet` got VF device id, for example "8086 154c",

      echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
      echo 0000:81:02.0 > /sys/bus/pci/devices/0000:08:02.0/driver/unbind
      echo 0000:81:02.0 > /sys/bus/pci/drivers/pci-stub/bind

      echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
      echo 0000:81:02.1 > /sys/bus/pci/devices/0000:08:02.1/driver/unbind
      echo 0000:81:02.1 > /sys/bus/pci/drivers/pci-stub/bind

      echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
      echo 0000:81:02.2 > /sys/bus/pci/devices/0000:08:02.2/driver/unbind
      echo 0000:81:02.2 > /sys/bus/pci/drivers/pci-stub/bind


   it can be seen that VFs 81:02.0 & 81:02.1 & 81:02.2 's drv is pci-stub.

4. Passthrough VFs 81:02.0 & 81:02.1 to vm0, and start vm0::

      /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
      -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-1.img -vnc :1 \
      -device pci-assign,host=81:02.0,id=pt_0 \
      -device pci-assign,host=81:02.1,id=pt_1
5. Passthrough VFs 81:02.2  to vm1, and start vm1::

      /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
      -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-2.img -vnc :2 \
      -device pci-assign,host=81:02.2,id=pt_0

6. Login vm0 and vm1, got VFs pci device id in vm0 and vm1, assume they are 00:04.0 & 00:05.0 on vm0,00:04.0 on vm1, bind them to igb_uio driver,for vm0::

      ./usertools/dpdk-devbind.py --bind=igb_uio 00:04.0 00:05.0
      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 1  -- -i
      testpmd> set fwd mac
      testpmd> start
7. On vm 1::
      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 1  -- -i

8. On vm0::

        testpmd>clear port stats all

9. Tester loop send packet to vf0 on vm0

10. On vm1 loop start stop port 1000 times::

      testpmd>port stop all
      testpmd>port start all

11. Tester stop send packet

12. On vm0,check port stats,verify vf0 vf1 can receive packet ,no error
