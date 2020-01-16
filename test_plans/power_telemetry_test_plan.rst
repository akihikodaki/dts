.. Copyright (c) <2010-2020>, Intel Corporation
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

=============================
Power Lib Telemetry Test Plan
=============================

Three types of data will be reported by DPDK telemetry lib in l3fwd-power sample.
+   {"empty_poll"},
+   {"full_poll"},
+   {"busy_percent"}


Preparation Work for Settings
=============================
1. Turn on Speedstep option in BIOS
2. Turn on CPU C3 and C6
3. Turn on Turbo in BIOS
4. Disable intel_pstate in Linux kernel command::

    intel_pstate=disable

5. Let user space can control the CPU frequency::

    cpupower frequency-set -g userspace

Compile DPDK with telemetry enabled, enable telemetry lib in configuration file::

    -CONFIG_RTE_LIBRTE_TELEMETRY=n
    +CONFIG_RTE_LIBRTE_TELEMETRY=y


Test Case 1 : Check all 3 type of power related info reported by Telemetry System
=================================================================================
1. Launch l3fwd-power sample with telemetry enabled, bind one NIC to DPDK driver, launch l3fwd-power::

    ./l3fwd-power -l 1-2 -n 4 --telemetry -- -p 0x1 -P --config="(0,0,2)" --telemetry

2. Get the telemetry info using dpdk-telemetry-client.py script, then choose mode 3 ``Send for global Metrics``::

    python usertools/dpdk-telemetry-client.py  /var/run/some_client

3. Check the returned info include "empty_poll", "full_poll", "busy_percent", as following::

    {
      "port": 4294967295,
      "stats": [
        {
          "name": "empty_poll",
          "value": 1705624132
        },
        {
          "name": "full_poll",
          "value": 4275898
        },
        {
          "name": "busy_percent",
          "value": 0
        }]
    }

Test Case 2 : Check busy_percent with different injected throughput
===================================================================
1. Using step1~3 in test case 1.

2. Inject packets with line rate with 64 bit frame size, check the busy_percent returned, it should be no-zero number.

3. Stop the injected packet stream, check the busy_percent returned, it should be 0.
