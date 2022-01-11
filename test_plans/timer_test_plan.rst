.. Copyright (c) <2010-2017>, Intel Corporation
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

=======================================
Sample Application Tests: Timer Example
=======================================

This example shows how timer can be used in a RTE application. This
program print some messages from different lcores regularly,
demonstrating how to use timers.

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

In the timer example there are two timers.

Timer 0 is periodical, running on the master lcore,
reloaded automatically every second.

Timer 1 is single one, being loaded manually by every second/3 ,
once manually load will switch to next lcore.

Build DPDK and example::

   cd dpdk
   CC=gcc meson --werror -Denable_kmods=True  -Dlibdir=lib --default-library=static x86_64-native-linuxapp-gcc
   ninja -C x86_64-native-linuxapp-gcc -j 50

   meson configure -Dexamples=timer x86_64-native-linuxapp-gcc
   ninja -C x86_64-native-linuxapp-gcc

Usage of application::

  ./examples/dpdk-timer [EAL options]

Where the EAL options are::

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

To find out the mapping of lcores (processor) to core id and socket
(physical id), the command below can be used::

  $ grep "processor\|physical id\|core id\|^$" /proc/cpuinfo

The number of logical core will be used as parameter to the timer example.

Test Case: timer callbacks running on targeted cores
====================================================

To run the example in linuxapp environment::

  ./examples/dpdk-timer -c ffffff

Timer0, every second, on master lcore, reloaded automatically.
The check output as below by every second on master lcore::

  timer0_cb() on lcore 0

Timer1, every second/3, on next lcore, reloaded manually.
The check output as below by every second/3 on master lcore::

  timer1_cb() on lcore 1
  timer1_cb() on lcore 2
  timer1_cb() on lcore 3
  timer1_cb() on lcore 4
        ...
        ...
        ...
  timer1_cb() on lcore 23

Verify the ``timer0_cb`` and ``timer1_cb`` care called properly
on the target cores.

..
   Don't add the accuracy test for timer example.
   It makes no sense if there is no timestamp on the timer callback.
   If it's suitable to have accuracy test in the future,
   a report table will be given.
