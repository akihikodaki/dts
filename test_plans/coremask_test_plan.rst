.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

==============
Coremask Tests
==============


Prerequisites
=============

This test will run in any machine able to run ``test``. No traffic will be sent.
No extra needs for ports.


Test Case: individual coremask
==============================

Launch ``test`` once per core, set the core mask for the core::

    ./x86_64-default-linuxapp-gcc/app/test/dpdk-test -c <One core mask> -n 4


Verify: every time the application is launched the core is properly detected
and used.

Stop ``test``.


Test Case: big coremask
=======================

Launch ``test`` with a mask bigger than the available cores::

    ./x86_64-default-linuxapp-gcc/app/test/dpdk-test -c <128 bits mask> -n 4


Verify: the application handles the mask properly and all the available cores
are detected and used.

Stop ``test``.

Test Case: all cores
====================

Launch ``test`` with all the available cores::

    ./x86_64-default-linuxapp-gcc/app/test/dpdk-test -c <All cores mask> -n 4


Verify: all the cores have been detected and used by the application.

Stop ``test``.

Test Case: wrong coremask
=========================

Launch ``test`` with several wrong masks::

    ./x86_64-default-linuxapp-gcc/app/test/dpdk-test -c <Wrong mask> -n 4


Verify: the application complains about the mask and does not start.

Stop ``test``.
