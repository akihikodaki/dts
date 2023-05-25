.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2023 Intel Corporation

=======================================================================================
Benchmark the performance of pf multi driver forwarding with Intel® Ethernet 700 Series
=======================================================================================

Description
===========

The feature reduce the ITR interval of multi-driver mode in driver i40e.
Set the multi-driver mode in driver i40e, the perf will no drop compare with
no multi-driver mode.

Prerequisites
=============

1. Hardware::

    I40e: XXV710, XL710, X710

2. Software::

    dpdk: git clone http://dpdk.org/git/dpdk
    trex: git clone http://trex-tgn.cisco.com/trex/release/v2.93.tar.gz


Test Case
=========
The test case check the throughput result with ipv4, in the case,
we will send the bi-direction flows with line rate, then we can check the
passthrough rate.

Common Steps
------------

1. Bind tested ports to vfio-pci::

    <dpdk_dir>#./usertools/dpdk-devbind.py -s
    0000:b1:00.0 'Ethernet Controller XXV710 for 25GbE SFP28 158b' if=ens21f0 drv=i40e unused=vfio-pci
    0000:ca:00.0 'Ethernet Controller XXV710 for 25GbE SFP28 158b' if=ens25f0 drv=i40e unused=vfio-pci
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci <pci device id>
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:00.0
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci 0000:ca:00.0

2. Configure traffic generator to send traffic

    Test flow MAC table.

    +------+---------+------------+----------------+
    | Flow | Traffic | MAC        | MAC            |
    |      | Gen.    | Src.       | Dst.           |
    |      | Port    | Address    | Address        |
    +======+=========+============+================+
    |   1  |   TG0   | Random MAC | 11:22:33:44:55 |
    +------+---------+------------+----------------+
    |   2  |   TG1   | Random Mac | 11:22:33:44:55 |
    +------+---------+------------+----------------+

    The Flow IP table.

    +------+---------+------------+------------+
    | Flow | Traffic | IPV4       | IPV4       |
    |      | Gen.    | Src.       | Dest.      |
    |      | Port    | Address    | Address    |
    +======+=========+============+============+
    |   1  |   TG0   | Any IP     | 198.18.1.0 |
    +------+---------+------------+------------+
    |   2  |   TG1   | Any IP     | 198.18.0.0 |
    +------+---------+------------+------------+

    Set the packet length : 64 bytes-1518 bytes
    The IPV4 Dest Address increase with the num 1024.

3. Test results table.

    +-----------+------------+-------------+---------+
    |  Fwd_core | Frame Size |  Throughput |   Rate  |
    +===========+============+=============+=========+
    |  1C/1T    |    64      |  xxxxx Mpps |   xxx % |
    +-----------+------------+-------------+---------+
    |  1C/1T    |   ...      |  xxxxx Mpps |   xxx % |
    +-----------+------------+-------------+---------+

Test Case 1: test_perf_enable_multi_driver
------------------------------------------
test steps
~~~~~~~~~~
1. Bind PF ports to dpdk driver as common step 1::

    ./usertools/dpdk-devbind.py -b vfio-pci b1:00.0 ca:00.0

2. Start dpdk-testpmd with multi driver::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=512 \
     -a 0000:b1:00.0,support-multi-driver=1 -a 0000:ca:00.0,support-multi-driver=1 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=io \
     --nb-cores=1

    Note:
      -force-max-simd-bitwidth: set 512.
      support-multi-driver: enable multi driver

3. Configure traffic generator to send traffic as common step 2.

4. Record Test results as common step 3.
