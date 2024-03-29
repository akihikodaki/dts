.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2015-2017 Intel Corporation

=============
VF VLAN Tests
=============


The support of VLAN offload features by VF device consists in:

- the filtering of received VLAN packets
- VLAN header stripping by hardware in received [VLAN] packets
- VLAN header insertion by hardware in transmitted packets

Prerequisites
=============

1. Create VF device from PF devices::

     ./dpdk_nic_bind.py --st
     0000:87:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
     0000:87:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=

     If the drive support vf-vlan-pruning flag:
     ethtool --set-priv-flags ens259f0 vf-vlan-pruning on
     ethtool --set-priv-flags ens259f1 vf-vlan-pruning on

     echo 1 > /sys/bus/pci/devices/0000\:87\:00.0/sriov_numvfs
     echo 1 > /sys/bus/pci/devices/0000\:87\:00.1/sriov_numvfs

     ./dpdk_nic_bind.py --st

     0000:87:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
     0000:87:02.0 'XL710/X710 Virtual Function' unused=
     0000:87:0a.0 'XL710/X710 Virtual Function' unused=

2. Detach VFs from the host, bind them to pci-stub driver::

     /sbin/modprobe pci-stub

     using `lspci -nn|grep -i ethernet` got VF device id, for example "8086 154c",

     echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
     echo 0000:87:02.0 > /sys/bus/pci/devices/0000:87:02.0/driver/unbind
     echo 0000:87:02.0 > /sys/bus/pci/drivers/pci-stub/bind

     echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
     echo 0000:87:0a.0 > /sys/bus/pci/devices/0000:87:0a.0/driver/unbind
     echo 0000:87:0a.0 > /sys/bus/pci/drivers/pci-stub/bind

3. Passthrough VFs 87:02.0 & 87:0a.0 to vm0 and start vm0::

     /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
     -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-1.img -vnc :1 \
     -device pci-assign,host=87:02.0,id=pt_0 \
     -device pci-assign,host=87:0a.0,id=pt_1

4. Login vm0 and then bind VF devices to igb_uio driver.::

     ./tools/dpdk_nic_bind.py --bind=igb_uio 00:04.0 00:05.0

5. Start testpmd, set it in rxonly mode and enable verbose output:

 if test IAVF, start up VF port::

     dpdk-testpmd -c 0x0f -n 4 -a 00:04.0 -a 00:05.0 -- -i --portmask=0x3
     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start

.. note::
   according to dpdk commit 5cbfb386aa3f4c49b3cd9579e4e928cc5ab08d35,if not add parameter "enable-hw-vlan", the vlan
   offload should be disable.the avx2 behavior is not appropriate, the avx2 and avx512 shouldn't have gap on vlan
   offload.this feature will be implemetned in the future.so add parameter "--enable-hw-vlan" in testpmd to test vlan
   strip.

if test DCF, set VF port to dcf and start up::

   Enable kernel trust mode:

       ip link set $PF_INTF vf 0 trust on

   start testpmd with scalar path:

    dpdk-testpmd -c 0x0f -n 4 -a 00:04.0,cap=dcf -a 00:05.0,cap=dcf --force-max-simd-bitwidth=64 -- -i --portmask=0x3

.. note::

   make dcf as full feature pmd is dpdk22.07 feature, and only support E810 series nic.
   the dcf not support vlan offload and change the rx path in vector path when pmd is initialized, so we use
   the scalar path to start testpmd(use param "--force-max-simd-bitwidth=64").


Test Case 1: Add port based vlan on VF
======================================

Linux network configuration tool only set pvid on VF devices.

1. Add pvid on VF0 from PF device::

     ip link set $PF_INTF vf 0 vlan 2

2. Send packet with same vlan id and check VF can receive

3. Send packet without vlan and check VF can't receive

4. Send packet with wrong vlan id and check Vf can't receive

5. Check pf device show correct pvid setting::

     ip link show ens259f0
     ...
     vf 0 MAC 00:00:00:00:00:00, vlan 1, spoof checking on, link-state auto

Test Case 2: Remove port based vlan on VF
=========================================

1. Remove added vlan from PF device::

     ip link set $PF_INTF vf 0 vlan 0

2. Restart testpmd and send packet without vlan and check VF can receive

3. Set packet with vlan id 0 and check VF can receive

4. Set packet with random id 1-4095 and check VF can't receive

Test Case 3: VF port based vlan tx
==================================

1. Add pvid on VF0 from PF device::

     ip link set $PF_INTF vf 0 vlan 2

2. Start testpmd with mac forward mode::


     testpmd> set fwd mac
     testpmd> start

3. Send packet from tester port1 and check packet received by tester port0::

     Check port1 received packet with configured vlan 2

Test Case 3: VF tagged vlan tx
===============================

1. Start testpmd with full-featured tx code path and with mac forward mode::

     dpdk-testpmd -c f -n 3 -- -i
     testpmd> set fwd mac
     testpmd> start

2. Add tx vlan offload on VF0, take care the first param is port::

     testpmd> tx_vlan set 0 1

3. Send packet from tester port1 and check packet received by tester port0::

     Check port- received packet with configured vlan 1

4. Rerun with step2-3 with random vlan and max vlan 4095

Test case4: VF tagged vlan rx
=============================

1. Make sure port based vlan disabled on VF0 and VF1

2. Start testpmd with rxonly mode and parameter "--enable-hw-vlan"::

     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start

.. note::

     parameter "--enable-hw-vlan" not support nic: IXGBE_10G-82599_SFP.

3. Send packet without vlan and check packet received

4. Send packet with vlan 0 and check packet received

5. Add vlan on VF0 from VF driver::

     testpmd> rx_vlan add 1 0

6. Send packet with vlan0/1 and check packet received

7. Rerun with step5-6 with random vlan and max vlan 4095

8. Remove vlan on VF0::

     rx_vlan rm 1 0

9. Send packet with vlan 0 and check packet received

10. Send packet without vlan and check packet received

11. Send packet with vlan 1 and check packet can't received

Test case5: VF Vlan strip test
==============================

1. Start testpmd with mac forward mode and parameter "--enable-hw-vlan"::

     testpmd> set fwd mac
     testpmd> set verbose 1
     testpmd> start

.. note::

     parameter "--enable-hw-vlan" not support nic: IXGBE_10G-82599_SFP.

2. Add tagged vlan 1 on VF0::

     testpmd> rx_vlan add 1 0

3. Disable VF0 vlan strip and sniff packet on tester port1::

     testpmd> vlan set strip off 0

4. Set packet from tester port0 with vlan 1 and check sniffed packet has vlan

5. Enable vlan strip on VF0 and sniff packet on tester port1::

     testpmd> vlan set strip on 0

6. Send packet from tester port0 with vlan 1 and check sniffed packet without vlan

7. Send packet from tester port0 with vlan 0 and check sniffed packet without vlan

8. Rerun with step 2-8 with random vlan and max vlan 4095
