.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

===========================================
TestPmd rfc2544 test with IPV4/IPV6 packets
===========================================

This document provides rfc2544 tests for the userland Ethernet Controller Poll Mode Driver (PMD).
The userland PMD application runs the ``IO forwarding mode`` test which described in the PMD test
plan document with different parameters for the configuration of NIC ports.

RFC2544 Zero packet loss test case: Used to determine the DUT throughput as defined in
RFC1242(https://www.ietf.org/rfc/rfc1242.txt). Note RFC6201
https://www.ietf.org/rfc/rfc6201.txt has updated RFC2544 and RFC1242. Please check the link
for more details. In this case, RFC2544 test uses dpdk-testpmd as test application.

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
This suite focus on dpdk-testpmd application, so any standard Ethernet Network Adapter is qualified.

Software
--------
dpdk: git clone http://dpdk.org/git/dpdk
trex: git clone http://trex-tgn.cisco.com/trex/release/v2.93.tar.gz


Test Case
=========
Send a specific number of frames at a specific rate through the DUT and then
count the frames that are transmitted by the DUT. If the count of offered frames is not equal
to the count of received frames, the rate of the offered stream is reduced and the test is rerun.
The throughput is the fastest rate at which the count of test frames transmitted by the DUT is
equal to the number of test frames sent to it by the test equipment.

Common Steps
------------
1. Bind tested ports to vfio-pci::

    <dpdk_dir>#./usertools/dpdk-devbind.py -s
    0000:17:00.0 'Device 1592' if=ens5f0 drv=ice unused=vfio-pci
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci <pci device id>
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci 0000:17:01.0

2. Configure traffic generator to send traffic

    Routing table for IPv4 packets:

        +-------+-----------------------+
        |   #   |    IPv4 (IP/length)   |
        +=======+=======================+
        |   0   |      198.18.0.0/24    |
        +-------+-----------------------+
        |   1   |      198.18.1.0/24    |
        +-------+-----------------------+
        |   2   |      198.18.2.0/24    |
        +-------+-----------------------+
        |   3   |      198.18.3.0/24    |
        +-------+-----------------------+

    Routing table for IPv6 packets:

        +-------+--------------------------------------------+
        |   #   |              IPv6 (IP/length)              |
        +=======+============================================+
        |   0   | 2001:0200:0000:0000:0000:0000:0000:0000/64 |
        +-------+--------------------------------------------+
        |   1   | 2001:0200:0000:0001:0000:0000:0000:0000/64 |
        +-------+--------------------------------------------+
        |   2   | 2001:0200:0000:0002:0000:0000:0000:0000/64 |
        +-------+--------------------------------------------+
        |   3   | 2001:0200:0000:0003:0000:0000:0000:0000/64 |
        +-------+--------------------------------------------+

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

        - IPv6 packets

        +------+---------+-----------------------------------------+---------+
        | Flow | Traffic |                                         | IPv6    |
        |      | Gen.    |           IPV6 Dst. Address             | Src.    |
        |      | Port    |                                         | Address |
        +======+=========+=========================================+=========+
        |   1  |   TG0   | 2001:0200:0000:0000:0000:0000:0000:0000 |  Any Ip |
        +------+---------+-----------------------------------------+---------+
        |   2  |   TG1   | 2001:0200:0000:0001:0000:0000:0000:0000 |  Any Ip |
        +------+---------+-----------------------------------------+---------+
        |   3  |   TG2   | 2001:0200:0000:0002:0000:0000:0000:0000 |  Any Ip |
        +------+---------+-----------------------------------------+---------+
        |   4  |   TG3   | 2001:0200:0000:0003:0000:0000:0000:0000 |  Any Ip |
        +------+---------+-----------------------------------------+---------+

        Set the packet length : 66 bytes-1518 bytes
        The IPV6 Src Address increase with the num 1024.

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


Test Case: testpmd rfc2544 performance with IPv4/IPv6 Packets
-------------------------------------------------------------

1. Bind tested ports to dpdk driver as common step 1.

2. Start dpdk-testpmd::

    <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=512 \
     -- -i --portmask=0x1 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=io \
     --nb-cores=1

    Note:
      -force-max-simd-bitwidth: This setting is used to determine the vector path for component selection.
                                And the default is avx2.

3. Configure traffic generator to send traffic as common step 2.

4. Record Test results as common step 3.
