.. Copyright (c) <2011>, Intel Corporation
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

=============
Load Balancer
=============

This test case uses the Load Balancer sample application to benchmark the
concept of isolating the packet I/O task from the application specific workload.
A number of lcores are dedicated to handle the interaction with the NIC ports
(I/O lcores), while the rest of the lcores are dedicated to performing the
application processing (worker lcores). The worker lcores are totally oblivious
to the intricacies of the packet I/O activity and use the NIC-agnostic interface
provided by SW rings to exchange packets with the I/O cores.

Prerequisites
=============

1. Hardware requirements

-  For each CPU socket, each memory channel should be populated with at least
   1x DIMM.
-  If the PCIe controller is on the CPU, then each CPU socket is populated with
   the same number of NICs (2x or 4x NICs per CPU socket);
-  Special PCIe restrictions may be required for performance. For example, the
   following requirements should be met for 10GbE NICs:

    -  NICs are plugged into PCIe Gen2 or Gen3 slots;
    -  For PCIe Gen2 slots, the number of lanes should be 8x or higher;
    -  A single port from each NIC card should be used, so for 4x ports, 4x NICs
       should be connected to the traffic generator.

2. BIOS requirements

-  Hyper-Threading Technology is ENABLED
-  Hardware Prefetcher is DISABLED
-  Adjacent Cache Line Prefetch is DISABLED
-  Direct Cache Access is DISABLED

3. Linux kernel requirements

-  Linux kernel has the following features enabled: huge page support, UIO, HPET
-  Appropriate number of huge pages are reserved at kernel boot time
-  The IDs of the hardware threads (logical cores) per each CPU socket can be
   determined by parsing the file /proc/cpuinfo. The naming convention for the
   logical cores is: C{x.y.z} = hyper-thread z of physical core y of CPU socket
   x, with typical values of x = 0 .. 3, y = 0 .. 7, z = 0 .. 1. Logical cores
   C{0.0.1} and C{0.0.1} should be avoided while executing the test, as they
   are used by the Linux kernel for running regular processes.

4. Software application configuration

The application configuration is done through the command line:

-  -c COREMASK: Reunion of all the cores specified by the --rx, --tx and --w
   parameters.
-  --rx and --tx: These parameters are used to provide the list of lcores used
   for packet I/O, plus the list of the RX ports & queues, as well as the list
   of TX ports, that are handled by each of the packet I/O lcores;
-  The RX and TX of the NICs that are physically attached (through PCIe) to a
   specific CPU socket should always be handled by lcores from the same socket;
-  The RX and TX of the same port can be handled by different lcores, depending
   on the usecase, therefore the set of RX lcores can be different than the set
   of TX lcores;
-  Typical configurations enabled for the I/O cores for each CPU socket (as long
   as the conditions below are met, the actual lcore IDs are irrelevant):

    -  Single lcore handling the RX and TX for all the NICs connected to its CPU
       socket. Its sibling hyper-thread should not be used by the application;

-  One lcore handling the RX and TX for a single NIC port (with its sibling
   hyper-thread not used by the application). For each CPU socket, there are N
   physical cores used for packet I/O for N NIC ports;
-  One lcore handling the RX for all the NIC ports connected to its CPU socket
   and another lcore handling the TX for the same NIC ports (with the sibling
   hyper-threads not used by the application). For each CPU socket, there are 2
   physical cores used for packet I/O for N NIC ports;
-  --w: This parameter specifies the list of worker lcores;

    -  A worker lcore cannot be a packet I/O lcore;
    -  Typical configurations enabled for each CPU socket: 1 / 2 / 4 / 8. Each
       worker should be allocated on a different physical core. For 8 workers
       (per CPU socket), if not enough physical cores, both hyper-threads of 4
       physical cores can be used. As long as these conditions are met, the
       actual lcore IDs are irrelevant.

-  --lpm: IPv4 routing table;
    -  Typically, there is a single rule for each TX port and the address spaces
       of the rules do not overlap, e.g. for each TX_PORT used by the
       application, the rule "10.0.TX_PORT.0/24 => TX_PORT" is included in the
       list.
-  --rsz: Ring sizes
    -  Typically, the default values are used (parameter not present in the
       command line).
-  --bsz: Burst sizes
    -  Typically, the default values are used (parameter not present in the
       command line).
-  --pos-lb: Position of the 1-byte header field within the input packet that is
   used to determine the worker ID for each packet

    -  Typically, the default value is used (parameter not present in the
       command line).

5. Traffic generator configuration

The application is used to benchmark the penalty of packets going across
different CPU sockets. In the general case, the input packets are RX-ed by NIC
connected to CPU socket X, dispatched to worker running on CPU socket Y, TX-ed
by NIC connected to CPU socket Z. The typical cases under test are: AAA, AAB,
ABB, ABC (for 2-socket systems, ABC is actually ABA).

The worker ID is determined by reading a 1-byte field from the input packet. Its
position is specified using the --pos-lb command line argument. For convenience,
the --pos-lb argument typically points to the last byte of the IPv4 source
address, e.g. the IPv4 source address for a traffic flow that shoud be processed
by WORKER_ID is: 0.0.0.WORKER_ID.

The TX port is determined by the LPM rule that is hit by the IPv4 destination
address field read from each packet. Therefore, the traffic generator
configuration has to be in sync with the routing table of the application
(provided using the --lpm parameter). Given the convention described above of
LPM rules of: "10.0.TX_PORT.0/24 => TX_PORT", then packets with IPv4 destination
address of 10.0.TX_PORT.1 will be sent out by TX_PORT, regardless of the worker
lcore processing them.

For a specific test case, the recommended flow configuration for each traffic
generator port (connected to a NIC attached to CPU socket X) is to create a
traffic flow for each pair of (worker on CPU socket Y, NIC TX port on CPU
socket Z) and equally divide the TX rate amongst all the traffic flows on the
same traffic generator port. This guarantees that all the workers on CPU
socket Y will be hit evenly and none of the NIC TX ports on CPU socket Z will be
oversubscribed.

In this case, the same set of application command lines (testing different
packet I/O and worker set configurations) can be applied with no modifications
to test scenarios AAA, AAB, ABB, ABC/ABA by simply modifying two fields within
each of the traffic flows sent by the traffic generator on each of its ports.

Test Case: Load Balancer
========================

Assuming that Logical core 4, 5, 6, 7 are connected to a traffic generator,
launch the ``load_balancer`` with the following arguments::

  ./examples/load_balancer/build/load_balancer -l 3-7 -n 4 -- \
  --rx "(0,0,3),(1,0,3),(2,0,3),(3,0,3)" \
  --tx "(0,3),(1,3),(2,3),(3,3)" --w "4,5,6,7" \
  --lpm "1.0.0.0/24=>0;1.0.1.0/24=>1;1.0.2.0/24=>2;1.0.3.0/24=>3; " \
  --bsz "(10, 10), (10, 10), (10, 10)" --pos-lb 29

If the app run successfully, it will be the same as the shown in the terminal. ::

  ...
  LPM rules:
        0: 1.0.0.0/24 => 0;
        1: 1.0.1.0/24 => 1;
        2: 1.0.2.0/24 => 2;
        3: 1.0.3.0/24 => 3;
  Ring sizes: NIC RX = 1024; Worker in = 1024; Worker out = 1024; NIC TX = 1024;
  Burst sizes: I/O RX (rd = 10, wr = 10); Worker (rd = 10, wr = 10); I/O TX (rd = 10, wr = 10)
  Logical core 4 (worker 0) main loop.
  Logical core 5 (worker 1) main loop.
  Logical core 6 (worker 2) main loop.
  Logical core 7 (worker 3) main loop.
  Logical core 3 (I/O) main loop.
