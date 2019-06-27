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

    ./l3fwd-power -c 0xc000000 -n 4 -- -P -p 0x01  --config '(0,0,27)'

4. Send packets by packet generator with high speed, check the used cpu frequency is almost 100%::

    cat /sys/devices/system/cpu/cpu27/cpufreq/cpuinfo_cur_freq

5. Send packets by packet generator with low speed, the CPU frequency will reduce about 50%::

    cat /sys/devices/system/cpu/cpu27/cpufreq/cpuinfo_cur_freq