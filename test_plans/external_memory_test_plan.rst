.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2015-2018 Intel Corporation

=========================================
Ability to use external memory test plan
=========================================

Description:
------------
Provide an abstraction for DPDK hugepage allocation, to have a "default" memory
allocator that will allocate hugepages, but also have custom allocator support for
external memory.

Test case 1: IGB_UIO and anonymous memory allocation
-----------------------------------------------------
Bind the ports to IGB_UIO driver

Start testpmd with --mp-alloc=xmem flag::

   ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -- --mp-alloc=xmem -i

Start forward in testpmd

Start send traffic from outside to test the forward function


Test case 2: IGB_UIO and anonymous hugepage memory allocation
--------------------------------------------------------------

Bind the ports to IGB_UIO driver

Start testpmd with --mp-alloc=xmemhuge flag::

   ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -- --mp-alloc=xmemhuge -i

Start forward in testpmd

Start send traffic from outside to test the forward function


Test case 3: VFIO and anonymous memory allocation
--------------------------------------------------
Bind the ports to vfio-pci driver

Start testpmd with --mp-alloc=xmem flag::

   ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -- --mp-alloc=xmem -i

Start forward in testpmd

Start send traffic from outside to test the forward function


Test case 4: VFIO and anonymous hugepage memory allocation
-----------------------------------------------------------
Bind the ports to vfio-pci driver

Start testpmd with --mp-alloc=xmemhuge flag::

   ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -- --mp-alloc=xmemhuge -i

Start forward in testpmd

Start send traffic from outside to test the forward function