.. Copyright (c) <2021>, Intel Corporation
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

   - Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.

   - Neither the name of Intel Corporation nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.

==================
NIC VF Smoke Test
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

    niantic/fortville/columbiaville

2. Software:

    dpdk: http://dpdk.org/git/dpdk
    scapy: http://www.secdev.org/projects/scapy/

3. Compile DPDK::

    CC=gcc meson -Denable_kmods=True -Dlibdir=lib --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc

4. Get the pci device id of DUT, for example::

    ./usertools/dpdk-devbind.py -s

    0000:86:01.0 'Device 1593' if=enp134s0f0 drv=ice unused=vfio-pci

5. Generate 1 VFs on PF::

    echo 1 > /sys/bus/pci/devices/0000:86:01.0/sriov_numvfs

    ./usertools/dpdk-devbind.py -s
    0000:86:01.0 'Ethernet Adaptive Virtual Function 1889' if=enp134s1 drv=iavf unused=vfio-pci

6. Set VF MAC address::

    ip link set enp134s0f0 vf 0 mac 00:01:23:45:67:89

7. Bind VF to dpdk driver::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:86:01.0

8. Launch dpdk on VF::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:86:01.0 --file-prefix=pf -- -i --max-pkt-len=9600 --tx-offloads=0x00008000 --rxq=4 --txq=4
    testpmd> set fwd mac
    testpmd> set verbose 3
    testpmd> start
    testpmd> show port info all


Test Case 1: test enable and disable jumbo frame
====================================================

1. set fwd mode is mac::

    testpmd> set fwd mac
    testpmd> set verbose 3
    testpmd> start

2. Send a packet with size 9601 bytes ::

    testpmd> show port stats 0

    ######################## NIC statistics for port 0  ########################
    RX-packets: 0          RX-errors: 1         RX-bytes: 0
    TX-packets: 0          TX-errors: 0         TX-bytes: 0
    ############################################################################

Verify that TX-bytes on port 0 and RX-bytes on port 0 are 0.

3. Send a packet with size 9600 bytes ::

    testpmd> show port stats 0

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-errors: 0         RX-bytes: 9600
    TX-packets: 1          TX-errors: 0         TX-bytes: 9600
    ############################################################################

Verify that TX-bytes on port 0 and RX-bytes on port 0 are 9600.

4. Set mtu is 1500 ::

    testpmd> port config mtu 1500

5. Send a packet with size 1518 bytes ::

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
