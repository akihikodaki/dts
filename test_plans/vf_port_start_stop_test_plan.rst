.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2015-2017 Intel Corporation

========================
VF Port Start Stop Tests
========================

The suit support NIC: Intel® Ethernet 700 Series, Intel® Ethernet 800 Series and Intel® 82599 Gigabit Ethernet Controller.

Prerequisites
=============

Create Two VF interfaces from two kernel PF interfaces, and then attach them to VM. Suppose PF is 0000:04:00.0. Generate 2VFs using commands below and make them in pci-stub mods.

1. Get the pci device id of DUT::

    ./dpdk_nic_bind.py --st
    0000:04:00.0 '82599ES 10-Gigabit SFI/SFP+ Network Connection' if=ens261f0 drv=ixgbe unused=igb_uio

2. Create 2 VFs from 2 PFs::

      echo 2 > /sys/bus/pci/devices/0000\:04\:00.0/sriov_numvfs

   VFs 04:10.0 & 04:10.1 have been created::

      ./dpdk_nic_bind.py --st
      0000:04:00.0 '82599ES 10-Gigabit SFI/SFP+ Network Connection' if=ens261f0 drv=ixgbe unused=
      0000:04:10.0 '82599 Ethernet Controller Virtual Function' if=enp4s16 drv=ixgbevf unused=
      0000:04:10.1 '82599 Ethernet Controller Virtual Function' if=enp4s16f1 drv=ixgbevf unused=

3. Detach VFs from the host, bind them to pci-stub driver::

      /sbin/modprobe pci-stub
      echo "8086 10ed" > /sys/bus/pci/drivers/pci-stub/new_id
      echo 0000:04:10.0 > /sys/bus/pci/devices/0000\:04\:10.0/driver/unbind
      echo 0000:04:10.0 > /sys/bus/pci/drivers/pci-stub/bind
      echo 0000:04:10.1 > /sys/bus/pci/devices/0000\:04\:10.1/driver/unbind
      echo 0000:04:10.1 > /sys/bus/pci/drivers/pci-stub/bind

   or using the following more easy way::

      ./dpdk_nic_bind.py -b pci-stub 04:10.0 04:10.1

   it can be seen that VFs 04:10.0 & 04:10.1 's drv is pci-stub::

      ./dpdk_nic_bind.py --st
      0000:04:00.0 '82599ES 10-Gigabit SFI/SFP+ Network Connection' if=ens261f0 drv=ixgbe unused=vfio-pci
      0000:04:10.0 '82599 Ethernet Controller Virtual Function' if= drv=pci-stub unused=ixgbevf,vfio-pci
      0000:04:10.1 '82599 Ethernet Controller Virtual Function' if= drv=pci-stub unused=ixgbevf,vfio-pci

4. Do not forget bring up PFs::

      ifconfig ens261f0 up

   Passthrough VFs 04:10.0 & 04:10.1 to vm0, and start vm0, you can refer to below command::

      taskset -c 6-12 qemu-system-x86_64 \
      -enable-kvm -m 8192  -smp 6 -cpu host -name dpdk15-vm1 \
      -drive file=/home/image/fedora23.img \
      -netdev tap,id=hostnet1,ifname=tap1,script=/etc/qemu-ifup,vhost=on \
      -device rtl8139,netdev=hostnet1,id=net1,mac=52:54:01:6b:10:61,bus=pci.0,addr=0xa \
      -device pci-assign,bus=pci.0,addr=0x6,host=04:10.0 \
      -device pci-assign,bus=pci.0,addr=0x7,host=04:10.1 \
      -vnc :11 -daemonize

   the /etc/qemu-ifup can be below script, need you to create first::

      #!/bin/sh
      set -x
      switch=br0
      if [ -n "$1" ];then
          /usr/sbin/tunctl -u `whoami` -t $1
          /sbin/ip link set $1 up
          sleep 0.5s
        /sbin/ip link set $1 master $switch
          exit 0
      else
          echo "Error: no interface specified"
      exit 1
      fi

   Set up bridge br0 before create /etc/qemu-ifup, for example::

      cd /etc/sysconfig/network-scripts
      vim ifcfg-enp1s0f0

      HWADDR=00:1e:67:fb:0f:d4
      TYPE=Ethernet
      NAME=enp1s0f0
      ONBOOT=yes
      DEVICE=enp1s0f0
      NM_CONTROLLED=no
      BRIDGE=br0

      vim ifcfg-br0
      TYPE=Bridge
      DEVICE=br0
      ONBOOT=yes
      NM_CONTROLLED=no
      BOOTPROTO=dhcp
      HOSTNAME="dpdk-test58"

   Login vm0, got VFs pci device id in vm0, assume they are 00:06.0 &
   00:07.0, bind them to igb_uio driver, and then start testpmd, set it in
   mac forward mode::

       ./tools/dpdk_nic_bind.py --bind=igb_uio 00:06.0 00:07.0
       ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0f -n 4 -- -i
       testpmd-> set fwd mac
       testpmd-> start

Test Case: port start/stop
==========================

Start send packets from tester , then start/stop ports several times ,verify if it running right.

Commands could be used to start/stop ports refer to below:

Start port::

    testpmd-> port start all

Stop port::

    testpmd-> port stop all

Send IP+UDP packet::

    Ether(dst="0E:CB:F8:FF:4E:02", src="0E:CB:F8:FF:4E:02")/IP(src="127.0.0.2")/UDP()/("X"*46)

Send IP+TCP packet::

    Ether(dst="0E:CB:F8:FF:4E:02", src="0E:CB:F8:FF:4E:02")/IP(src="127.0.0.2")/TCP()/("X"*46)

Send IP+SCTP packet::

    Ether(dst="0E:CB:F8:FF:4E:02", src="0E:CB:F8:FF:4E:02")/IP(src="127.0.0.2")/SCTP()/("X"*46)

Send IPv6+UDP packet::

    Ether(dst="0E:CB:F8:FF:4E:02", src="0E:CB:F8:FF:4E:02")/IP(src="::2")/UDP()/("X"*46)

Send IPv6+TCP packet::

    Ether(dst="0E:CB:F8:FF:4E:02", src="0E:CB:F8:FF:4E:02")/IP(src="::2")/TCP()/("X"*46)
