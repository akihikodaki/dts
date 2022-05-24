.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

=============================================
Sample Application Tests: Hello World Example
=============================================

This example is one of the most simple RTE application that can be
done. The program will just print a "helloworld" message on every
enabled lcore.

Command Usage::

  ./dpdk-helloworld -c COREMASK [-m NB] [-r NUM] [-n NUM]

    EAL option list:
      -c COREMASK: hexadecimal bitmask of cores we are running on
      -m MB      : memory to allocate (default = size of hugemem)
      -n NUM     : force number of memory channels (don't detect)
      -r NUM     : force number of memory ranks (don't detect)
      --huge-file: base filename for hugetlbfs entries
    debug options:
      --no-huge  : use malloc instead of hugetlbfs
      --no-pci   : disable pci
      --no-hpet  : disable hpet
      --no-shconf: no shared config (mmap'd files)


Prerequisites
=============

Support igb_uio and vfio driver, if used vfio, kernel need 3.6+ and enable vt-d in bios.
When used vfio , used "modprobe vfio" and "modprobe vfio-pci" insmod vfio driver, then used
"./tools/dpdk_nic_bind.py --bind=vfio-pci device_bus_id" to bind vfio driver to test driver.

To find out the mapping of lcores (processor) to core id and socket (physical
id), the command below can be used::

  $ grep "processor\|physical id\|core id\|^$" /proc/cpuinfo

The total logical core number will be used as ``helloworld`` input parameters.


Test Case: run hello world on single lcores
===========================================

To run example in single lcore ::

  $ ./dpdk-helloworld -c 1
    hello from core 0

Check the output is exact the lcore 0


Test Case: run hello world on every lcores
==========================================

To run the example in all the enabled lcore ::

  $ ./dpdk-helloworld -cffffff
    hello from core 1
    hello from core 2
    hello from core 3
           ...
           ...
    hello from core 0

Verify the output of according to all the core masks.
