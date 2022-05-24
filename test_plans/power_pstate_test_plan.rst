.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

=======================================
Power Lib Based on Intel Pstate Driver
=======================================
Before DPDK 19.02 version, DPDK power lib is based on acpi-cpufreq driver in Linux.
From DPDK 19.02, Power lib start support intel_pstate driver.

Prepare Settings
================
1. Turn on Speedstep option in BIOS
2. Turn on CPU C3 and C6
3. Turn on Turbo in BIOS
4. In BIOS set up the HWPM to "Native Mode"
5. Turn off "Hyper Threading"
6. Probe msr (used to get Intel CPU's no_turbo max frequency)

Definition of CPU frequency in this test suite:
sys_min = sys/devices/system/cpu/cpu{}/cpufreq/cpuinfo_min_freq
sys_max = sys/devices/system/cpu/cpu{}/cpufreq/cpuinfo_max_freq
no_turbo_max = [rdmsr -p 1 0x0CE -f 15:8 -d]00000

Note:
For Intel Processor, If "Hyper Threading" enabled in BIOS, need change frequency on both HT core
at the same time to let the frequency take effect.
From DPDK 19.08, dpdk-vm_power_manager will set fifo channel for each core.
Before DPDK 19.08, all core will share 1 fifo channel

Test Case1 : Test Pstate lib basic action based on directly power command
===========================================================================
Step 1. Create powermonitor fold for::

    Create monitor channel folder, /tmp/powermonitor, give permission for read and write

Step 2. Luanch VM power manager sample::

    ./<build_target>/examples/dpdk-vm_power_manager -l 1-4 -n 4 --file-prefix=power --no-pci

Step 3. Prepare different command in JSON format then send it to the fifo channel::

    The command Sample as following:
    {"instruction": {
    "name": "policy",
    "command": "power",
    "unit": "SCALE_MAX"
    }}

    Test with following 6 command type with following Sequency:
    ENABLE_TURBO -> SCALE_MIN -> SCALE_MAX -> DISABLE_TURBO -> ENABLE_TURBO -> SCALE_UP -> SCALE_DOWN
    cat command.json >/tmp/powermonitor/fifo{core_number}
    :"SCALE_MAX": Scale frequency of this core to maximum
    :"SCALE_MIN": Scale frequency of this core to minimum
    :"SCALE_UP": Scale up frequency of this core
    :"SCALE_DOWN": Scale down frequency of this core
    :"ENABLE_TURBO": Enable Turbo Boost for this core
    :"DISABLE_TURBO": Disable Turbo Boost for this core

Step 4. Check the Core1  frequency for each command in Step 3::

    min=sys/devices/system/cpu/cpu{}/cpufreq/scaling_min_freq
    max=sys/devices/system/cpu/cpu{}/cpufreq/scaling_max_freq
    Check point of Step SCALE_MIN: min=max=sys_min
    Check point of Step SCALE_MAX: min=max=sys_max
    Check point of Step DISABLE_TURBO: min=max=no_turbo_max
    Check point of Step ENABLE_TURBO: min=max=no_turbo_max
    Check point of Step SCALE_UP: min=max=sys_max
    Check point of Step SCALE_DOWN: min=max=no_turbo_max
