.. Copyright (c) <2011-2019>, Intel Corporation
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

=====================================
Performance-thread  performance Tests
=====================================

The Performance-Thread results are produced using ``l3fwd-thread`` application.

For more information about Performance Thread sameple applicaton please refer to 
link: http://doc.dpdk.org/guides/sample_app_ug/performance_thread.html

Prerequisites
=============

1. Hardware requirements:

    - For each CPU socket, each memory channel should be populated with at least 1x DIMM
    - Board is populated with 4x 1GbE or 10GbE ports. Special PCIe restrictions may
      be required for performance. For example, the following requirements should be
      met for Intel 82599 (Niantic) NICs:

        - NICs are plugged into PCIe Gen2 or Gen3 slots
        - For PCIe Gen2 slots, the number of lanes should be 8x or higher
        - A single port from each NIC should be used, so for 4x ports, 4x NICs should
          be used

    - NIC ports connected to traffic generator. It is assumed that the NIC ports
      P0, P1 (as identified by the DPDK application) are connected to the
      traffic generator ports TG0, TG1. The application-side port mask of
      NIC ports P0, P1 is noted as PORTMASK in this section.

2. BIOS requirements:

    - Intel Hyper-Threading Technology is ENABLED
    - Hardware Prefetcher is DISABLED
    - Adjacent Cache Line Prefetch is DISABLED
    - Direct Cache Access is DISABLED

3. Linux kernel requirements:

    - Linux kernel has the following features enabled: huge page support, UIO, HPET
    - Appropriate number of huge pages are reserved at kernel boot time
    - The IDs of the hardware threads (logical cores) per each CPU socket can be
      determined by parsing the file /proc/cpuinfo. The naming convention for the
      logical cores is: C{x.y.z} = hyper-thread z of physical core y of CPU socket x,
      with typical values of x = 0 .. 3, y = 0 .. 7, z = 0 .. 1. Logical cores
      C{0.0.1} and C{0.0.1} should be avoided while executing the test, as they are
      used by the Linux kernel for running regular processes.

4. The application options to be used in below test cases are listed as well as the 
general description.::

    ./build/l3fwd-thread [EAL options] -- \
        -p PORTMASK [-P]
        --rx(port,queue,lcore,thread)[,(port,queue,lcore,thread)]
        --tx(lcore,thread)[,(lcore,thread)]
        [--enable-jumbo] [--max-pkt-len PKTLEN]]
        [--no-lthreads]

   For other options please refer to URL memtioned above for detail explanation.

5. Traffic generator requirements

The flows need to be configured and started by the traffic generator:

  +------+---------+------------+---------------+------------+---------+
  | Flow | Traffic | MAC        | MAC           | IPV4       | IPV4    |
  |      | Gen.    | Src.       | Dst.          | Src.       | Dest.   |
  |      | Port    | Address    | Address       | Address    | Address |
  +======+=========+============+===============+============+=========+
  |   1  |   TG0   | Random MAC | DUT Port0 Mac | Random IP  | 2.1.1.1 |
  +------+---------+------------+---------------+------------+---------+
  |   2  |   TG1   | Random Mac | DUT port1 Mac | Random IP  | 1.1.1.1 |
  +------+---------+------------+---------------+------------+---------+

6. Test results table.

Frame sizes should be configured from 64,128,256,512,1024,2000, etc

  +------------+---------+------------------+--------------+
  | Frame Size |  S/C/T  | Throughput(Mpps) | Line Rate(%) |
  +============+=========+==================+==============+
  | 64         |         |                  |              |
  +------------+---------+------------------+--------------+
  | 128        |         |                  |              |
  +------------+---------+------------------+--------------+
  | 256        |         |                  |              |
  +------------+---------+------------------+--------------+
  | 512        |         |                  |              |
  +------------+---------+------------------+--------------+
  | 1024       |         |                  |              |
  +------------+---------+------------------+--------------+
  | 2000       |         |                  |              |
  +------------+---------+------------------+--------------+


Test Case: one_lcore_per_pcore performance
==========================================

1. Launch app with descriptor parameters::

    ./examples/performance-thread/l3fwd-thread/x86_64-native-linuxapp-gcc/l3fwd-thread \
     -c ff -n 4 -- -P -p 3 --max-pkt-len 2500  \
     --rx="(0,0,0,0)(1,0,0,0)" --tx="(1,0)" --no-lthread

   (Note: option "--stat-lcore" is not enabled in the automation scripts)

2. Send traffic and verify performance.

3. Repeat above tests with below command lines respectively

  +-----+---------------------------------------------------------------------------------------------------+
  | #   |                             Command Line                                                          |
  +=====+===================================================================================================+
  | 1   | ./l3fwd-thread -c ff -n 4 -- -P -p 3 --max-pkt-len 2500 \                                         |
  |     |                 --rx="(0,0,0,0)(1,0,1,1) --tx="(2,0)(3,1) \                                       |
  |     |                 --no-lthread                                                                      |
  +-----+---------------------------------------------------------------------------------------------------+
  | 2   | ./l3fwd-thread -c ff -n 4 -- -P -p 3 --max-pkt-len 2500 \                                         |
  |     |                 --rx="(0,0,0,0)(0,1,1,1)(1,0,2,2)(1,1,3,3)" \                                     |
  |     |                 --tx="(4,0)(5,1)(6,2)(7,3)" --no-lthread                                          |
  +-----+---------------------------------------------------------------------------------------------------+
  | 3   | ./l3fwd-thread -c ff -n 4 -- -P -p 3 --max-pkt-len 2500 \                                         |
  |     |                --rx="(0,0,0,0)(0,1,1,1)(0,2,2,2)(0,3,3,3)(1,0,4,4)(1,1,5,5)(1,2,6,6)(1,3,7,7)" \  |
  |     |                --tx="(8,0)(9,1)(10,2)(11,3)(12,4)(13,5)(14,6)(15,7)" \                            |
  |     |                --no-lthread                                                                       |
  +-----+---------------------------------------------------------------------------------------------------+

4. Check test results and full out the above result table.


Test Case: n_lcore_per_pcore performance
========================================

1. Launch app with descriptor parameters::

    ./examples/performance-thread/l3fwd-thread/x86_64-native-linuxapp-gcc/l3fwd-thread \
     --lcores="2,(0-1)@0" -- -P -p 3 --max-pkt-len 2500 \
     --rx="(0,0,0,0)(1,0,0,0)" --tx="(1,0)"

   (Note: option "--stat-lcore" is not enabled in the automation scripts)

2. Send traffic and verify performance both directional and bi-directional

3. Repeat above tests with below command lines respectively

  +-----+---------------------------------------------------------------------------------------------------+
  | #   |                             Command Line                                                          |
  +=====+===================================================================================================+
  | 1   | ./l3fwd-thread -n 4 --lcores="(0-3)@0,4" -- -P -p 3 --max-pkt-len 2500  \                         |
  |     |                 --rx="(0,0,0,0)(1,0,1,1) --tx="(2,0)(3,1) \                                       |
  |     |                 --no-lthread                                                                      |
  +-----+---------------------------------------------------------------------------------------------------+
  | 2   | ./l3fwd-thread -n 4 --lcores="(0-7)@0,8" -- -P -p 3-P -p 3 --max-pkt-len 2500  \                  |
  |     |                 --rx="(0,0,0,0)(0,1,1,1)(1,0,2,2)(1,1,3,3)" \                                     |
  |     |                 --tx="(4,0)(5,1)(6,2)(7,3)" --no-lthread                                          |
  +-----+---------------------------------------------------------------------------------------------------+
  | 3   | ./l3fwd-thread -n 4 --lcores="(0-15)@0,16" -- -P -p 3 --max-pkt-len 2500  \                       |
  |     |                --rx="(0,0,0,0)(0,1,1,1)(0,2,2,2)(0,3,3,3)(1,0,4,4)(1,1,5,5)(1,2,6,6)(1,3,7,7)" \  |
  |     |                --tx="(8,0)(9,1)(10,2)(11,3)(12,4)(13,5)(14,6)(15,7)" \                            |
  |     |                --no-lthread                                                                       |
  +-----+---------------------------------------------------------------------------------------------------+

4. Check test results and full out the above result table.


Test Case: n_lthread_per_pcore performance
==========================================

1. Launch app with descriptor parameters::

    ./examples/performance-thread/l3fwd-thread/x86_64-native-linuxapp-gcc/l3fwd-thread \
     -c ff -n 4 -- -P -p 3 --max-pkt-len 2500 \
     ----tx="(0,0)" --tx="(0,0)"

   (Note: option "--stat-lcore" is not enabled in the automation scripts)

2. Send traffic and verify performance both directional and bi-directional

3. Repeat above tests with below command lines respectively

  +-----+---------------------------------------------------------------------------------------------------+
  | #   |                             Command Line                                                          |
  +=====+===================================================================================================+
  | 1   | ./l3fwd-thread -c ff -n 4 -- -P -p 3 --max-pkt-len 2500  \                                        |
  |     |                 --rx="(0,0,0,0)(1,0,1,1) --tx="(0,0),(0,1)"                                       |
  +-----+---------------------------------------------------------------------------------------------------+
  | 2   | ./l3fwd-thread -c ff -n 4 -- -P -p 3 --max-pkt-len 2500  \                                        |
  |     |                 --rx="(0,0,0,0)(0,1,0,1)(1,0,0,2)(1,1,0,3)" \                                     |
  |     |                 --tx="(0,0)(0,1)(0,2)(0,3)"                                                       |
  +-----+---------------------------------------------------------------------------------------------------+
  | 3   | ./l3fwd-thread -c ff -n 4 -- -P -p 3 --max-pkt-len 2500  \                                        |
  |     |                --rx="(0,0,0,0)(0,1,0,1)(0,2,0,2)(0,3,0,3)(1,0,0,4)(1,1,0,5)(1,2,0,6)(1,3,0,7)" \  |
  |     |                --tx="(0,0)(0,1)(0,2)(0,3)(0,4)(0,5)(0,6)(0,7)" \                                  |
  +-----+---------------------------------------------------------------------------------------------------+

4. Check test results and full out the above result table.
