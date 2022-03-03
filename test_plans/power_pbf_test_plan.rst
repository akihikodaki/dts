.. Copyright (c) <2019>, Intel Corporation
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

===============
Power PBF Tests
===============
PBF(Priority Base Frequency) is new power feature on some Intel CPU SKU. This feature can
support some core in core list have garenteed higher base frequency DPDK start support this feature from 19.05

Preparation work
================
Check the SKU of Processor: 6230N, 6252N and 5218N can support this feature
1. Turn on Speedstep option in BIOS
2. Set C-State to C0/C1
3. Turn on Turbo in BIOS
4. Turn on PBF in BIOS
5. Set HW Pstate to "Native Mode without Legacy Support"
6. Turn on RAPL Prioritization
7. Modprobe msr module
8. DON'T set intel_pstate to disable in grub
9. Turn on the debug log for DPDK power lib, CONFIG_RTE_LIBRTE_POWER_DEBUG=y
10. Install the Jansson development package, ``apt-get install libjansson-dev`` or ``dnf -y install jansson-devel``.


Test Case1 : Check High Priority Core Can Be Recognized By Power Lib
====================================================================
Step 1. Create powermonitor fold for::

    Create power monitor channel folder, /tmp/powermonitor, give permission for read and write

Step 2. Compile DPDK with Power Lib debug info on, then Luanch VM power manager sample::

    ./<build_target>/examples/dpdk-vm_power_manager -l 1-46 -n 4 --file-prefix=power --no-pci

    Check two different base_max frequency will be shown in log, for example on Intel 6230N Processor:
    The log will be like as following
    POWER: power_get_available_freqs: sys min 800000, sys max 3900000, base_max 2300000
    POWER: power_get_available_freqs: sys min 800000, sys max 3900000, base_max 2700000

    For each core, get following 3 frequency item, cross check frequency in the VM_power out put log:
    sys_min=sys/devices/system/cpu/cpu{}/cpufreq/cpuinfo_min_freq
    sys_max=sys/devices/system/cpu/cpu{}/cpufreq/cpuinfo_max_freq
    base_max=sys/devices/system/cpu/cpu{}/cpufreq/base_frequency

    Take Intel 6230N Processor as example:
    sys_min=800000
    sys_max=3900000
    base_max=2700000(high priority Core) base_max=2300000 (Normal Core)

    The high priority core has max frequency at 27000000
    Normal core has max frequency at 2300000

Test Case2 : CPU MIN and MAX Freq Test for the High Priority Core
=================================================================
Step 1. Create powermonitor fold for::

    Create monitor channel folder, /tmp/powermonitor, give permission for read and write

Step 2. Compile DPDK with Power Lib debug info on, then aunch VM power manager sample::

    ./<build_target>/examples/dpdk-vm_power_manager -l 1-46 -n 4 --file-prefix=power --no-pci

Step 3. Prepare different command in JSON format::

    From Test Case1, can get the high priority core list. We pick one core from this list
    Command JSON file template:
    {"instruction": {
    "name": "policy1",
    "command": "power",
    "unit": "SCALE_MIN",
    }}

Step 4: Send different command to power sample, then check the frequency::

    Command Steps: ENABLE_TURBO-> SCALE_MAX-> SCALE_DOWN-> SCALE_MIN
    Send action JSON file to dpdk-vm_power_manager's fifo channel, each core will have it's own channel:
    cat command.json >/tmp/powermonitor/fifo{core_number}

    Check the CPU frequency is changed accordingly in previous list by following method:
    min=sys/devices/system/cpu/cpu{}/cpufreq/scaling_min_freq
    max=sys/devices/system/cpu/cpu{}/cpufreq/scaling_max_freq
    Step SCALE_MAX: min=max=sys_max
    Step SCALE_DOWN: min=max=base_max
    Step SCALE_MIN: min=max=sys_min


    More info about the command:
    :"SCALE_MAX": Scale frequency of this core to maximum
    :"SCALE_MIN": Scale frequency of this core to minimum
    :"SCALE_UP": Scale up frequency of this core
    :"SCALE_DOWN": Scale down frequency of this core
    :"ENABLE_TURBO": Enable Turbo Boost for this core
    :"DISABLE_TURBO": Disable Turbo Boost for this core

Test Case3 : Check "DISABLE_TURBO" Action When Core is In Turbo Status for High Priority Core
=============================================================================================
Step 1. Create powermonitor fold for::

   Create monitor channel folder, /tmp/powermonitor, give permission 777

Step 2. Compile DPDK with Power Lib debug info on, then launch VM power manager sample::

 ./<build_target>/examples/dpdk-vm_power_manager -l 1-46 -n 4 --file-prefix=power --no-pci

Step 3. Prepare Several command in JSON format then send it to the fifo channel for the high priority core::

    {"instruction": {
    "name": "policy2",
    "command": "power",
    "unit": "SCALE_MIN",
    }}
    cat command.json >/tmp/powermonitor/fifo{core_number}

    Command Steps: ENABLE_TURBO -> SCALE_MAX ->DISABLE_TURBO

Step 4. Check the CPU frequency will be set to No turbo max frequency when turbo is off::

        min=sys/devices/system/cpu/cpu{}/cpufreq/scaling_min_freq
        max=sys/devices/system/cpu/cpu{}/cpufreq/scaling_max_freq
        Check point of Step SCALE_MAX: min=max=sys_max
        Check point of Step DISABLE_TURBO: min=max=base_max


Test Case4:  Check Distributor Sample Use High Priority Core as Distribute Core
===============================================================================
Step 1. Get the Priority core list on DUT in test case 1::

    For example:
    6,7,13,14,15,16,21,26,27,29,36,38
    On one Intel 6230N Processor
    Note: the high base frequency core location of each processor is different.

Step 2. Launch distributor with 1 priority core, check the high priority core will be picked as the distributor core::

    Two worker:
    ./distributor_app -l 1-6  -n 4 -- -p 0x1

    Check the high priority core is assigned as distributor core in log, for example:
    "Core 6 acting as distributor core."

Test Case5:  Check Distributor Sample Will use High priority core for distribute core and rx/tx core
====================================================================================================
Step 1. Get the Priority core list on DUT in test case 1::

    Using pbf.py to check, or check from kernel
    For example:
    6,7,13,14,15,16,21,26,27,29,36,38
    On one intel 6230N Processor
    Note: the high base frequency core location of each processor are different.

Step 2. Launch distributor with 3 priority core, check the high priority
core will be picked as the distributor core, rx and tx core::

    For example, the high priority core is" 6,7 13"
    ./distributor_app -l 1-6,7,13  -n 4 -- -p 0x1

Step 3. Check the high priority core is assigned as distributor core in log, for example::

   Distributor on priority core 6

Step 4. Check the high priority core are assigned as tx/rx core in log, for example::

   Core 13 doing packet TX.
   Core 7 doing packet RX.
