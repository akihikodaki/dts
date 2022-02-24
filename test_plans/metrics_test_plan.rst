.. Copyright (c) 2010-2019 Intel Corporation
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

=======
metrics
=======

The Metrics implements a mechanism by which *producers* can publish numeric
information for later querying by *consumers*. Here dpdk-proc-info process is the
*consumers*. ``latency stats`` and ``bit rate`` are the two implements based
on metrics lib.

The dpdk-proc-info process use new command line option "--metrics" to display
metrics statistics.

Functionality:

* The library will register ethdev Rx/Tx callbacks for each active port,
  queue combinations.
* The library will register latency stats names with new metrics library.
* Rx packets will be marked with time stamp on each sampling interval.
* On Tx side, packets with time stamp will be considered for calculating
  the minimum, maximum, average latencies and also jitter.
* Average latency is calculated using exponential weighted moving average
  method.
* Minimum and maximum latencies will be low and high latency values
  observed so far.
* Jitter calculation is done based on inter packet delay variation.

note: DPDK technical document refer to ``doc/guides/prog_guide/metrics_lib.rst``

latency stats
=============

Latency stats measures minimum, average and maximum latencies, and jitter in
nano seconds.

bit rate
========

Calculates peak and average bit-rate statistics.

Prerequisites
=============

2x Intel® 82599 (Niantic) NICs (2x 10GbE full duplex optical ports per NIC)
plugged into the available PCIe Gen2 8-lane slots in two different configurations.

port topology diagram::

       packet generator                         DUT
        .-----------.                      .-----------.
        | .-------. |                      | .-------. |
        | | portA | | <------------------> | | port0 | |
        | | portB | | <------------------> | | port1 | |
        | '-------' |                      | '-------' |
        |           |                      |    nic    |
        '-----------'                      '-----------'

Test content
============

latency stats
-------------

The idea behind the testing process is to send different frames number of
different packets from packet generator to the DUT while these are being
forwarded back by the app and measure some of statistics. These data are queried
by the dpdk-proc app.

- min_latencyy_ns

  - Minimum latency in nano seconds

- max_latencyy_ns

  - Maximum latency in nano seconds

- avg_latencyy_ns

  - Average latency in nano seconds

- jittery_ns

  - Latency variation

bit rate
--------

The idea behind the testing process is to send different frames number of
different packets from packet generator to the DUT while these are being
forwarded back by the app and measure some of statistics. These data are queried
by the dpdk-proc app.

- mean_bits_in

  - Average rx bits rate

- mean_bits_out

  - Average tx bits rate

- peak_bits_in

  - peak rx bits rate

- peak_bits_out

  - peak tx bits rate

- ewma_bits_in

  - Average inbound bit-rate (EWMA smoothed)

- ewma_bits_out

  - Average outbound bit-rate (EWMA smoothed)

transmission packet format
--------------------------
UDP format::

    [Ether()/IP()/UDP()/Raw('\0'*60)]

transmission Frames size
------------------------
Then measure the forwarding throughput for different frame sizes.

Frame size(64/128/256/512/1024)

Test Case : test latency stats
==============================
#. Connect two physical ports to traffic generator.

#. bind two ports to igb_uio driver::

    ./tools/dpdk_nic_bind.py --bind=igb_uio 0000:xx:00.0 0000:xx:00.1

#. Start testpmd, set it in io fwd mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4  -- -i --latencystats=2
    testpmd> set fwd io
    testpmd> start

#. Configure packet flow in packet generator.

#. Use packet generator to send packets, continue traffic lasting several minitues.

#. run dpdk-proc to get latency stats data, query data at a average interval and
   get 5 times data::

   ./x86_64-native-linuxapp-gcc/app/dpdk-proc-info -- --metrics

#. latency stats has no reference standard data, only check non-zero and logic reasonable value.

Test Case : test bit rate
=========================
#. Connect two physical ports to traffic generator.

#. bind two ports to igb_uio driver.

    ./tools/dpdk_nic_bind.py --bind=igb_uio 00:08.0 00:08.1

#. Start testpmd, set it in io fwd mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4  -- -i --bitrate-stats=2
    testpmd> set fwd io
    testpmd> start

#. Configure packet flow in packet generator.

#. Use packet generator to send packets, continue traffic lasting several minitues.

#. run dpdk-proc to get latency stats data, query data at a average interval and
   get 5 times data::

   ./x86_64-native-linuxapp-gcc/app/dpdk-proc-info -- --metrics

#. Compare dpdk statistics data with packet generator statistics data.

Test Case : test bit rate peak value
====================================
#. Connect two physical ports to traffic generator.

#. bind two ports to igb_uio driver::

    ./tools/dpdk_nic_bind.py --bind=igb_uio 00:08.0 00:08.1

#. Start testpmd, set it in io fwd mode::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4  -- -i --bitrate-stats=2
    testpmd> set fwd io
    testpmd> start

#. Configure packet flow in packet generator.

#. Use packet generator to send packets, continue traffic lasting several minitues.

#. run dpdk-proc to get latency stats data, query data at a average interval and
   get 5 times data::

   ./x86_64-native-linuxapp-gcc/app/dpdk-proc-info -- --metrics

#. decline packet generator rate percent from 100%/80%/60%/20%, loop step 5/6.

#. check peak_bits_out/peak_bits_in should keep the first max value when packet
   generator work with decreasing traffic rate percent.
