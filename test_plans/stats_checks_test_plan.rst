.. # BSD LICENSE
    #
    # Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
    # Copyright © 2018[, 2019] The University of New Hampshire. All rights reserved.
    # All rights reserved.
    #
    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions
    # are met:
    #
    #   * Redistributions of source code must retain the above copyright
    #     notice, this list of conditions and the following disclaimer.
    #   * Redistributions in binary form must reproduce the above copyright
    #     notice, this list of conditions and the following disclaimer in
    #     the documentation and/or other materials provided with the
    #     distribution.
    #   * Neither the name of Intel Corporation nor the names of its
    #     contributors may be used to endorse or promote products derived
    #     from this software without specific prior written permission.
    #
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    # "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    # LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    # A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    # OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    # SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    # LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    # DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    # THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

=================
Stats Check tests
=================

The support of stats checks by Poll Mode Drivers consists of the ability
of the driver to properly report statistics upon request. Such statistics
should include number of packets and bytes sent and recieved, as well as
the number of dropped packets and transmission errors.

.. note::

   Maximum Packet Length = MTU(Maximum Transmission Unit) + 14(src mac + dst mac) + 4(CRC)
   e.g., 1518 = 1500 + 14 + 4

Prerequisites
=============

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

Assuming that ports ``0`` and ``1`` of the test target are directly connected
to the traffic generator, launch the ``testpmd`` application with the following
arguments::

  ./build/app/dpdk-testpmd -c ffffff -n 6 -- -i --portmask=0x3 --max-pkt-len=9600 \
  --tx-offloads=0x00008000

The -n command is used to select the number of memory channels. It should match the number of memory channels on that setup.

Setting tx-offload to 0x8000 and the maximum packet length
to 9600 (CRC included) makes input Jumbo Frames to be stored in multiple
buffers by the hardware RX engine.

Start packet forwarding in the ``testpmd`` application with the ``start``
command. Then, for each port on the target make the Traffic Generator
transmit a packet to the port of arbitrary size less than the MTU of
the target port, checking that the same amount of frames and bytes
are received back by the Traffic Generator from the port.

Functional Tests of Status Checks
=================================

Testing the support of Status Checks in Poll Mode Drivers consists of
configuring the gathering the initial status of a port, sending a
packet to that port, and checking the status of the port. The initial
status and the new status are then compared for expected differences.
The fields checked are RX-packets, RX-bytes, RX-errors, TX-packets,
TX-errors, and TX-bytes.

Test Case: Status Checks
====================================================

Check the initial state of the ports (Single example port shown)::

  testpmd> show port stats all
    ######################## NIC statistics for port 0  ########################
    RX-packets: 0        RX-missed: 0         RX-bytes:  0
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 0          TX-errors: 0          TX-bytes:  0

    Throughput (since last show)
    Rx-pps:            0
    Tx-pps:            0
    ############################################################################

Send a packet with size 50 bytes (Single example port show) ::

  testpmd> show port stats all
    ######################## NIC statistics for port 0  ########################
    RX-packets: 1        RX-missed: 0         RX-bytes:  50
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 0          TX-errors: 0          TX-bytes:  0

    Throughput (since last show)
    Rx-pps:            0
    Tx-pps:            0
    ############################################################################


Functional Tests of xstats Checks
==================================

Testing the support of xstatus Checks in Poll Mode Drivers consists of
configuring the gathering the initial status of a port, sending some
packets to that port, and checking the xstatus of the port.
This case will compare the initial xstatus and the new xstatus,
and compare the xstats and stats result.
The fields checked are RX-packets and TX-packets of each queue stats,
RX-packets, RX-bytes, TX-packets and TX-bytes of each port stats,
rx_good_packets and rx_good_bytes of each port xstats,
tx_good_packets and tx_good_bytes of each port xstats,
FVL does not support hardware per queue stats,
so we won't check rx and tx per queue stats.

Test Case: PF xstatus Checks
============================
1. Bind two PF ports to pmd driver::

    ./usertools/dpdk-devbind.py -b vfio-pci device_bus_id0 device_bus_id1

2. Launch testpmd and enable rss::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 -- -i --rxq=4 --txq=4
    testpmd> port config all rss all
    testpmd> set fwd mac

3. show the xstats before packet forwarding, all the value are 0.
4. Start forward and send 100 packets with random src IP address,
   then stop forward.

5. Check stats and xstats::

    testpmd> stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ------- Forward Stats for RX Port= 0/Queue= 0 -> TX Port= 1/Queue= 0 -------
    RX-packets: 29             TX-packets: 29             TX-dropped: 0

    ------- Forward Stats for RX Port= 0/Queue= 1 -> TX Port= 1/Queue= 1 -------
    RX-packets: 21             TX-packets: 21             TX-dropped: 0

    ------- Forward Stats for RX Port= 0/Queue= 2 -> TX Port= 1/Queue= 2 -------
    RX-packets: 24             TX-packets: 24             TX-dropped: 0

    ------- Forward Stats for RX Port= 0/Queue= 3 -> TX Port= 1/Queue= 3 -------
    RX-packets: 26             TX-packets: 26             TX-dropped: 0

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 100            RX-dropped: 0             RX-total: 100
    TX-packets: 0              TX-dropped: 0             TX-total: 0
    ----------------------------------------------------------------------------

    ---------------------- Forward statistics for port 1  ----------------------
    RX-packets: 0              RX-dropped: 0             RX-total: 0
    TX-packets: 100            TX-dropped: 0             TX-total: 100
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 100            RX-dropped: 0             RX-total: 100
    TX-packets: 100            TX-dropped: 0             TX-total: 100
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    testpmd> show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 100        RX-missed: 0          RX-bytes:  6000
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 0          TX-errors: 0          TX-bytes:  0

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################

    ######################## NIC statistics for port 1  ########################
    RX-packets: 0          RX-missed: 0          RX-bytes:  0
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 100        TX-errors: 0          TX-bytes:  6000

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################

    testpmd> show port xstats all
    ###### NIC extended statistics for port 0
    rx_good_packets: 100
    tx_good_packets: 0
    rx_good_bytes: 6000
    tx_good_bytes: 0
    ......
    rx_q0_packets: 0
    rx_q0_bytes: 0
    rx_q0_errors: 0
    rx_q1_packets: 0
    rx_q1_bytes: 0
    rx_q1_errors: 0
    rx_q2_packets: 0
    rx_q2_bytes: 0
    rx_q2_errors: 0
    rx_q3_packets: 0
    rx_q3_bytes: 0
    rx_q3_errors: 0
    tx_q0_packets: 0
    tx_q0_bytes: 0
    tx_q1_packets: 0
    tx_q1_bytes: 0
    tx_q2_packets: 0
    tx_q2_bytes: 0
    tx_q3_packets: 0
    tx_q3_bytes: 0
    ......
    ###### NIC extended statistics for port 1
    rx_good_packets: 0
    tx_good_packets: 100
    rx_good_bytes: 0
    tx_good_bytes: 6000
    rx_q0_packets: 0
    rx_q0_bytes: 0
    rx_q0_errors: 0
    rx_q1_packets: 0
    rx_q1_bytes: 0
    rx_q1_errors: 0
    rx_q2_packets: 0
    rx_q2_bytes: 0
    rx_q2_errors: 0
    rx_q3_packets: 0
    rx_q3_bytes: 0
    rx_q3_errors: 0
    tx_q0_packets: 0
    tx_q0_bytes: 0
    tx_q1_packets: 0
    tx_q1_bytes: 0
    tx_q2_packets: 0
    tx_q2_bytes: 0
    tx_q3_packets: 0
    tx_q3_bytes: 0

verify rx_good_packets, RX-packets of port 0 and tx_good_packets, TX-packets of port 1 are both 100.
rx_good_bytes, RX-bytes of port 0 and tx_good_bytes, TX-bytes of port 1 are the same.
FVL does not support hardware per queue stats,
so rx_qx_packets and rx_qx_bytes are both 0.
tx_qx_packets and tx_qx_bytes are both 0 too.

6. Clear stats::

      testpmd> clear port stats all

7. Check stats and xstats, verify rx_good_packets, RX-packets of port 0 and tx_good_packets, TX-packets of port 1 are both 0.

8. Repeat above 4 and 5 steps.

9. Clear xstats::

    testpmd> clear port xstats all

10. Check stats and xstats, verify rx_good_packets, RX-packets of port 0 and tx_good_packets, TX-packets of port 1 are both 0.


Test Case: VF xstats Checks
============================
1. Create one VF port on a kernel PF, then bind the VF to pmd driver::

    echo 1 > /sys/bus/pci/devices/device_bus_id/sriov_numvfs
    ./usertools/dpdk-devbind.py -s
    ./usertools/dpdk-devbind.py -b vfio-pci vf_bus_id

2. Launch testpmd on the VF and enable RSS::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 -- -i --rxq=4 --txq=4
    testpmd> port config all rss all
    testpmd> set fwd mac

3. Then run the same steps of PF xstats Checks, get same result.
note: because one port forwarding packets, so check rx and tx both in port 0.
