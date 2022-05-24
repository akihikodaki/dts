.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2020 Intel Corporation

========================================
Power Policy Based on Branch Ratio Tests
========================================
Based on the branch ratio info offered by CPU, the DPDK user can know if
the CPU's real workload is high or Low. Then the host server can adjust the
related CPU frequency base this indicator.


Prepare work
============
1. Turn on Speedstep option in BIOS.
2. Turn off Hardware Power(HWP disable).
3. Turn on Turbo in BIOS.
4. Enable intel_pstate in Linux kernel command::

    intel_pstate=enable

5. modprobe msr module to let the application can get the CPU HW info.
6. Let user space can control the CPU frequency::

    cpupower frequency-set -g userspace

sys_min=/sys/devices/system/cpu/cpu2/cpufreq/cpuinfo_min_freq
no_turbo_max=$(rdmsr -p 2 0x0CE -f 15:8 -d)00000

Test Case 1 : Set Branch-Ratio Test Rate by User ====================================================================================
1. Launch VM power manager sample on the host to run branch monitor.
./<build_target>/examples/dpdk-vm_power_manager -v -c 0xe -n 1 -m 1024 --no-pci  -- --core-branch-ratio=1-3:0.3

2. Launch testpmd with fwd io mode::

    ./<build_target>/app/dpdk-testpmd -v -c 0x6 -n 1 -m 1024 --file-prefix=vmpower2 -- -i
    > start

3. Inject packet with packet generator to the NIC, with line rate,
check the branch ratio and the related CPU frequency, in this case, the
core 2 will be used by testpmd as worker core, branch ratio will be shown as
following in dpdk-vm_power_manager's log output::

    1: 0.0048 {250065} {20001}
    0: 0.0307 {35782} {20000}
    1: 0.0042 {259798} {0}
    1: 0.0045 {242642} {20001}

The above values in order are core number, ratio measured , # of branches, number of polls.

4. [Check Point]Inject packets with packet generator with Line Rate(10G), check
the core 2 frequency use following cmd, The Frequency reported should be at the
highest frequency::
cat /sys/devices/system/cpu/cpu2/cpufreq/scaling_cur_freq
[no_turbo_max]: cur_freq >= no_turbo_max(P1)

5. [Check Point]Stopped the traffic from packet generator. Check the core 2
frequency again, the Frequency reported should be::

    [sys_min]:cur_freq <= sys_min
