.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

==============================================================
Benchmark the performance of header split forwarding with E810
==============================================================

Description
===========
When Rx queue is configured with RTE_ETH_RX_OFFLOAD_BUFFER_SPLIT offload
and corresponding protocol, packets received will be directly split into
two different mempools.

Prerequisites
=============

1. Hardware:

   1.1) header split perf test for Intel® Ethernet Network Adapter E810-CQDA2:
        1 NIC or 2 NIC cards attached to the same processor and 1 port used of each NIC.
   1.2) header split perf test for Intel® Ethernet Network Adapter E810-XXVDA4:
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
    0000:4b:00.0 'Device 1592' if=ens6f0 drv=ice unused=vfio-pci
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci <pci device id>
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci 0000:17:00.0
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci 0000:4b:00.0

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
    |   3  |   TG2   | Random Mac | 11:22:33:44:55 |
    +------+---------+------------+----------------+
    |   4  |   TG3   | Random Mac | 11:22:33:44:55 |
    +------+---------+------------+----------------+

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

Test Case 1: test_perf_enable_header_split_rx_on
------------------------------------------------

1. Bind PF ports to dpdk driver as common step 1::

    ./usertools/dpdk-devbind.py -b vfio-pci 17:00.0 4b:00.0

2. Start dpdk-testpmd::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=64 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=rxonly \
     --nb-cores=1 --mbuf-size=2048,2048

    Note:
      -force-max-simd-bitwidth: Set 64, the feature only support 64.
      -mbuf-size=2048,2048: config two mempools.

3. Config mac split::
    
    testpmd>port stop all
    testpmd>port config 0 rx_offload buffer_split on
    testpmd>port config 1 rx_offload buffer_split on
    testpmd>set rxhdrs eth
    testpmd>port start all
    testpmd>start

4. Configure traffic generator to send traffic as common step 2.

5. Record Test results as common step 3.

Test case 2: test_perf_disable_header_split_rx_on
-------------------------------------------------

1. Bind PF ports to dpdk driver as common step 1::

    ./usertools/dpdk-devbind.py -b vfio-pci 17:00.0 4b:00.0

2. Start dpdk-testpmd::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=64 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=rxonly \
     --nb-cores=1

     Note:
      -force-max-simd-bitwidth: Set 64, the feature only support 64.

3. Configure traffic generator to send traffic as common step 2.

4. Record Test results as common step 3.

5. Start dpdk-testpmd::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=64 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=rxonly \
     --nb-cores=1 --mbuf-size=2048,2048

     Note:
      -force-max-simd-bitwidth: Set 64, the feature only support 64.
      -mbuf-size=2048,2048: config two mempools.

6. Configure traffic generator to send traffic as common step 2.

7. Record Test results as common step 3.

Test case 3: test_perf_enable_header_split
------------------------------------------

1. Bind PF ports to dpdk driver as common step 1::

    ./usertools/dpdk-devbind.py -b vfio-pci 17:00.0 4b:00.0

2. Start dpdk-testpmd::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=64 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=rxonly \
     --nb-cores=1 --mbuf-size=2048,2048

    Note:
      -force-max-simd-bitwidth: Set 64, the feature only support 64.
      -mbuf-size=2048,2048: config two mempools.

3. Config udp split::
    
    testpmd>port stop all
    testpmd>port config 0 rx_offload buffer_split on
    testpmd>port config 1 rx_offload buffer_split on
    testpmd>set rxhdrs inner-ipv4-udp
    testpmd>port start all
    testpmd>start
    
4. Config traffic generator as common step 2.
   
5. Record Test results as common step 3.

6. Config traffic generator with udp flow.

7. Record Test results as common step 3.

Test case 4: test_perf_disable_header_split
-------------------------------------------

1. Bind PF ports to dpdk driver as common step 1::

    ./usertools/dpdk-devbind.py -b vfio-pci 17:00.0 4b:00.0

2. Start dpdk-testpmd::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=64 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=io \
     --nb-cores=1

    Note:
      -force-max-simd-bitwidth: Set 64, the feature only support 64.

3. Configure traffic generator to send traffic as common step 2.

4. Record Test results as common step 3.

5. Start dpdk-testpmd::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=64 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=io \
     --nb-cores=1 --mbuf-size=2048,2048

    Note:
      -force-max-simd-bitwidth: Set 64, the feature only support 64.
      -mbuf-size=2048,2048: config two mempools.

6. Configure traffic generator to send traffic as common step 2.

7. Record Test results as common step 3.
