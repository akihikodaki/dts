.. Copyright (c) <2019>, Intel Corporation
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

==============
NTB test plan
==============

The ntb sample application shows how to use ntb rawdev driver.
This sample provides interactive mode to do packet based processing
between two systems.

This sample supports 4 types of packet forwarding mode.

* ``file-trans``: transmit files between two systems. The sample will
  be polling to receive files from the peer and save the file as
  ``ntb_recv_file[N]``, [N] represents the number of received file.
* ``rxonly``: NTB receives packets but doesn't transmit them.
* ``txonly``: NTB generates and transmits packets without receiving any.
* ``iofwd``: iofwd between NTB device and ethdev.
 
Command-line Options
--------------------

The application supports the following command-line options.

* ``--buf-size=N``

  Set the data size of the mbufs used to N bytes, where N < 65536.
  The default value is 2048.

* ``--fwd-mode=mode``

  Set the packet forwarding mode as ``file-trans``, ``txonly``,
  ``rxonly`` or ``iofwd``.

* ``--nb-desc=N``

  Set number of descriptors of queue as N, namely queue size,
  where 64 <= N <= 1024. The default value is 1024.

* ``--txfreet=N``

  Set the transmit free threshold of TX rings to N, where 0 <= N <=
  the value of ``--nb-desc``. The default value is 256.

* ``--burst=N``

  Set the number of packets per burst to N, where 1 <= N <= 32.
  The default value is 32.

* ``--qp=N``

  Set the number of queues as N, where qp > 0.

Using the application
----------------------

The application is console-driven using the cmdline DPDK interface:
 From this interface the available commands and descriptions of what
 they do as as follows:
 
* ``send [filepath]``: Send file to the peer host. Need to be in
  file-trans forwarding mode first.
* ``start``: Start transmission.
* ``stop``: Stop transmission.
* ``show/clear port stats``: Show/Clear port stats and throughput.
* ``set fwd file-trans/rxonly/txonly/iofwd``: Set packet forwarding mode.
* ``quit``: Exit program.

Test Case1: NTB test with file-trans fwd mode using igb_uio 
===========================================================

1. Insmod kernel module and bind Non-Transparent Bridge to igb_uio driver on two host machines separately::

    insmod x86_64-native-linuxapp-gcc/kmod/igb_uio.ko wc_activate=1
    ./usertools/dpdk-devbind.py -b igb_uio ae:00.0

2. Launch ntb_fwd sample on Machine1::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --buf-size=65407
    >set fwd file-trans
    >start

3. Launch ntb_fwd sample on Machine2::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --buf-size=65407
    >set fwd file-trans
    >start

4. Send file from Machine1::

    >send xxx  # [xxx] is srouce absolute path + file

5. Check file can be received on Machine2 fixed path.

Test Case2: NTB test with file-trans fwd mode using vfio-pci
============================================================

1. Insmod kernel module and bind Non-Transparent Bridge to vfio-pci driver on two host machines separately::

    insmod x86_64-native-linuxapp-gcc/kmod/igb_uio.ko
    insmod vfio-pci
    lspci -vv -s ae:00.0
    echo "base=0x39bfa0000000 size=0x400000 type=write-combining" >> /proc/mtrr
    echo "base=0x39bfa0000000 size=0x4000000 type=write-combining" >> /proc/mtrr
    ./usertools/dpdk-devbind.py -b vfio-pci ae:00.0

2. Launch ntb_fwd sample on Machine1::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --buf-size=65407
    >set fwd file-trans

3. Launch ntb_fwd sample on Machine2::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --buf-size=65407
    >set fwd file-trans

4. Send file from Machine1::

    >send xxx  # [xxx] is srouce absolute path + file

5. Check file can be received on Machine2 fixed path.

Test Case3: NTB test with rxonly/txonly fwd mode using igb_uio
==============================================================

1. Insmod kernel module and bind Non-Transparent Bridge to igb_uio driver on two host machines separately::

    insmod x86_64-native-linuxapp-gcc/kmod/igb_uio.ko wc_activate=1
    ./usertools/dpdk-devbind.py -b igb_uio ae:00.0

2. Launch ntb_fwd sample on Machine1::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --buf-size=65407
    >set fwd rxonly
    >start
    >show port stats

3. Launch ntb_fwd sample on Machine2::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --buf-size=65407
    >set fwd txonly
    >start
    >show port stats

4. Check throughput with log info on two machines.

Test Case4: NTB test with rxonly/txonly fwd mode using vfio-pci
==============================================================

1. Insmod kernel module and bind Non-Transparent Bridge to vfio-pci driver on two host machines separately::

    insmod x86_64-native-linuxapp-gcc/kmod/igb_uio.ko
    insmod vfio-pci
    lspci -vv -s ae:00.0
    echo "base=0x39bfa0000000 size=0x400000 type=write-combining" >> /proc/mtrr
    echo "base=0x39bfa0000000 size=0x4000000 type=write-combining" >> /proc/mtrr
    ./usertools/dpdk-devbind.py -b vfio-pci ae:00.0

2. Launch ntb_fwd sample on Machine1::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --buf-size=65407
    >set fwd rxonly
    >start
    >show port stats

3. Launch ntb_fwd sample on Machine2::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --buf-size=65407
    >set fwd txonly
    >start
    >show port stats

4. Check throughput with log info on two machines.

Test Case5: NTB test with io fwd mode using igb_uio
===================================================
Test flow: TG <-> NIC1 <-> NTB1 <-> NTB2 <-> NIC2 <-> TG

1. Insmod kernel module and bind Non-Transparent Bridge and NIC to igb_uio driver on two host machines separately::

    insmod x86_64-native-linuxapp-gcc/kmod/igb_uio.ko wc_activate=1
    ./usertools/dpdk-devbind.py -b igb_uio xx:xx.x    # xx:xx.x is NTB
    ./usertools/dpdk-devbind.py -b igb_uio xx:xx.x    # xx:xx.x is NIC

2. Launch ntb_fwd sample on Machine1::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --fwd-mode=iofwd --burst=32
    >set fwd iofwd 
    >start
    >show port stats

3. Launch ntb_fwd sample on Machine2::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --fwd-mode=iofwd --burst=32
    >set fwd iofwd
    >start
    >show port stats

4. Send packets (dest mac= nic mac address) with TG and check throughput with log info on two machines.

Test Case6: NTB test with io fwd mode using vfio-pci
====================================================
Test flow: TG <-> NIC1 <-> NTB1 <-> NTB2 <-> NIC2 <-> TG

1. Insmod kernel module and bind Non-Transparent Bridge and NIC to vfio-pci driver on two host machines separately::

    insmod x86_64-native-linuxapp-gcc/kmod/vfio-pci.ko
    insmod vfio-pci
    lspci -vv -s ae:00.0
    echo "base=0x39bfa0000000 size=0x400000 type=write-combining" >> /proc/mtrr
    echo "base=0x39bfa0000000 size=0x4000000 type=write-combining" >> /proc/mtrr
    ./usertools/dpdk-devbind.py -b vfio-pci xx:xx.x    # xx:xx.x is NTB
    ./usertools/dpdk-devbind.py -b vfio-pci xx:xx.x    # xx:xx.x is NIC

2. Launch ntb_fwd sample on Machine1::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --fwd-mode=iofwd --burst=32
    >set fwd iofwd 
    >start
    >show port stats

3. Launch ntb_fwd sample on Machine2::

    ./examples/ntb/build/ntb_fwd -l 28-32 -n 6 -- -i --fwd-mode=iofwd --burst=32
    >set fwd iofwd
    >start
    >show port stats

4. Send packets (dest mac= nic mac address) with TG and check throughput with log info on two machines.
