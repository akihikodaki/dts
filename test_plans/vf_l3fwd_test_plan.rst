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


==================================
VF L3 Forwarding Performance Tests
==================================

This document provides benchmark test for NIC VFs which are created from
kernel PFs or DPDK PFs. These tests use l3fwd as a simple forwarder
between NIC vfs. The goal of this test plan is to have a tested benchmark
between NIC vfs.


Prerequisites
==============

* Hardware requirements:

  * XL710, XXV710: 2 ports from 2 NICs, 1 port per NIC, 2 cores & 2 queues per VF.

    ::

      +------------------------------+
      |  DUT           |  TESTER     |
      +==============================+
      | NIC-1,Port-1  ---  TG,Port-1 |
      | NIC-2,Port-1  ---  TG,Port-2 |
      +------------------------------+


  * X710: 4 ports from 1 NIC, 1 core 1 queues per port.

    ::

      +------------------------------+
      |  DUT           |  TESTER     |
      +==============================+
      | NIC-1,Port-1  ---  TG,Port-1 |
      | NIC-1,Port-2  ---  TG,Port-2 |
      | NIC-1,Port-3  ---  TG,Port-3 |
      | NIC-1,Port-4  ---  TG,Port-4 |
      +------------------------------+

  * 825992: 2 ports from 2 NIC, 1 core 1 queues per port.

    ::

      + -----------------------------+
      |  DUT           |  TESTER     |
      +==============================+
      | NIC-1,Port-1  ---  TG,Port-1 |
      | NIC-2,Port-1  ---  TG,Port-2 |
      +------------------------------+

* Case config:
    For test vf_l3fwd perf, need to set "define RTE_TEST_RX_DESC_DEFAULT 2048" and "define RTE_TEST_TX_DESC_DEFAULT 2048"
    in ./examples/l3fwd/l3fwd.h and re-build l3fwd.

Setup overview
==============

Set up topology as above based on the NIC used.

Build dpdk and examples=l3fwd:
   CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static <build_target>
   ninja -C <build_target>

   meson configure -Dexamples=l3fwd <build_target>
   ninja -C <build_target>

Test Case 1: Measure performance with kernel PF & dpdk VF
=========================================================

1, Bind PF ports to kernel driver, i40e or ixgbe, then create 1 VF from each PF,
take XL710 for example::

  echo 1 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
  echo 1 > /sys/bus/pci/devices/0000\:18\:00.1/sriov_numvfs

2, Set vf mac address::

  ip link set ens5f0 vf 0 mac 00:12:34:56:78:01
  ip link set ens5f1 vf 0 mac 00:12:34:56:78:02

3, Bind all the created VFs to dpdk driver, igb_uio or vfio-pci::

  ./usertools/dpdk-devbind.py -b igb_uio 18:02.0 18:06.0

4, Start dpdk l3fwd with 1:1 matched cores and queues::

  ./<build_target>/examples/dpdk-l3fwd -c 0xf -n 4 -- -p 0x3 --config '(0,0,0),(1,0,1),(0,1,2),(1,1,3)'

5, Send packet with frame size from 64bytes to 1518bytes with ixia traffic generator,
make sure your traffic configuration meets LPM rules, and will go to all queues, all ports.
Fill out this table with results.

+-------+------+--------+-----------+
| Frame | mode | Mpps   | %linerate |
+=======+======+========+===========+
| 64    | lpm  |        |           |
+-------+------+--------+-----------+
| 128   | lpm  |        |           |
+-------+------+--------+-----------+
| 256   | lpm  |        |           |
+-------+------+--------+-----------+
| 512   | lpm  |        |           |
+-------+------+--------+-----------+
| 1024  | lpm  |        |           |
+-------+------+--------+-----------+
| 1518  | lpm  |        |           |
+-------+------+--------+-----------+


Test Case 2: Measure performance with dpdk PF & dpdk VF
=======================================================

1, Bind PF ports to igb_uio driver, then create 1 VF from each PF,
take XL710 for example::

  ./usertools/dpdk-devbind.py -b igb_uio 18:00.0 18:00.1
  echo 1 > /sys/bus/pci/devices/0000\:18\:00.0/max_vfs
  echo 1 > /sys/bus/pci/devices/0000\:18\:00.1/max_vfs

2, Bind the two created VFs to dpdk driver, igb_uio or vfio-pci::

  ./usertools/dpdk-devbind.py -b igb_uio 18:02.0 18:06.0

3, Start testpmd and set vfs mac address::

  ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 --socket-mem=1024,1024 --file-prefix=pf -b 0000:18:02.0 -b 0000:18:06.0 -- -i
  testpmd>set vf mac addr 0 0 00:12:34:56:78:01
  testpmd>set vf mac addr 1 0 00:12:34:56:78:02

4, Start dpdk l3fwd with 1:1 matched cores and queues::

  ./<build_target>/examples/dpdk-l3fwd -c 0x3c -n 4 -a 0000:18:02.0 -a 0000:18:06.0 -- -p 0x3 --config '(0,0,2),(1,0,3),(0,1,4),(1,1,5)'

5, Send packet with frame size from 64bytes to 1518bytes with ixia traffic generator,
make sure your traffic configuration meets LPM rules, and will go to all queues, all ports.
Fill out this table with results.

+-------+------+--------+-----------+
| Frame | mode | Mpps   | %linerate |
+=======+======+========+===========+
| 64    | lpm  |        |           |
+-------+------+--------+-----------+
| 128   | lpm  |        |           |
+-------+------+--------+-----------+
| 256   | lpm  |        |           |
+-------+------+--------+-----------+
| 512   | lpm  |        |           |
+-------+------+--------+-----------+
| 1024  | lpm  |        |           |
+-------+------+--------+-----------+
| 1518  | lpm  |        |           |
+-------+------+--------+-----------+
