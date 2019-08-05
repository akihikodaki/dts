.. Copyright (c) <2010-2019>, Intel Corporation
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

=============
ethtool stats
=============

This document provides test plan for ethtool stats . This is a simple example
app featuring packet processing, ethtool is a utility for Linux kernel-based
operating system for displaying and modifying some parameters of network
interface controllers (NICs) and their device drivers.

Currently Ethtool supports a more complete list of stats for the same drivers
that DPDK supports. The idea behind this epic is two fold as following.
1. To achieve metric equivalence with what linux's ethtool provides.
2. To extend the functionality of the xstats API to enable the following options::

    - the retrieval of aggregate stats upon request (Top level stats).
    - the retrieval of the extended NIC stats.
    - grouping of stats logically so they can be retrieved per logical grouping.
    - the option to enable/disable the stats groups to retrieve similar to set private flags in ethtool.

Prerequisites
=============

2xNICs (2 full duplex optical ports per NIC). One on dut, another one on tester,
link them together. Update two nics' firmware to latest version.

Test cases
==========

Check port extended statistics parameter after sending packet from peer link port.

bind two ports::

    ./usertools/dpdk-devbind.py --bind=igb_uio <pci address 1> <pci address 2>

Test Case: xstat command set intergrity
---------------------------------------

check ``dpdk-procinfo`` tool support ``xstats`` command options.

These options should be included::

   ``xstats``
   ``xstats-name``
   ``xstats-id``
   ``xstats-reset``

steps:

#. boot up ``testpmd``::

    ./<target name>/app/testpmd -c 0x600006 -n 4  -- -i --port-topology=loop

#. run ``dpdk-procinfo`` tool::

    ./<target name>/app/dpdk-procinfo

#. check ``dpdk-procinfo`` tool output should contain upper options.

Test Case: xstat command
------------------------

check if port extended statistics can get right data.

steps:

#. boot up ``testpmd``::

    ./<target name>/app/testpmd -c 0x600006 -n 4  -- -i --port-topology=loop

#. send udp packet of 64/72/128/256/512/1024 size to port 0/1::

    sendp([Ether()/IP()/UDP()/Raw('\0'*60)], iface=<port 0 name>)

#. run ``dpdk-procinfo`` tool with ``xstats`` option and check if all port have
   a correct data of different size packet::

    ./<target name>/app/dpdk-procinfo -- -p 3 --xstats

Test Case: xstat-reset command
------------------------------

check if port extended statistics can be cleared.

steps:

#. boot up ``testpmd``::

    ./<target name>/app/testpmd -c 0x600006 -n 4  -- -i --port-topology=loop

#. send udp packet of 64/72/128/256/512/1024 size to port 0/1::

    sendp([Ether()/IP()/UDP()/Raw('\0'*60)], iface=<port 0 name>)

#. run ``dpdk-procinfo`` tool with ``xstats-reset`` option and check if all port
   statistics have been cleared::

    ./<target name>/app/dpdk-procinfo -- -p 3 --xstats-reset

Test Case: xstat single statistic
---------------------------------

check if port extended statistic name can be get by statistic id and check
related data's correctness.

steps:

#. boot up ``testpmd``::

    ./<target name>/app/testpmd -c 0x600006 -n 4  -- -i --port-topology=loop

#. run ``dpdk-procinfo`` tool with ``xstats`` option to get all NIC extended
   statistics parameters of port and use the output display sequence as parameter
   index in the following search index::

    ./<target name>/app/dpdk-procinfo -- -p 3 --xstats

#. send udp packet of 64/72/128/256/512/1024 size to port 0/1::

    sendp([Ether()/IP()/UDP()/Raw('\0'*60)], iface=<port 0 name>)

#. run ``dpdk-procinfo`` tool with ``xstats-id`` option to get the statistic
   name corresponding with the index id::

    ./<target name>/app/dpdk-procinfo -- -p 3 --xstats-id 0,1,...N

#. run ``dpdk-procinfo`` tool with ``xstats-name`` option to get the statistic
   data corresponding with the statistic name::

    ./<target name>/app/dpdk-procinfo -- -p 3 --xstats-name <statistic name>