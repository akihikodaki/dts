.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2019 Intel Corporation

================
VM hotplug Tests
================

Description
===========
Hotplug requires to let users plug out/in the NIC during runtime. The DPDK
software should handle that well without any crash or similar. That
means the interrupt event reporting needed to support that.

Note, this feature is about to fix the gap of passive SR-IOV live migration
by failsafe PMD. So "plug out/in the NIC" typically does not the case that
physically plug out/in a NIC from/to server, it should be case that remove/add
a qemu device from/to a VM.

Hardware
========
Ixgbe and i40e NICs

Note
====
Known issue for UIO in dpdk/doc/guides/rel_notes/known_issues.rst as below,
This test plan only test VFIO scenario.

Kernel crash when hot-unplug igb_uio device while DPDK application is running
-----------------------------------------------------------------------------

**Description**:
   When device has been bound to igb_uio driver and application is running,
   hot-unplugging the device may cause kernel crash.

**Reason**:
   When device is hot-unplugged, igb_uio driver will be removed which will destroy UIO resources.
   Later trying to access any uio resource will cause kernel crash.

**Resolution/Workaround**:
   If using DPDK for PCI HW hot-unplug, prefer to bind device with VFIO instead of IGB_UIO.

**Affected Environment/Platform**:
    ALL.

**Driver/Module**:
   ``igb_uio`` module.


Test Case: one device
=====================
Bind host PF port 0 to vfio_pci::

    modprobe vfio_pci
    ./usertools/dpdk-devbind.py -b vfio_pci 18:00.0

Passthrough PF and start qemu script as below, using “-monitor stdio”
will send the monitor to the standard output::

    taskset -c 0-7 qemu-system-x86_64 -enable-kvm \
    -m 4096 -cpu host -smp 8 -name qemu-vm1 \
    -monitor stdio \
    -drive file=/home/vm_b/ubuntu-16.04_test_vfio.img \
    -device vfio-pci,host=0000:18:00.0,id=dev1 \
    -netdev tap,id=hostnet1,ifname=tap1,script=/etc/qemu-ifup,downscript=/etc/qemu-ifdown,vhost=on \
    -device rtl8139,netdev=hostnet1,id=net0,mac=00:00:00:14:c4:31,bus=pci.0,addr=0x1f \
    -vnc :5

Log in VM, bind passthrough port 0 to vfio-pci::

    modprobe -r vfio_iommu_type1
    modprobe -r vfio
    modprobe vfio enable_unsafe_noiommu_mode=1
    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 00:03.0

Start testpmd with "--hot-plug" enable, set rxonly forward mode
and enable verbose output::

    ./dpdk-testpmd -c f -n 4 -- -i --hot-plug
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

Send packets from tester, check RX could work successfully

Set txonly forward mode, send packet from testpmd, check TX could
work successfully::

    testpmd> set fwd txonly
    testpmd> start

Remove device from qemu interface::

   (qemu) device_del dev1

Check device is removed, no system hange and core dump::

   ./usertools/dpdk-devbind.py -s

Add device from qemu interface::

    (qemu) device_add vfio-pci,host=18:00.0,id=dev1

Check driver adds the device, bind port to vfio-pci

Attach the VF from testpmd::

    testpmd> port attach 00:03.0
    testpmd> port start all

Check testpmd adds the device successfully, no hange and core dump

Check RX/TX could work successfully

Repeat above steps for 3 times

Test Case: one device + reset
=============================
Bind host PF port 0 to vfio_pci::

    modprobe vfio_pci
    ./usertools/dpdk-devbind.py -b vfio_pci 18:00.0

Log in VM, passthrough PF and start qemu script same as above

Bind passthrough port 0 to vfio-pci::

    modprobe -r vfio_iommu_type1
    modprobe -r vfio
    modprobe vfio enable_unsafe_noiommu_mode=1
    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 00:03.0

Start testpmd with "--hot-plug" enable, set rxonly forward mode
and enable verbose output::

    ./dpdk-testpmd -c f -n 4 -- -i --hot-plug
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

Send packets from tester, check RX could work successfully

Set txonly forward mode, send packet from testpmd, check TX could
work successfully::

    testpmd> set fwd txonly
    testpmd> start

Remove device from qemu interface::

   (qemu) device_del dev1

Quit testpmd

Check device is removed, no system hange and core dump::

   ./usertools/dpdk-devbind.py -s

Add device from qemu interface::

    (qemu) device_add vfio-pci,host=18:00.0,id=dev1

Check driver adds the device, bind port to vfio-pci

Restart testpmd

Check testpmd adds the device successfully, no hange and core dump

Check RX/TX could work successfully

Repeat above steps for 3 times


Test Case: two/multi devices
============================
Bind host PF port 0 and port 1 to vfio_pci::

    modprobe vfio_pci
    ./usertools/dpdk-devbind.py -b vfio_pci 18:00.0 18:00.1

Passthrough PFs and start qemu script as below, using “-monitor stdio”
will send the monitor to the standard output::

    taskset -c 0-7 qemu-system-x86_64 -enable-kvm \
    -m 4096 -cpu host -smp 8 -name qemu-vm1 \
    -monitor stdio \
    -drive file=/home/vm_b/ubuntu-16.04_test_vfio.img \
    -device vfio-pci,host=0000:18:00.0,id=dev1 \
    -device vfio-pci,host=0000:18:00.1,id=dev2 \
    -netdev tap,id=hostnet1,ifname=tap1,script=/etc/qemu-ifup,downscript=/etc/qemu-ifdown,vhost=on \
    -device rtl8139,netdev=hostnet1,id=net0,mac=00:00:00:14:c4:31,bus=pci.0,addr=0x1f \
    -vnc :5

Log in VM, bind passthrough port 0 and port 1 to vfio-pci::

    modprobe -r vfio_iommu_type1
    modprobe -r vfio
    modprobe vfio enable_unsafe_noiommu_mode=1
    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 00:03.0 00:04.0

Start testpmd with "--hot-plug" enable, set rxonly forward mode
and enable verbose output::

    ./dpdk-testpmd -c f -n 4 -- -i --hot-plug
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

Send packets from tester, check RX could work successfully
Set txonly forward mode, send packet from testpmd, check TX could
work successfully::

    testpmd> set fwd txonly
    testpmd> start

Remove device 1 and device 2 from qemu interface::

   (qemu) device_del dev1
   (qemu) device_del dev2

Check devices are removed, no system hange and core dump::

   ./usertools/dpdk-devbind.py -s

Add devices from qemu interface::

    (qemu) device_add vfio-pci,host=18:00.0,id=dev1
    (qemu) device_add vfio-pci,host=18:00.1,id=dev2

Check driver adds the devices, bind port to vfio-pci

Attach the VFs from testpmd::

    testpmd> port attach 00:03.0
    testpmd> port attach 00:04.0
    testpmd> port start all

Check testpmd adds the devices successfully, no hange and core dump

Check RX/TX could work successfully

Repeat above steps for 3 times


Test Case: two/multi devices + reset
====================================
Bind host PF port 0 and port 1 to vfio_pci::

    modprobe vfio_pci
    ./usertools/dpdk-devbind.py -b vfio_pci 18:00.0 18:00.1

Passthrough PFs and start qemu script same as above

Log in VM, bind passthrough port 0 and port 1 to vfio-pci::

    modprobe -r vfio_iommu_type1
    modprobe -r vfio
    modprobe vfio enable_unsafe_noiommu_mode=1
    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 00:03.0 00:04.0

Start testpmd with "--hot-plug" enable, set rxonly forward mode
and enable verbose output::

    ./dpdk-testpmd -c f -n 4 -- -i --hot-plug
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

Send packets from tester, check RX could work successfully

Set txonly forward mode, send packets from testpmd, check TX could
work successfully::

    testpmd> set fwd txonly
    testpmd> start

Remove device 1 and device 2 from qemu interface::

   (qemu) device_del dev1
   (qemu) device_del dev2

Quit testpmd

Check devices are removed, no system hange and core dump::

   ./usertools/dpdik-devbind.py -s

Add devices from qemu interface::

    (qemu) device_add vfio-pci,host=18:00.0,id=dev1
    (qemu) device_add vfio-pci,host=18:00.1,id=dev2

Check driver adds the devices, bind ports to vfio-pci

Restart testpmd

Check testpmd adds the devices successfully, no hange and core dump

Check RX/TX could work successfully

Repeat above steps for 3 times
