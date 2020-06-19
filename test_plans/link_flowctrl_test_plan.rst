.. Copyright (c) <2010-2017>, Intel Corporation
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

================================
Ethernet Link Flow Control Tests
================================

The support of Ethernet link flow control features by Poll Mode Drivers
consists in:

- At the receive side, if packet buffer is not enough, NIC will send out the
  pause frame to peer and ask the peer to slow down the Ethernet frame #
  transmission.

- At the transmit side, if pause frame is received, NIC will slow down the
  Ethernet frame transmission according to the pause frame.

MAC Control Frame Forwarding consists in:

- Control frames (PAUSE Frames) are taken by the NIC and do not pass to the
  host.

- When Flow Control and MAC Control Frame Forwarding are enabled the PAUSE
  frames will be passed to the host and can be handled by testpmd.

.. note::

   Priority flow control is not included in this test plan.

Configuration Functions in testpmd:

  Set the link flow control parameter on a port::

    testpmd> set flow_ctrl rx (on|off) tx (on|off) (high_water) (low_water) \
           (pause_time) (send_xon) mac_ctrl_frame_fwd (on|off) \
           autoneg (on|off) (port_id)

  * ``high_water`` (integer): High threshold value to trigger XOFF.

  * ``low_water`` (integer): Low threshold value to trigger XON.

  * ``pause_time`` (integer): Pause quota in the Pause frame.

  * ``send_xon`` (0/1): Send XON frame.

  * ``mac_ctrl_frame_fwd``: Enable receiving MAC control frames.

  * ``autoneg``: Change the auto-negotiation parameter.

  .. note::

     the high_water, low_water, pause_time, send_xon are configured into the
     NIC register. It is not necessary to validate the accuracy of these parameters.
     And what change it can cause. The port_id is used to indicate the NIC to be
     configured. In certain case, a system can contain multiple NIC. However the NIC
     need not be configured multiple times.


Prerequisites
=============

Assuming that ports ``0`` and ``2`` are connected to a traffic generator,
launch the ``testpmd`` with the following arguments::

  ./build/app/testpmd -cffffff -n 3 -- -i --burst=1 --txpt=32 \
  --txht=8 --txwt=0 --txfreet=0 --rxfreet=64 --mbcache=250 --portmask=0x5

The -n command is used to select the number of memory channels.
It should match the number of memory channels on that setup.

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id


Test Case: Ethernet link flow control
=====================================
This case series are focus on ``Ethernet link flow control features``, requires a high-speed packet generator, such as ixia.

Subcase: test_perf_flowctrl_on_pause_fwd_on
-------------------------------------------
Enable both link flow control and PAUSE frame forwarding::

  testpmd> set flow_ctrl rx on tx on high_water low_water pause_time
  send_xon mac_ctrl_frame_fwd on autoneg on port_id

Setup the ``csum`` forwarding mode::

  testpmd> set fwd csum
  Set csum packet forwarding mode

Start the packet forwarding::

  testpmd> start
    csum packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Validate the NIC can generate the pause frame(``tx on``).
Configure the traffic generator to send IPv4/UDP packet at the length of 66Byte
at the line speed (10G). Because the 66Byte packet cannot reach line rate when
running with testpmd, so it is expected that the pause frame will be sent to the
peer (traffic generator). Ideally this mechanism can avoid the packet loss. And
this depends on high_water/low_water and other parameters are configured properly.
It is strongly recommended that the user look into the data sheet before doing
any flow control configuration. By default, the flow control on 10G is disabled.
the flow control for 1G is enabled.

Validate the NIC can deal with the pause frame(``rx on``).
Configure the traffic generator to send out large amount of pause frames, this
will cause the NIC to disable / slow down the packet transmission according to
the pause time. Once the traffic generator stop sending the pause frame, the NIC
will restore the packet transmission to the expected rate.

Subcase: test_perf_flowctrl_on_pause_fwd_off
--------------------------------------------
Enable link flow control and Disable PAUSE frame forwarding::

  testpmd> set flow_ctrl rx on tx on high_water low_water pause_time
  send_xon mac_ctrl_frame_fwd off autoneg on port_id

Validate same behavior as ``test_perf_flowctrl_on_pause_fwd_on``

Subcase: test_perf_flowctrl_rx_on
---------------------------------
Enable only rx link flow control::

  testpmd> set flowctrl rx on tx off high_water low_water pause_time
  send_xon mac_ctrl_frame_fwd off autoneg on port_id

Validate the NIC can deal with the pause frame(``rx on``).

Subcase: test_perf_flowctrl_off_pause_fwd_off
---------------------------------------------
Disable both link flow control and PAUSE frame forwarding.
This is the default mode for 10G PMD, by default, testpmd is running on this mode.
no need to execute any command::

  testpmd> set flowctrl rx off tx off high_water low_water pause_time
  send_xon mac_ctrl_frame_fwd off autoneg on port_id

Validate the NIC won't generate the pause frame when the packet buffer is not
enough. Packet loss can be observed.
Validate the NIC will not slow down the packet transmission after receiving the
pause frame.

Subcase: test_perf_flowctrl_off_pause_fwd_on
--------------------------------------------
Disable link flow control and enable PAUSE frame forwarding::

  testpmd> set flowctrl rx off tx off high_water low_water pause_time
  send_xon mac_ctrl_frame_fwd on autoneg on port_id

Validate same behavior as ``test_perf_flowctrl_off_pause_fwd_off``

Subcase: test_perf_flowctrl_tx_on
---------------------------------
Enable only tx link flow control::

  testpmd> set flowctrl rx off tx on high_water low_water pause_time
  send_xon mac_ctrl_frame_fwd off autoneg on port_id

Validate same behavior as test_perf_flowctrl_on_pause_fwd_off

Subcase: test_perf_flowctrl_on_port_stop_start
----------------------------------------------
Link flow control setting still working after port stop/start.

* ``enable`` Link flow control::

    testpmd> set flow_ctrl rx on tx on high_water low_water pause_time
    send_xon mac_ctrl_frame_fwd off autoneg on port_id

  validate behavior same as ``test_perf_flowctrl_on_pause_fwd_off``.

  Stop and start port::

    testpmd> stop
    testpmd> port stop 0
    testpmd> port start 0
    testpmd> start

  validate behavior same as ``test_perf_flowctrl_on_pause_fwd_off``.


* ``disable`` Link flow control::

    testpmd> set flowctrl rx off tx off high_water low_water pause_time
    send_xon mac_ctrl_frame_fwd off autoneg on port_id

  validate behavior same as ``test_perf_flowctrl_off_pause_fwd_off``.

  Stop and start port::

    testpmd> stop
    testpmd> port stop 0
    testpmd> port start 0
    testpmd> start

  validate behavior same as ``test_perf_flowctrl_off_pause_fwd_off``.


Test Case: MAC Control Frame Forwarding
=======================================
This case series foucs on ``MAC Control Frame Forwarding``, no requirment of
high-speed packets, it's very friendship to use scapy as packet generator.

Subcase: test_flowctrl_off_pause_fwd_off
----------------------------------------
PAUSE Frames will not be received by testpmd while Flow Control disabled and
MAC Control Frame Forwarding disabled::

  testpmd> set flow_ctrl rx off tx off 300 50 10 1 mac_ctrl_frame_fwd off autoneg off 0

Send PAUSE packets to DUT with below options:

* Regular frame (correct src and dst mac addresses and opcode)
* Wrong source frame (wrong src, correct and dst mac address and correct opcode)
* Wrong opcode frame (correct src and dst mac address and wrong opcode)
* Wrong destination frame (correct src mac and opcode, wrong dst mac address)

Validate no packet received by testpmd according to ``show port stats all``

Subcase: test_flowctrl_off_pause_fwd_on
---------------------------------------
All PAUSE Frames will be forwarded by testpmd while Flow Control disabled and
MAC Control Frame Forwarding enabled::

  testpmd> set flow_ctrl rx off tx off 300 50 10 1 mac_ctrl_frame_fwd on autoneg off 0

Send PAUSE packets to DUT with same options as ``test_flowctrl_off_pause_fwd_off``

Validate port statistic match below table

.. table::

   +-------+-----------------+---------------+
   |   #   | Frames          | Received      |
   +=======+=================+===============+
   |   0   | Regular frame   | Yes           |
   +-------+-----------------+---------------+
   |   1   | Wrong src mac   | Yes           |
   +-------+-----------------+---------------+
   |   2   | Wrong opcode    | Yes           |
   +-------+-----------------+---------------+
   |   3   | Wrong dst mac   | Yes           |
   +-------+-----------------+---------------+

Subcase: test_pause_fwd_port_stop_start
---------------------------------------
MAC Control Frame Forwarding setting still working after port stop/start.

* ``enable`` MAC Control Frame Forwarding, and validate packets are received::

    testpmd> set flow_ctrl mac_ctrl_frame_fwd on 0

  Send regular PAUSE packets to DUT, and validate packets are received.

  Stop and start port::

    testpmd> stop
    testpmd> port stop 0
    testpmd> port start 0
    testpmd> start

  Send regular PAUSE packets to DUT, and validate packets are received.


* ``disable`` MAC Control Frame Forwarding, and validate ``no`` packets are received::

    testpmd> set flow_ctrl mac_ctrl_frame_fwd off 0

  Send regular PAUSE packets to DUT, and validate ``no`` packets are received.

  Stop and start port::

    testpmd> stop
    testpmd> port stop 0
    testpmd> port start 0
    testpmd> start

  Send regular PAUSE packets to DUT, and validate ``no`` packets are received.
