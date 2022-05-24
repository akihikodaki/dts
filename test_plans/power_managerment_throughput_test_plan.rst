.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

======================================
Power managerment throughput test plan
======================================

This test plan test cpu frequence changed according io workloads with l3fwd-power sample.
The cpu frequency status depends on NIC and CPU type.

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

Test Case1: Check the CPU frequency can change according differernt packet speed
================================================================================

1. Check that you are using the "acpi-cpufreq" driver by command "cpufreq-info".

2. CPU frequency controlled by userspace by command "cpupower frequency-set -g userspace".

3. Bind one nic port to igb_uio, launch l3fwd-power sample, one core used for one port::

    ./<build_target>/examples/dpdk-l3fwd-power -c 0xc000000 -n 4 -- -P -p 0x01  --config '(0,0,27)'

4. Send packets by packet generator with high speed, check the used cpu frequency is almost 100%::

    cat /sys/devices/system/cpu/cpu27/cpufreq/cpuinfo_cur_freq

5. Send packets by packet generator with low speed, the CPU frequency will reduce about 50%::

    cat /sys/devices/system/cpu/cpu27/cpufreq/cpuinfo_cur_freq