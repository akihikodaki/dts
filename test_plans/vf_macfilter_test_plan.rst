.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2015-2017 Intel Corporation

===================
VF MAC Filter Tests
===================

The suit support NIC: Intel® Ethernet 700 Series, Intel® Ethernet 800 Series and Intel® 82599 Gigabit Ethernet Controller.

Test Case 1: test_kernel_2pf_2vf_1vm_iplink_macfilter
=====================================================

1. Get the pci device id of DUT, for example::

      ./usertools/dpdk-devbind.py -s

      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=

2. Create 2 VFs from 2 PFs, and set the VF MAC address at PF0::

      echo 1 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
      echo 1 > /sys/bus/pci/devices/0000\:81\:00.1/sriov_numvfs

      ./usertools/dpdk-devbind.py -s
      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=
      0000:81:02.0 'XL710/X710 Virtual Function' unused=
      0000:81:0a.0 'XL710/X710 Virtual Function' unused=

      ip link set ens259f0 vf 0 mac 00:11:22:33:44:55

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

   it can be seen that VFs 81:02.0 & 81:0a.0 's driver is pci-stub.

4. Passthrough VFs 81:02.0 & 81:0a.0 to vm0, and start vm0::

      /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
      -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-1.img -vnc :1 \
      -device pci-assign,host=81:02.0,id=pt_0 \
      -device pci-assign,host=81:0a.0,id=pt_1

5. Login vm0, got VFs pci device id in vm0, assume they are 00:06.0 & 00:07.0,
   bind them to igb_uio driver, and then start testpmd, enable CRC strip,
   disable promisc mode,set it in mac forward mode::

      ./usertools/dpdk-devbind.py --bind=igb_uio 00:06.0 00:07.0

   if test IAVF, start up VF port::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0f -n 4 -a 00:06.0 -a 00:07.0 -- -i --portmask=0x3

      testpmd> port stop all
      testpmd> port config all crc-strip on
      testpmd> port start all
      testpmd> set promisc all off
      testpmd> set fwd mac
      testpmd> start

   if test DCF, set VF port to dcf and start up::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0f -n 4 -a 00:06.0,cap=dcf -a 00:07.0,cap=dcf -- -i --portmask=0x3

.. note::

      make dcf as full feature pmd is dpdk22.07 feature, and only support E810 series nic.

6. Use scapy to send 100 random packets with ip link set MAC to VF, verify the
   packets can be received by one VF and can be forwarded to another VF
   correctly.

7. Also use scapy to send 100 random packets with a wrong MAC to VF, verify
   the packets can't be received by one VF and also can't be forwarded to
   another VF correctly.

Test Case 2: test_kernel_2pf_2vf_1vm_mac_add_filter
===================================================

1. Get the pci device id of DUT, for example::

      ./usertools/dpdk-devbind.py -s

      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=

2. Create 2 VFs from 2 PFs, and don't set the VF MAC address at PF0::

      echo 1 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
      echo 1 > /sys/bus/pci/devices/0000\:81\:00.1/sriov_numvfs

      ./usertools/dpdk-devbind.py -s
      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=
      0000:81:02.0 'XL710/X710 Virtual Function' unused=
      0000:81:0a.0 'XL710/X710 Virtual Function' unused=

3. Detach VFs from the host, bind them to pci-stub driver::

      /sbin/modprobe pci-stub

      using `lspci -nn|grep -i ethernet` to get VF device id, for example "8086 154c",

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

   it can be seen that VFs 81:02.0 & 81:0a.0 's driver is pci-stub.

4. Passthrough VFs 81:02.0 & 81:0a.0 to vm0, and start vm0::

      /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
      -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-1.img -vnc :1 \
      -device pci-assign,host=81:02.0,id=pt_0 \
      -device pci-assign,host=81:0a.0,id=pt_1

5. login vm0, got VFs pci device id in vm0, assume they are 00:06.0 & 00:07.0,
   bind them to igb_uio driver, and then start testpmd, enable CRC strip on
   VF, disable promisc mode, add a new MAC to VF0 and then start::

      ./usertools/dpdk-devbind.py --bind=igb_uio 00:06.0 00:07.0

   if test IAVF, start up VF port::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0f -n 4 -a 00:06.0 -a 00:07.0 -- -i --portmask=0x3

      testpmd> port stop all
      testpmd> port config all crc-strip on
      testpmd> port start all
      testpmd> set promisc all off
      testpmd> mac_addr add 0 00:11:22:33:44:55
      testpmd> set fwd mac
      testpmd> start

   if test DCF, set VF port to dcf and start up::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0f -n 4 -a 00:06.0,cap=dcf -a 00:07.0,cap=dcf -- -i --portmask=0x3

.. note::

      make dcf as full feature pmd is dpdk22.07 feature, and only support E810 series nic.

6. Use scapy to send 100 random packets with current VF0's MAC, verify the
   packets can be received by one VF and can be forwarded to another VF
   correctly.

7. Use scapy to send 100 random packets with new added VF0's MAC, verify the
   packets can be received by one VF and can be forwarded to another VF
   correctly.

8. remove the added mac address.
      testpmd> mac_addr remove 0 00:11:22:33:44:55

9. Use scapy to send 100 random packets to the deleted MAC to VF0, verify the
   packets can't be received by one VF and also can't be forwarded to another
   VF correctly

10. Use scapy to send 100 random packets with a wrong MAC to VF0, verify the
    packets can't be received by one VF and also can't be forwarded to another
    VF correctly.

Test Case 3: test_dpdk_2pf_2vf_1vm_mac_add_filter
===================================================

1. Get the pci device id of DUT, bind them to igb_uio, for example::

      ./usertools/dpdk-devbind.py -s

      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=
      ./usertools/dpdk-devbind.py --bind=igb_uio 0000:81:00.0 0000:81:00.1

2. Create 2 VFs from 2 PFs, and don't set the VF MAC address at PF0::

      echo 1 > /sys/bus/pci/devices/0000\:81\:00.0/max_vfs
      echo 1 > /sys/bus/pci/devices/0000\:81\:00.1/max_vfs

      ./usertools/dpdk-devbind.py -s
      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+'  drv=igb_uio unused=i40e
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+'  drv=igb_uio unused=i40e
      0000:81:02.0 'XL710/X710 Virtual Function' unused=
      0000:81:0a.0 'XL710/X710 Virtual Function' unused=

3. Start testpmd::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 -b 0000:81:02.0 -b 0000:81:0a.0 -- -i

4. Detach VFs from the host, bind them to pci-stub driver::

      /sbin/modprobe pci-stub

      using `lspci -nn|grep -i ethernet` to get VF device id, for example "8086 154c",

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

   it can be seen that VFs 81:02.0 & 81:0a.0 's driver is pci-stub.
5. Passthrough VFs 81:02.0 & 81:0a.0 to vm0, and start vm0::

      /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
      -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-1.img -vnc :1 \
      -device pci-assign,host=81:02.0,id=pt_0 \
      -device pci-assign,host=81:0a.0,id=pt_1

6. login vm0, got VFs pci device id in vm0, assume they are 00:06.0 & 00:07.0,
   bind them to igb_uio driver, and then start testpmd, enable CRC strip on
   VF, disable promisc mode, add a new MAC to VF0 and then start::

      ./usertools/dpdk-devbind.py --bind=igb_uio 00:06.0 00:07.0
      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0f -n 4 -a 00:06.0 -a 00:07.0 -- -i --portmask=0x3

      testpmd> port stop all
      testpmd> port config all crc-strip on
      testpmd> port start all
      testpmd> set promisc all off
      testpmd> mac_addr add 0 00:11:22:33:44:55
      testpmd> set fwd mac
      testpmd> start

7. Use scapy to send 100 random packets with current VF0's MAC, verify the
   packets can be received by one VF and can be forwarded to another VF
   correctly.

8. Use scapy to send 100 random packets with new added VF0's MAC, verify the
   packets can be received by one VF and can be forwarded to another VF
   correctly.

9. remove the added mac address.
      testpmd> mac_addr remove 0 00:11:22:33:44:55

10. Use scapy to send 100 random packets to the deleted MAC to VF0, verify the
    packets can't be received by one VF and also can't be forwarded to another
    VF correctly

11. Use scapy to send 100 random packets with a wrong MAC to VF0, verify the
    packets can't be received by one VF and also can't be forwarded to
    another VF correctly.

Test Case 4: test_dpdk_2pf_2vf_1vm_iplink_macfilter
===================================================

1. Get the pci device id of DUT, bind them to igb_uio, for example::

      ./usertools/dpdk-devbind.py -s

      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=
      ./usertools/dpdk-devbind.py --bind=igb_uio 0000:81:00.0 0000:81:00.1


2. Create 2 VFs from 2 PFs, and set the VF MAC address at PF0::

      echo 1 > /sys/bus/pci/devices/0000\:81\:00.0/max_vfs
      echo 1 > /sys/bus/pci/devices/0000\:81\:00.1/max_vfs

      ./usertools/dpdk-devbind.py -s
      0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+'  drv=igb_uio unused=i40e
      0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+'  drv=igb_uio unused=i40e
      0000:81:02.0 'XL710/X710 Virtual Function' unused=
      0000:81:0a.0 'XL710/X710 Virtual Function' unused=

3. Start testpmd::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 -b 0000:81:02.0 -b 0000:81:0a.0 -- -i
      testpmd>set vf mac addr 0 0 00:11:22:33:44:55

4. Detach VFs from the host, bind them to pci-stub driver::

      /sbin/modprobe pci-stub

      using `lspci -nn|grep -i ethernet` to get VF device id, for example "8086 154c",

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

   it can be seen that VFs 81:02.0 & 81:0a.0 's driver is pci-stub.
5. Passthrough VFs 81:02.0 & 81:0a.0 to vm0, and start vm0::

      /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
      -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-1.img -vnc :1 \
      -device pci-assign,host=81:02.0,id=pt_0 \
      -device pci-assign,host=81:0a.0,id=pt_1

6. Login vm0, got VFs pci device id in vm0, assume they are 00:06.0 & 00:07.0,
   bind them to igb_uio driver, and then start testpmd, enable CRC strip,
   disable promisc mode, set it in mac forward mode::

      ./usertools/dpdk-devbind.py --bind=igb_uio 00:06.0 00:07.0
      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0f -n 4 -a 00:06.0 -a 00:07.0 -- -i --portmask=0x3

      testpmd> port stop all
      testpmd> port config all crc-strip on
      testpmd> port start all
      testpmd> set promisc all off
      testpmd> set fwd mac
      testpmd> start

7. Use scapy to send 100 random packets with ip link set MAC to VF, verify the
   packets can be received by one VF and can be forwarded to another VF
   correctly.

8. Also use scapy to send 100 random packets with a wrong MAC to VF, verify
   the packets can't be received by one VF and also can't be forwarded to
   another VF correctly.
