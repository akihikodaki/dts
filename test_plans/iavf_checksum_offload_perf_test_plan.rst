.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2023 Intel Corporation

=====================================================
Benchmark the performance of iavf checksum forwarding
=====================================================

Description
===========

Send packets with incorrect checksum,
verify dpdk can rx it and report the checksum error,
verify that the same number of packet are correctly received on the traffic
generator side.

Prerequisites
=============

1. Hardware:

   I40E driver NIC (Intel® Ethernet 700 Series XXV710, XL710, X710)
   ICE driver NIC (Intel® Ethernet 800 Series E810-CQDA2, E810-XXVDA4)

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
1. Bind PF ports to kernel driver(ice), then create 1 VF from each PF,
   take E810-CQDA2 for example::

    echo 1 > /sys/bus/pci/devices/0000\:17\:00.0/sriov_numvfs
    echo 1 > /sys/bus/pci/devices/0000\:4b\:00.0/sriov_numvfs

2. Ip link set VF trust on and spoofchk off on DUT::

    ip link set $PF_INTF vf 0 trust on
    ip link set $PF_INTF vf 0 spoofchk off

3. Set vf mac address::

    ip link set ens5f0 vf 0 mac 00:12:34:56:78:01
    ip link set ens6f0 vf 0 mac 00:12:34:56:78:02

4. Bind tested ports to vfio-pci::

    <dpdk_dir>#./usertools/dpdk-devbind.py -s
    0000:17:00.0 'Device 1592' if=ens5f0 drv=ice unused=vfio-pci
    0000:4b:00.0 'Device 1592' if=ens6f0 drv=ice unused=vfio-pci
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci <pci device id>
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci 0000:17:01.0
    <dpdk_dir>#./usertools/dpdk-devbind.py -b vfio-pci 0000:4b:01.0

5. Start dpdk-testpmd::

     <build_dir>/app/dpdk-testpmd -l 5,6 -n 8 --force-max-simd-bitwidth=512 \
     -- -i --portmask=0x3 --rxq=1 --txq=1 --txd=1024 --rxd=1024 --forward=io \
     --nb-cores=1 --enable-rx-cksum

    Note:
      -force-max-simd-bitwidth: set 512
      -enable-rx-cksum: enable rx checksum

6. Configure traffic generator to send traffic

    Test flow MAC table.

    +------+---------+------------+----------------+
    | Flow | Traffic | MAC        | MAC            |
    |      | Gen.    | Src.       | Dst.           |
    |      | Port    | Address    | Address        |
    +======+=========+============+================+
    |   1  |   TG0   | Random MAC | 00:12:34:56:01 |
    +------+---------+------------+----------------+
    |   2  |   TG1   | Random Mac | 00:12:34:56:02 |
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

    Set the packet length : 128 bytes-1518 bytes
    The IPV4 Dest Address increase with the num 1024.

7. Test results table.

    +-----------+------------+-------------+---------+
    |  Fwd_core | Frame Size |  Throughput |   Rate  |
    +===========+============+=============+=========+
    |  1C/1T    |    128     |  xxxxx Mpps |   xxx % |
    +-----------+------------+-------------+---------+
    |  1C/1T    |   ...      |  xxxxx Mpps |   xxx % |
    +-----------+------------+-------------+---------+

Test Case 1: test_perf_disable_checksum_offload_ipv4
----------------------------------------------------

1. Repeat common step 1-5.

2. Configure traffic generator to send traffic as common step 6.

3. Record Test results as common step 7.

4. Config SW checksum offload::

    testpmd>stop
    testpmd>set fwd csum
    testpmd>port stop all
    testpmd>csum set ip sw 0
    testpmd>csum set ip sw 1
    testpmd>port start all
    testpmd>start

5. Configure traffic generator to send traffic as common step 6.

   And configure the correct or incorrect ipv4 checksum separately.

6. Record Test results as common step 7.

Test Case 2: test_perf_disable_checksum_offload_vxlan
-----------------------------------------------------

1. Repeat common step 1-5.

2. Config SW checksum offload::

    testpmd>stop
    testpmd>set fwd csum
    testpmd>port stop all
    testpmd>csum set ip sw 0
    testpmd>csum set ip sw 1
    testpmd>port start all
    testpmd>start

3. Set the traffic flow as below:

    Ether / IPv4 / UDP / VXLAN / Ether / IPv4 / UDP / payload

    Set the packet length : 128 bytes-1518 bytes.

    Configure the correct or incorrect inner and outer ipv4 checksum and udp checksum separately.

4. Record Test results as common step 7.

Test Case 3: test_perf_enable_checksum_offload_ipv4
---------------------------------------------------

1. Repeat common step 1-5.

2. Config HW checksum offload::

    testpmd>stop
    testpmd>set fwd csum
    testpmd>port stop all
    testpmd>csum set ip hw 0
    testpmd>csum set ip hw 1
    testpmd>port start all
    testpmd>set promisc all on
    testpmd>start

3. Configure traffic generator to send traffic as common step 6.

   And configure the correct or incorrect ipv4 checksum separately.

5. Record Test results as common step 7.

Test Case 4: test_perf_enable_checksum_offload_vxlan
----------------------------------------------------

1. Repeat common step 1-5.

2. Config HW checksum offload::

    testpmd>stop
    testpmd>set fwd csum
    testpmd>port stop all
    testpmd>csum set ip hw 0
    testpmd>csum set ip hw 1
    testpmd>csum set udp hw 0
    testpmd>csum set udp hw 1
    testpmd>csum set outer-ip hw 0
    testpmd>csum set outer-ip hw 1
    testpmd>csum set outer-udp hw 0
    testpmd>csum set outer-udp hw 1
    testpmd>csum parse-tunnel on 0
    testpmd>csum parse-tunnel on 1
    testpmd>port start all
    testpmd>set promisc all on
    testpmd>start

3. Set the traffic flow as below:

    Ether / IPv4 / UDP / VXLAN / Ether / IPv4 / UDP / payload

    Set the packet length : 128 bytes-1518 bytes.

    Configure the correct or incorrect inner and outer ipv4 checksum and udp checksum separately.

4. Record Test results as common step 7.
