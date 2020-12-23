Test DPDK based on igb_uio
==========================

The kernel module igb_uio is moved to the dpdk-kmods repository in the
/linux/igb_uio/ directory snice DPDK 20.11 (commit: 56bb5841fd06).
The most easy way to test DPDK in DTS based on igb_uio is to add igb_uio
source code back to dpdk.


Get Source Code
---------------

Get DPDK::

   git clone git://dpdk.org/dpdk
   git clone http://dpdk.org/git/dpdk

Get igb_uio::

   git clone http://dpdk.org/git/dpdk-kmods
   git clone git://dpdk.org/dpdk-kmods

Integrate igb_uio into DPDK
---------------------------

Assume you have cloned the dpdk and dpdk-kmods source code
in ./dpdk and ./dpdk-kmods.

#. Copy dpdk-kmods/linux/igb_uio/ to dpdk/kernel/linux/::

    [root@dts linux]# cp -r ./dpdk-kmods/linux/igb_uio /root/dpdk/kernel/linux/
    [root@dts linux]# ls ./dpdk/kernel/linux/
    igb_uio  kni  meson.build

#. enable igb_uio build in meson:

*   add igb_uio in dpdk/kernel/linux/meson.build subdirs as below::

     subdirs = ['kni', 'igb_uio']

.. note::

    igb_uio will be added into compile list when it is added in subdirs.


*   create a file of meson.build in dpdk/kernel/linux/igb_uio/ as below::

     # SPDX-License-Identifier: BSD-3-Clause
     # Copyright(c) 2017 Intel Corporation

     mkfile = custom_target('igb_uio_makefile',
             output: 'Makefile',
             command: ['touch', '@OUTPUT@'])

     custom_target('igb_uio',
             input: ['igb_uio.c', 'Kbuild'],
             output: 'igb_uio.ko',
             command: ['make', '-C', kernel_dir + '/build',
                     'M=' + meson.current_build_dir(),
                     'src=' + meson.current_source_dir(),
                     'EXTRA_CFLAGS=-I' + meson.current_source_dir() +
                             '/../../../lib/librte_eal/include',
                     'modules'],
             depends: mkfile,
             install: true,
             install_dir: kernel_dir + '/extra/dpdk',
             build_by_default: get_option('enable_kmods'))

.. note::

    DPDK is using meson build, create meson.build so that igb_uio can be built.

DTS configuration
-----------------

#. Pack the dpdk into dpdk.tar.gz and copy into dts/dep::

    tar -zcvf dpdk.tar.gz dpdk
    cp dpdk.tar.gz ~/dts/dep


#. config drivername=igb_uio in execution.cfg::

    [Execution1]
    crbs=127.0.0.1
    drivername=igb_uio
    build_type=meson
    test_suites=
        checksum_offload,
    targets=
        x86_64-native-linuxapp-gcc
    parameters=nic_type=cfg:func=true

#. configure dts with other requirements (not mentioned here) and now start dts::

   ./dts

.. note ..

    dts parameter "-s" means skip setup, it won't unpack dep/dpdk.tar.gz
    to the default directory `/root/dpdk`, but use dpdk already there.
    so copy the integrated dpdk to `/root/dpdk` if with `-s`