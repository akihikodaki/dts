.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

==============================================================
Benchmark the performance of rx timestamp forwarding with E810
==============================================================

This document provides the plan for testing the performance of Intel Ethernet Controller.
This test plan cover the test cases of throughput with enable rx timestamp.
The Performance results are produced using ``dpdk-testpmd`` application.

Prerequisites
=============

1. Hardware:

   1.1) rx timestamp perf test for Intel® Ethernet Network Adapter E810-CQDA2:
        1 NIC or 2 NIC cards attached to the same processor and 1 port used of each NIC.
   1.2) rx timestamp perf test for Intel® Ethernet Network Adapter E810-XXVDA4:
        1 NIC card attached to the processor and 4 ports used.

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
    0000:17:00.0 'Device 1592' if=ens5f0 drv=ice unused=vfio-pci
    0000:4b:00.1 'Device 1592' if=ens6f0 drv=ice unused=vfio-pci
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci <pci device id>
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci 0000:17:00.0
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci 0000:4b:00.1

2. Configure traffic generator to send traffic

    Test flow MAC table.

    +------+---------+------------+---------------+
    | Flow | Traffic | MAC        | MAC           |
    |      | Gen.    | Src.       | Dst.          |
    |      | Port    | Address    | Address       |
    +======+=========+============+===============+
    |   1  |   TG0   | Random MAC | DUT Port0 Mac |
    +------+---------+------------+---------------+
    |   2  |   TG1   | Random Mac | DUT port1 Mac |
    +------+---------+------------+---------------+
    |   3  |   TG2   | Random Mac | DUT port2 Mac |
    +------+---------+------------+---------------+
    |   4  |   TG3   | Random Mac | DUT port3 Mac |
    +------+---------+------------+---------------+

    The Flow IP table.

    +------+---------+------------+---------+
    | Flow | Traffic | IPV4       | IPV4    |
    |      | Gen.    | Src.       | Dest.   |
    |      | Port    | Address    | Address |
    +======+=========+============+=========+
    |   1  |   TG0   | Any IP     | 2.1.1.1 |
    +------+---------+------------+---------+
    |   2  |   TG1   | Any IP     | 1.1.1.1 |
    +------+---------+------------+---------+
    |   3  |   TG2   | Any IP     | 4.1.1.1 |
    +------+---------+------------+---------+
    |   4  |   TG3   | Any IP     | 3.1.1.1 |
    +------+---------+------------+---------+

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
    |  2C/2T    |    64      |  xxxxx Mpps |   xxx % |
    +-----------+------------+-------------+---------+
    |  2C/2T    |    ...     |  xxxxx Mpps |   xxx % |
    +-----------+------------+-------------+---------+
    |  4C/4T    |    64      |  xxxxx Mpps |   xxx % |
    +-----------+------------+-------------+---------+
    |  4C/4T    |    ...     |  xxxxx Mpps |   xxx % |
    +-----------+------------+-------------+---------+
    |  8C/8T    |    64      |  xxxxx Mpps |   xxx % |
    +-----------+------------+-------------+---------+
    |  8C/8T    |    ...     |  xxxxx Mpps |   xxx % |
    +-----------+------------+-------------+---------+

Test Case 1: iavf_throughput_enable_ptp_scalar
----------------------------------------------

1. Bind PF ports to kernel driver(ice), then create 1 VF from each PF,
   take E810-CQDA2 for example::

    echo 1 > /sys/bus/pci/devices/0000\:17\:00.0/sriov_numvfs
    echo 1 > /sys/bus/pci/devices/0000\:4b\:00.1/sriov_numvfs

2. Set vf mac address::

    ip link set ens5f0 vf 0 mac 00:12:34:56:78:01
    ip link set ens6f0 vf 0 mac 00:12:34:56:78:02

3. Bind all the created VFs to dpdk driver as common step 1::

    ./usertools/dpdk-devbind.py -b vfio-pci 17:01.0 4b:01.0

4. Start dpdk-testpmd::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=64 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=mac \
     --nb-cores=1 --enable-rx-timestamp

    Note:
      -force-max-simd-bitwidth: Set 64, the feature only support 64.
      -enable-rx-timestamp: enable rx-timestamp.

5. Configure traffic generator to send traffic as common step 2.

6. Record Test results as common step 3.

Test Case 2: iavf_throughput_disable_ptp_scalar
-----------------------------------------------

1. Excute iavf_throughput_enable_ptp_scalar steps 1-3.

2. Start dpdk-testpmd with disable rx-timestamp::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=64 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=mac \
     --nb-cores=1

3. Excute iavf_throughput_enable_ptp_scalar steps 5-6.

Test Case 3: pf_throughput_enable_ptp_scalar
--------------------------------------------

1. Bind PF ports to dpdk driver as common step 1::

    ./usertools/dpdk-devbind.py -b vfio-pci 17:00.0 4b:00.0

2. Start dpdk-testpmd::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=64 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=io \
     --nb-cores=1 --enable-rx-timestamp

3. Configure traffic generator to send traffic as common step 2.

4. Record Test results as common step 3.

Test Case 4: pf_throughput_disable_ptp_scalar
---------------------------------------------

1. Bind PF ports to dpdk driver as common step 1::

    ./usertools/dpdk-devbind.py -b vfio-pci 17:00.0 4b:00.0

2. Start dpdk-testpmd with disable rx-timestamp::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=64 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=io \
     --nb-cores=1

3. Configure traffic generator to send traffic as common step 2.

4. Record Test results as common step 3.
