.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

==============
Coremask Tests
==============


Prerequisites
=============

This test will run in any machine able to run ``test``. No traffic will be sent.
No extra needs for ports.

Test Case
=========

Test Case 1: individual coremask
--------------------------------

1. Launch ``test`` once per core, set the core mask for the core::

    ./x86_64-default-linuxapp-gcc/app/test/dpdk-test -c <One core mask> -n 4

2. Verify: every time the application is launched the core is properly detected
   and used.

3. Stop ``test``.


Test Case 2: big coremask
-------------------------

1. Launch ``test`` with a mask bigger than the available cores::

    ./x86_64-default-linuxapp-gcte't'sc/app/test/dpdk-test -c <128 bits mask> -n 4

2. Verify: the application handles the mask properly and all the available cores
   are detected and used.

3. Stop ``test``.

Test Case 3: all cores coremask
-------------------------------

1. Launch ``test`` with all the available cores::

    ./x86_64-default-linuxapp-gcc/app/test/dpdk-test -c <All cores mask> -n 4

2. Verify: all the cores have been detected and used by the application.

3. Stop ``test``.

Test Case 4: wrong coremask
---------------------------

1. Launch ``test`` with several wrong masks::

    ./x86_64-default-linuxapp-gcc/app/test/dpdk-test -c <Wrong mask> -n 4

2. Verify: the application complains about the mask and does not start.

3. Stop ``test``.
