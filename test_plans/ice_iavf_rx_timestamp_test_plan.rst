.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=============================
ICE IAVF Support Rx Timestamp
=============================

Description
===========
The VF driver is able to enable rx timestamp offload, the 64 bits timestamp is able
to extracted from the flexible Rx descriptor and be stored in mbuf's dynamic field.
The received packets have timestamp values, and the timestamp values are incremented.

.. note::

    Require kernel support rx timestamp offload function in VF.

Prerequisites
=============

Topology
--------
DUT port 0 <----> Tester port 0

Hardware
--------
Supported NICs: Intel® Ethernet 800 Series E810-XXVDA4/E810-CQ

Software
--------
dpdk: http://dpdk.org/git/dpdk
scapy: http://www.secdev.org/projects/scapy/

General Set Up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110

2. Get the pci device id and interface of DUT and tester.
   For example, 0000:3b:00.0 and 0000:3b:00.1 is pci device id,
   ens785f0 and ens785f1 is interface::

    <dpdk dir># ./usertools/dpdk-devbind.py -s

    0000:3b:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci
    0000:3b:00.1 'Device 159b' if=ens785f1 drv=ice unused=vfio-pci

3. Generate 1 VF on PF0, set mac address for this VF::

    # echo 1 > /sys/bus/pci/devices/0000:3b:00.0/sriov_numvfs
    # ip link set ens785f0 vf 0 mac 00:11:22:33:44:55


4. Bind the DUT port to dpdk::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>

Test Case
=========
Common Steps
------------
All the packets in this test plan use below settings:
dst mac: 00:11:22:33:44:55
ipv4 src: 192.168.0.2
ipv4 dst: 192.168.0.3
ipv6 src: 2001::2
ipv6 dst: 2001::3
sport: 1026
dport: 1027
count: 3

1. Check driver is IAVF::

    testpmd> show port info all

2. Set fwd engine::

    testpmd> set fwd rxonly

3. Set verbose::

    testpmd> set verbose 1

4. Start testpmd::

    testpmd> start

5. Send ether packets, record the timestamp values and check the timestamp values are incremented::

    >>> sendp([Ether(dst="<dst mac>")/("X"*480)], iface="<tester interface>",count=<count>)

6. Send ipv4 packets, record the timestamp values and check the timestamp values are incremented::

    >>> sendp([Ether(dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*480)], iface="<tester interface>",count=<count>)

7. Send ipv6 packets, record the timestamp values and check the timestamp values are incremented::

    >>> sendp([Ether(dst="<dst mac>")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")/("X"*480)], iface="<tester interface>",count=<count>)

8. Send ipv4-udp packets, record the timestamp values and check the timestamp values are incremented::

    >>> sendp([Ether(dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/UDP(sport=<sport>, dport=<dport>)/("X"*480)], iface="<tester interface>",count=<count>)

9. Send ipv6-udp packets, record the timestamp values and check the timestamp values are incremented::

    >>> sendp([Ether(dst="<dst mac>")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")/UDP(sport=<sport>, dport=<dport>)/("X"*480)], iface="<tester interface>",count=<count>)

10. Send ipv4-tcp packets, record the timestamp values and check the timestamp values are incremented::

    >>> sendp([Ether(dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/TCP(sport=<sport>, dport=<dport>)/("X"*480)], iface="<tester interface>",count=<count>)

11. Send ipv6-tcp packets, record the timestamp values and check the timestamp values are incremented::

    >>> sendp([Ether(dst="<dst mac>")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")/TCP(sport=<sport>, dport=<dport>)/("X"*480)], iface="<tester interface>",count=<count>)

12. Send ipv4-sctp packets, record the timestamp values and check the timestamp values are incremented::

    >>> sendp([Ether(dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/SCTP(sport=<sport>, dport=<dport>)/("X"*480)], iface="<tester interface>",count=<count>)

13. Send ipv6-sctp packets, record the timestamp values and check the timestamp values are incremented::

    >>> sendp([Ether(dst="<dst mac>")/IPv6(src="<ipv6 src>",dst="<ipv6 dst>")/SCTP(sport=<sport>, dport=<dport>)/("X"*480)], iface="<tester interface>",count=<count>)

Test Case 1: Without timestamp, check no timestamp
--------------------------------------------------
This case is designed to check no timestamp value while testpmd not enable rx timestamp.

Test Steps
~~~~~~~~~~
1. Start testpmd with different command line::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 -a 3b:01.0 -- -i --rxq=16 --txq=16

2. Send packets as common steps, check no timestamp value.

Test Case 2: Single queue With timestamp, check timestamp
---------------------------------------------------------
This case is designed to check single queue has timestamp values and the timestamp values are incremented.

Test Steps
~~~~~~~~~~
1. Start testpmd with different command line::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 -a 3b:01.0 -- -i --enable-rx-timestamp

2. Send packets as common steps, check single queue has timestamp values and the timestamp values are incremented.

    testpmd> port 0/queue 0: received 3 packets
    src=00:00:00:02:00:00 - dst=00:11:22:33:44:55 - type=0x9000 - length=494 - nb_segs=1 - timestamp 1663602166832732634  - hw ptype: L2_ETHER  - sw ptype: L2_ETHER  - l2_len=14 - Receive queue=0x0
    ol_flags: RTE_MBUF_F_RX_L4_CKSUM_UNKNOWN RTE_MBUF_F_RX_IP_CKSUM_UNKNOWN RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
    src=00:00:00:02:00:00 - dst=00:11:22:33:44:55 - type=0x9000 - length=494 - nb_segs=1 - timestamp 1663602166832881817  - hw ptype: L2_ETHER  - sw ptype: L2_ETHER  - l2_len=14 - Receive queue=0x0
    ol_flags: RTE_MBUF_F_RX_L4_CKSUM_UNKNOWN RTE_MBUF_F_RX_IP_CKSUM_UNKNOWN RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
    src=00:00:00:02:00:00 - dst=00:11:22:33:44:55 - type=0x9000 - length=494 - nb_segs=1 - timestamp 1663602166833010250  - hw ptype: L2_ETHER  - sw ptype: L2_ETHER  - l2_len=14 - Receive queue=0x0
    ol_flags: RTE_MBUF_F_RX_L4_CKSUM_UNKNOWN RTE_MBUF_F_RX_IP_CKSUM_UNKNOWN RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN

Test Case 3: Multi queues With timestamp, check timestamp
---------------------------------------------------------
This case is designed to check multi queues have timestamp values and the timestamp values are incremented.

Test Steps
~~~~~~~~~~
1. Start testpmd with different command line::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 -a 3b:01.0 -- -i --rxq=16 --txq=16 --enable-rx-timestamp

2. Send packets as common steps, check multi queues have timestamp values and the timestamp values are incremented.
