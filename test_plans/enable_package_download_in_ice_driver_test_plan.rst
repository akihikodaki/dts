.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

===========================================================
Flexible pipeline package processing on E822 NIC mode Tests
===========================================================

Description
===========

DPDK PMD is able to load flexible pipeline package file,
process the content then program to NIC.

This is very important feature, all Classification and Qos functions
depends on this.

This feature set enabled package downloading to the device. The package is
to be in the /lib/firmware/intel/ice/ddp directory and named ice.pkg.
The package is shared by the kernel driver and the DPDK PMD.

If package download failed, driver need to go to safe mode.
RSS, QINQ, and checksum offload are disabled in safe mode.

Prerequisites
=============

Hardware::

    Ice NIC port*2
    DUT_port_0 <---> Tester_port_0
    DUT_port_1 <---> Tester_port_1

Test case 1: Download the package successfully
==============================================

1. Put the correct ice.pkg to /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg,
   then reboot the server.

2. Start the testpmd::

    ./<build_target>/app/dpdk-testpmd -c 0x3fe -n 6 -- -i --nb-cores=8 --rxq=8 --txq=8 \
    --port-topology=chained

   The testpmd can be started normally without any fail information.

3. Normal forward

   Set forward mode::

    testpmd> set mac fwd
    testpmd> start

   Send an IPV4 packet from Tester_port_0,
   Tester_port_1 can receive the forwarded packet.
   The forward can run normally.

4. The RSS function run normally.

   set rxonly mode::

    testpmd> set mac rxonly
    testpmd> start

5. Send UPD/TCP/SCTP+IPV4/IPV6 packets with packet generator
   with different IPV4/IPV6 address or TCP/UDP/SCTP ports,
   the packets can be distributed to different rx queues.

Test case 2: Driver enters Safe Mode successfully
=================================================

1. Server power on, then put a new ice.pkg to
   /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg.
   Make sure the new ice.pkg is different with the original one.

2. Start testpmd::

    ./<build_target>/app/dpdk-testpmd -c 0x3fe -n 6 \
    -a PORT0_PCI,safe-mode-support=1 -a PORT1_PCI,safe-mode-support=1 \
    -- -i --nb-cores=8 --rxq=8 --txq=8 --port-topology=chained

   There will be an error reported::

    ice_dev_init(): Failed to load the DDP package,Entering Safe Mode

   The driver need to go to safe mode.

3. Normal forward

   Set forward mode::

    testpmd> set mac fwd
    testpmd> start

   Send an IPV4 packet from Tester_port_0,
   Tester_port_1 can receive the forwarded packet.
   The forward can run normally.

4. The RSS function doesn't work.

   set rxonly mode::

    testpmd> set mac rxonly
    testpmd> start

5. Send UPD/TCP/SCTP+IPV4/IPV6 packets with packet generator
   with different IPV4/IPV6 address or TCP/UDP/SCTP ports,
   the packets can be only distributed to rx queue 0.

Test case 3: Driver enters Safe Mode failed
===========================================

1. Server power on, then put a new ice.pkg to
   /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg.
   Make sure the new ice.pkg is different with the original one.

2. Start testpmd::

    ./<build_target>/app/dpdk-testpmd -c 0x3fe -n 6 -- -i --nb-cores=8 --rxq=8 --txq=8 \
    --port-topology=chained

   There will be an error reported::

    ice_dev_init(): Failed to load the DDP package,Use safe-mode-support=1 to enter Safe Mode

   The driver failed to go to safe mode and testpmd failed to start.


Test Case 4: Check specific package loadding
=============================================

This test case requires 2 Intel E810 NICs

Copy 2 different ``ice.pkg`` into ``/lib/firmware/intel/ice/ddp/``, \
and rename 1 ice.pkg to ice-<interface serial number>.pkg, e.g. ice-8ce1abfffffefd3c.pkg

Get interface's serial number by::

  lspci -vs b1:00.0 #Change to your interface's BDF

For example,
- ``ice.pkg`` version is 1.2.5.1
- ``ice-8ce1abfffffefd3c.pkg`` version is 1.2.100.1

Compile DPDK and testpmd::

  CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static x86_64-native-linuxapp-gcc
  ninja -C x86_64-native-linuxapp-gcc

Launch testpmd with 1 default interface and 1 specific interface::

  ./<build_target>/app/dpdk-testpmd -l 6-9 -n 4 -a 18:00.0 -a b1:00.0 --log-level=8 -- -i

In this case, b1:00.0 interface is specific interface.

Check the initial output log, it shows::

  EAL: PCI device 0000:b1:00.0 on NUMA socket 0
  EAL:   probe driver: 8086:1593 net_ice
  **ice_load_pkg(): pkg to be loaded: 1.2.100.0, ICE COMMS Package**
