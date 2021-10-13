.. Copyright (c) <2014-2017>, Intel Corporation
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

=====================
Unit Tests: Dump Ring
=====================

This is the test plan for dumping the elements of Intel® DPDK ring.

This section explains how to run the unit tests for dumping elements of ring.
The test can be launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

The steps to run the unit test manually are as follow::

  # make -C ./app/test/
  # ./app/test/test -n 1 -c ffff
  RTE>> dump_ring

The final output of the test will be detailed elements of DPDK ring.

Dump the elements of designative DPDK ring::

  RTE>> dump_ring <ring_name>

The final output of the test will be detailed elements of the designative DPDK ring.

========================
Unit Tests: Dump Mempool
========================

This is the test plan for dumping the elements of Intel® DPDK mempool.

This section explains how to run the unit tests for dumping elements of mempool.
The test can be launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

The steps to run the unit test manually are as follow::

  # make -C ./app/test/
  # ./app/test/test -n 1 -c ffff
  RTE>> dump_mempool

The final output of the test will be detailed elements of DPDK mempool.

Dump the elements if designative DPDK mempool::

  RTE>> dump_mempool <mempool_name>

The final output of the test will be detailed elements of the designative DPDK mempool.

================================
Unit Tests: Dump Physical Memory
================================

This is the test plan for dumping the elements of Intel® DPDK physical memory.

This section explains how to run the unit tests for dumping elements of memory.
The test can be launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

The steps to run the unit test manually are as follow::

  # make -C ./app/test/
  # ./app/test/test -n 1 -c ffff
  RTE>> dump_physmem

The final output of the test will be detailed elements of DPDK physical memory.

========================
Unit Tests: Dump Memzone
========================

This is the test plan for dumping the elements of Intel® DPDK memzone.

This section explains how to run the unit tests for dumping elements of memzone.
The test can be launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

The steps to run the unit test manually are as follow::

  # make -C ./app/test/
  # ./app/test/test -n 1 -c ffff
  RTE>> dump_memzone

The final output of the test will be detailed elements of DPDK memzone.

============================
Unit Tests: Dump Struct Size
============================

This is the test plan for dumping the size of Intel® DPDK structure.

This section explains how to run the unit tests for dumping structure size.
The test can be launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

The steps to run the unit test manually are as follow::

  # make -C ./app/test/
  # ./app/test/test -n 1 -c ffff
  RTE>> dump_struct_sizes

The final output of the test will be the size of DPDK structure.

========================
Unit Tests: Dump Devargs
========================

This is the test plan for dumping device arguments of Intel® DPDK.

This section explains how to run the unit tests for dumping device arguments.
The test can be launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

The steps to run the unit test manually are as follow::

  # make -C ./app/test/
  # ./app/test/test -n 1 -c ffff -a|-b pci_address
  RTE>> dump_devargs

The final output of the test will be the pci address of allow list
or block list.

=============================
Unit Tests: Dump malloc stats
=============================

This is the test plan for dumping malloc stats of Intel® DPDK heaps.

This section explains how to run the unit tests for dumping malloc stats.
The test can be launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

The steps to run the unit test manually are as follow::

  # make -C ./app/test/
  # ./app/test/test -n 1 -c ffff
  RTE>> dump_malloc_stats

The final output of the test will be the malloc stats of DPDK heap.

=============================
Unit Tests: Dump malloc heaps
=============================

This is the test plan for dumping detailed malloc status of each Intel® DPDK heap.

This section explains how to run the unit tests for dumping malloc heaps.
The test can be launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

The steps to run the unit test manually are as follow::

  # make -C ./app/test/
  # ./app/test/test -n 1 -c ffff
  RTE>> dump_malloc_heaps

The final output of the test will be the detailed malloc status of each DPDK heap.

==========================
Unit Tests: Dump log types
==========================

This is the test plan for dumping log level of all Intel® DPDK log types.

This section explains how to run the unit tests for dumping log types.
The test can be launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

The steps to run the unit test manually are as follow::

  # make -C ./app/test/
  # ./app/test/test -n 1 -c ffff
  RTE>> dump_log_types

The final output of the test will be the log level of each DPDK log type.
