======================
How dts work with trex
======================

dpdk hugepage management conflict issue
=======================================
trex use older dpdk version than we release cycle source code. When dpdk change
the memory management merchanism, trex will meet the following issue.

Trex should run on an independent platform. DUT/Trex should run on two platforms
*. one is used as TESTER and trex server, another one is used as DUT.(dts/pktgen)
*. one is used as trex server, another one is used as DUT/TESTER.(recommended scheme)
   This scheme can make sure that trex run on its full status capability.

When trex run with dts on the same platform, trex server sometimes boot up
failed for hugepage error.

.. code-block:: console

      ./t-rex-64  -i --stl -k 4

         Starting Scapy server..... Scapy server is started
         Trying to bind to igb_uio ...
         /usr/bin/python3 dpdk_nic_bind.py --bind=igb_uio 0000:85:00.0 0000:8a:00.1
         The ports are bound/configured.
         Starting  TRex v2.41 please wait  ...
         EAL: Can only reserve 1766 pages from 4096 requested
         Current CONFIG_RTE_MAX_MEMSEG=256 is not enough
         Please either increase it or request less amount of memory.
         EAL: FATAL: Cannot init memory

         EAL: Cannot init memory

          You might need to run ./trex-cfg  once
         EAL: Error - exiting with code: 1
           Cause: Invalid EAL arguments

trex quit when using NNT
========================
when bind dut NNT port to igb_uio, peer port will get a link down status, then
trex server using NNT nic will quit.

.. code-block:: console

   WATCHDOG: task 'master' has not responded for more than 2.00044 seconds - timeout is 2 seconds

   *** traceback follows ***

   1       0x55a7c779561a ./_t-rex-64(+0x12761a) [0x55a7c779561a]
   2       0x7f23da4be1b0 /lib64/libpthread.so.0(+0x121b0) [0x7f23da4be1b0]
   3       0x55a7c7942d40 rte_delay_us_block + 128
   4       0x55a7c798d731 ixgbe_setup_mac_link_multispeed_fiber + 337
   5       0x55a7c79a8f14 ./_t-rex-64(+0x33af14) [0x55a7c79a8f14]
   6       0x55a7c7954c72 rte_eth_link_get_nowait + 114
   7       0x55a7c776a988 DpdkTRexPortAttr::update_link_status_nowait() + 24
   8       0x55a7c77856a6 CGlobalTRex::handle_slow_path() + 118
   9       0x55a7c7785ad7 CGlobalTRex::run_in_master() + 759
   10      0x55a7c7785e3c ./_t-rex-64(+0x117e3c) [0x55a7c7785e3c]
   11      0x55a7c793efba rte_eal_mp_remote_launch + 346
   12      0x55a7c7789e1e main_test(int, char**) + 1038
   13      0x7f23d9417f2a __libc_start_main + 234
   14      0x55a7c7719b9d ./_t-rex-64(+0xabb9d) [0x55a7c7719b9d]


   *** addr2line information follows ***

   ??:0
   ??:0
   ??:0
   ??:0
   ??:0
   ??:0
   ??:0
   ??:0
   ??:0
   ??:0
   ??:0
   ??:0
   ??:0
   ??:0


   ./t-rex-64: line 80: 25870 Aborted                 (core dumped) ./_$(

scapy name space conflict
=========================
trex scapy lib will be conflict with

resolved scheme
---------------

#. backup your scapy::
   cp -fr /usr/lib/python2.7/site-packages/scapy /usr/lib/python2.7/site-packages/scapy_backup

#. unify scapy version with trex::
   cp -fr /opt/trex/v2.41/trex_client/external_libs/scapy-2.3.1/python2/scapy /usr/lib/python2.7/site-packages/scapy

other issues
============

#. linux kernel verion should not be too low.

#. Trex only works with even number link peers.

#. Trex only works with nics, which are using the same driver.

#. Before boot up trex, please make sure the peer ports are on up status.

#. If you have ran dpdk on the platform which you want to deploy trex-server,
   reboot the platform to make sure that trex-server can work fine.

#. If using i40e driver, Trex v2.41 version need i40e nic firmware version newer than 5.02.