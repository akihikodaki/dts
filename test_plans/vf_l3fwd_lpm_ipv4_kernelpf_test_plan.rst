.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=============================================================
VF L3 forwarding kernel PF test in LPM mode with IPV4 packets
=============================================================

This document provides benchmark test for NIC VFs which are created from
kernel PFs or. These tests use l3fwd as a simple forwarder between NIC vfs.
The goal of this test plan is to have a tested benchmark between NIC vfs.
The Layer-3 Forwarding  performance results are produced using ``l3fwd`` application.
For detail test plan, please refer to ``l3fwd_test_plan.rst``.

Prerequisites
=============

Topology
--------
It requires at least 1 port connected traffic generator::
        Port0 --- TG0

2 ports::
        Port0 --- TG0
        Port1 --- TG1

4 ports::
        Port0 --- TG0
        Port1 --- TG1
        Port2 --- TG2
        Port3 --- TG3

Hardware
--------
This suite focus on l3fwd application, so any standard Ethernet Network Adapter is qualified.

Software
--------
dpdk: git clone http://dpdk.org/git/dpdk
trex: git clone http://trex-tgn.cisco.com/trex/release/v2.93.tar.gz


Test Case
=========
The test case check the throughput result with lpm mode and ipv4, in the case,
we will send the bi-direction flows with line rate, then we can check the
passthrough rate.

The l3fwd application has a number of command line options, here list the key options will be tested::

    ./dpdk-l3fwd [EAL options] -- -p PORTMASK
                             [--force-max-simd-bitwidth=max-simd-bitwidth]
                             --config(port,queue,lcore)[,(port,queue,lcore)]
                             [--rx-queue-size NPKTS]
                             [--tx-queue-size NPKTS]
                             [--parse-ptype]
                             [-L]|[-E]
                             ...
    Note:
        --force-max-simd-bitwidth: This setting is used to determine the vector path for component selection.
                                   And the default is avx2.
        --rx-queue-size: Rx queue size in decimal and default is 1024.
        --tx-queue-size: Tx queue size in decimal and default is 1024.
        --parse-ptype: Optional, set to use software to analyze packet type.
                       Without this option, hardware will check the packet type.
        [-L]|[-E]: L3fwd uses the parameters "-L" and "-E" to correspond to LPM and EM modes respectively.
                   And the default is LPM mode.

Common Steps
------------
1. Bind PF ports to kernel driver, i40e or ice, then create 1 VF from each PF,
   take E810 for example::

    <dpdk_dir>#echo 1 > /sys/bus/pci/devices/0000\:17\:00.0/sriov_numvfs

   Set vf mac address::

    <dpdk_dir>#ip link set ens5f0 vf 0 mac 00:12:34:56:78:01

   Bind all the created VFs to vfio-pci::

    <dpdk_dir>#./usertools/dpdk-devbind.py -s
    0000:17:00.0 'Device 1592' if=ens5f0 drv=ice unused=vfio-pci
    0000:17:01.0 'Device 1592' if=ens5f0v0 drv=iavf unused=vfio-pci
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci <pci device id>
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci 0000:17:01.0

2. Configure traffic generator to send traffic

    Routing table for IPv4 packets
        - In LPM mode, the LPM table used for packet routing is:

        +-------+-----------------------+
        |   #   | LPM prefix (IP/length)|
        +=======+=======================+
        |   0   |      198.18.0.0/24    |
        +-------+-----------------------+
        |   1   |      198.18.1.0/24    |
        +-------+-----------------------+
        |   2   |      198.18.2.0/24    |
        +-------+-----------------------+
        |   3   |      198.18.3.0/24    |
        +-------+-----------------------+

    The flows need to be configured and started by the traffic generator:
        - IPv4 packets

        +------+---------+------------+---------+
        | Flow | Traffic | IPv4       | IPv4    |
        |      | Gen.    | Dst.       | Src.    |
        |      | Port    | Address    | Address |
        +======+=========+============+=========+
        |   1  |   TG0   | 198.18.1.1 |  Any Ip |
        +------+---------+------------+---------+
        |   2  |   TG1   | 198.18.0.1 |  Any Ip |
        +------+---------+------------+---------+
        |   3  |   TG2   | 198.18.3.1 |  Any Ip |
        +------+---------+------------+---------+
        |   4  |   TG3   | 198.18.2.1 |  Any Ip |
        +------+---------+------------+---------+

        Set the packet length : 64 bytes-1518 bytes
        The IPV4 Src Address increase with the num 1024.

3. Test result table

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


Test Case: test_perf_vf_throughput_ipv4_lpm
-------------------------------------------

1. Bind VF ports to dpdk driver as common step 1.

2. Launch l3fwd::

     <build_dir>/examples/dpdk-l3fwd -l 5-8 -n 8 --force-max-simd-bitwidth=512 \
     -- -p 0x1 --config "(0,0,5),(0,1,6),(0,2,7),(0,3,8)" --rx-queue-size 1024 \
     --tx-queue-size 1024 --parse-ptype

3. Configure traffic generator to send traffic as common step 2.

4. Record Test results as common step 3.
