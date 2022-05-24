.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

=========================================
Sample Application Tests: Cmdline Example
=========================================

The cmdline example is a demo example of command line interface in RTE.
This library is a readline-like interface that can be used to debug your
RTE application.

It supports some features of GNU readline like completion, cut/paste,
and some other special bindings that makes configuration and debug
faster and easier.

This demo shows how rte_cmdline library can be extended to handle a
list of objects. There are 3 simple commands:

- ``add obj_name IP``: add a new object with an IP/IPv6 address
  associated to it.

- ``del obj_name``: del the specified object.

- ``show obj_name``: show the IP associated with the specified object.

Refer to programmer's guide in ``${RTE_SDK}/doc/rst`` for details.


Prerequisites
=============

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

Build dpdk and examples=cmdline:
   CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static <build_target>
   ninja -C <build_target>

   meson configure -Dexamples=cmdline <build_target>
   ninja -C <build_target>

Launch the ``cmdline`` with 24 logical cores in linuxapp environment::

  $ ./build/examples/dpdk-cmdline -cffffff

Test the 3 simple commands in below prompt ::

  example>


Test Case: cmdline sample commands test
=======================================

Add a test object with an IP address associated to it::

  example>add object 192.168.0.1
    Object object added, ip=192.168.0.1

Verify the object existence::

  example>add object 192.168.0.1
    Object object already exist

Show the object result by ``show`` command::

  example>show object
    Object object, ip=192.168.0.1

Verify the output matches the configuration.

Delete the object in cmdline and show the result again::

  example>del object
    Object object removed, ip=192.168.0.1

Double delete the object to verify the correctness::

  example>del object
    Bad arguments

Verify no such object exist now.::

  example>show object
    Bad arguments

Verify the hidden command ? and help command::

  example>help
    Demo example of command line interface in RTE

    This is a readline-like interface that can be used to
    debug your RTE application. It supports some features
    of GNU readline like completion, cut/paste, and some
    other special bindings.

    This demo shows how rte_cmdline library can be
    extended to handle a list of objects. There are
    3 commands:
    - add obj_name IP
    - del obj_name
    - show obj_name

  example>?
    show [Mul-choice STRING]: Show/del an object
    del [Mul-choice STRING]: Show/del an object
    add [Fixed STRING]: Add an object (name, val)
    help [Fixed STRING]: show help

Test Case: cmdline exit test
============================

To verify exit cmdline process::

  example>^D

.. there should be an ``quit`` command instead of ^D,
   or a hint make the user know how to exit.
