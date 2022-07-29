.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

======================================
Power managerment throughput test plan
======================================

This test plan test cpu frequency changed according io workloads with l3fwd-power sample.
The cpu frequency status depends on traffic speed.

Prerequisites
=============

1. Update Grub::

    Add "intel_pstate=disable" in kernel options.

2. BIOS configuration as below::

    CPU mode : "Power"
    Workload configuratuion："IO sensitive"
    Hardware Power : "Disabled"
    Speedstep : "Enabled"
    Turbo : "Enabled"
    C-stats：C0/C1
    C6 : "Enabled"

3. Let user space can control the CPU frequency::

    cpupower frequency-set -g userspace

Test Case 1: Check the CPU frequency with high traffic speed
================================================================================

1. Bind one nic port to igb_uio, launch l3fwd-power sample with sacle mode, one core used for one port::

    ./<build_target>/examples/dpdk-l3fwd-power -c 0x6 -n 1 -- --pmd-mgmt scale --max-empty-poll 128 -p 0x1 -P --config="(0,0,2)"

2. Send packets by packet generator with high speed, check the cpu frequency it should be equal or below turbo max frequency
   and be higher than p1.

    cat /sys/devices/system/cpu/cpu2/cpufreq/cpuinfo_cur_freq

Test Case 2: Check the CPU frequency with low traffic speed
================================================================================

1. same as Test Case 1 step 1.

2. Send packets by packet generator with low speed, check the cpu frequency it should be below p1.

    cat /sys/devices/system/cpu/cpu2/cpufreq/cpuinfo_cur_freq