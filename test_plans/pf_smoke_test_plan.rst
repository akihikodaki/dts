.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

==================
NIC PF Smoke Test
==================

Description
===========
Test the basic functions of dpdk.
1. Port connection status.
2. Launch testpmd normally.
3. Basic rx and tx.

Prerequisites
=============

1. Hardware:

    82599/Intel® Ethernet 700 Series/Intel® Ethernet 800 Series

2. Software:

    dpdk: http://dpdk.org/git/dpdk
    scapy: http://www.secdev.org/projects/scapy/

3. Compile DPDK::

    CC=gcc meson -Denable_kmods=True -Dlibdir=lib --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc

4. Get the pci device id of DUT, for example::

    ./usertools/dpdk-devbind.py -s

    0000:86:00.0 'Device 1593' if=enp134s0f0 drv=ice unused=vfio-pci

7. Bind PF to dpdk driver::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:86:00.0

8. Launch dpdk on PF::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:86:00.0 --file-prefix=pf -- -i --rxq=4 --txq=4
    testpmd> set fwd mac
    testpmd> set verbose 3
    testpmd> start
    testpmd> show port info all

Test Case 1: test enable and disable jumbo frame
====================================================
1. when launch dpdk on PF, add  parameter '--max-pkt-len=9600 --tx-offloads=0x00008000'

2. set fwd mode is mac::

    testpmd> set fwd mac
    testpmd> set verbose 3
    testpmd> start

3. Send a packet with size 9601 bytes ::

    testpmd> show port stats 0

    ######################## NIC statistics for port 0  ########################
    RX-packets: 0          RX-errors: 1         RX-bytes: 0
    TX-packets: 0          TX-errors: 0         TX-bytes: 0
    ############################################################################

Verify that TX-bytes on port 0 and RX-bytes on port 0 are 0.

4. Send a packet with size 9600 bytes ::

    testpmd> show port stats 0

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-errors: 0         RX-bytes: 9600
    TX-packets: 1          TX-errors: 0         TX-bytes: 9600
    ############################################################################

Verify that TX-bytes on port 0 and RX-bytes on port 0 are 9600.

5. Set mtu is 1500 ::

    testpmd> port config mtu 1500

6. Send a packet with size 1518 bytes ::

    testpmd> show port stats 0

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-errors: 0         RX-bytes: 1518
    TX-packets: 1          TX-errors: 0         TX-bytes: 1518
    ############################################################################

Verify that TX-bytes on port 0 and RX-bytes on port 0 are 1518

7. Send a packet with size 1519 bytes ::

    testpmd> show port stats 0

    ######################## NIC statistics for port 0  ########################
    RX-packets: 0          RX-errors: 1         RX-bytes: 0
    TX-packets: 0          TX-errors: 0         TX-bytes: 0
    ############################################################################

Verify that TX-bytes on port 0 and RX-bytes on port 1 are 0

Test Case 2: test RSS
====================================================
1. set fwd mode is rxonly::

    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

4. Send different hash types' packets with different keywords, then check rx port
    could receive packets by different queues::

      sendp([Ether(dst="00:01:23:45:67:89")/IP(src="192.168.0.4", dst=RandIP())], iface="eth3")

Test Case 3: test reset RX/TX queues
====================================================
1. Run ``port stop all`` to stop all ports.

2. Run ``port config all rxq 2`` to change the number of receiving queues to two.

3. Run ``port config all txq 2`` to change the number of transmitting queues to two.

4. Run ``port start all`` to restart all ports.

5. Check with ``show config rxtx`` that the configuration for these parameters changed.

6. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check if testpmd is able to receive and forward packets
   successfully.
