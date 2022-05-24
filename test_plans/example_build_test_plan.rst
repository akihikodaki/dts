.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2011 Intel Corporation

=============
Example Build
=============

This test case is for testing that all applications under DPDK examples compile successfully.
Such as these applications::

    - bbdev_app
    - bond
    - cmdline
    - distributor
    ...

Prerequisites
=============

Dependency package requirements:

    - libvert: https://libvirt.org/
    - intel-cmt-cat: https://github.com/01org/intel-cmt-cat

Test case: example build
========================

compile the applications of examples  successfully::

    meson configure -Dexamples=all x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc

If the compilation is successful, it will be the same as the shown in the terminal. ::

    ...
    [188/193] Linking target examples/dpdk-efd_node
    [189/193] Linking target examples/dpdk-vhost_crypto
    [190/193] Linking target examples/dpdk-pipeline
    [191/193] Linking target examples/dpdk-efd_server
    [192/193] Linking target examples/dpdk-vhost
    [193/193] Linking target examples/dpdk-vmdq
