.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2020 Intel Corporation

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


Test Case 1 : Check all 3 type of power related info reported by Telemetry System
=================================================================================
1. Launch l3fwd-power sample with telemetry enabled, bind one NIC to DPDK driver, launch l3fwd-power::

    ./<build_target>/examples/dpdk-l3fwd-power -l 1-2 -n 4 --telemetry -- -p 0x1 -P --config="(0,0,2)" --telemetry

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
