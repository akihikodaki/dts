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

5. Set CONFIG_RTE_LIBRTE_POWER_DEBUG=y CONFIG_RTE_LIBRTE_POWER=y in /config/common_base file.
6. modprobe msr module to let the application can get the CPU HW info.
7. Let user space can control the CPU frequency::

    cpupower frequency-set -g userspace

8. Prepare a valid VM using libvirt, 8 virtio-serial channel should be add as
configuration channel, vCPU and physical CPU mapping table should be configured.
The configuration part in libvirt is following::

      <cputune>
        <vcpupin vcpu='0' cpuset='0'/>
        <vcpupin vcpu='1' cpuset='1'/>
        <vcpupin vcpu='2' cpuset='2'/>
        <vcpupin vcpu='3' cpuset='3'/>
        <vcpupin vcpu='4' cpuset='4'/>
        <vcpupin vcpu='5' cpuset='5'/>
        <vcpupin vcpu='6' cpuset='6'/>
        <vcpupin vcpu='7' cpuset='7'/>
      </cputune>
          <channel type='unix'>
          <source mode='bind' path='/tmp/powermonitor/ubuntu.0'/>
          <target type='virtio' name='virtio.serial.port.poweragent.0'/>
          <address type='virtio-serial' controller='0' bus='0' port='1'/>
        </channel>
          <channel type='unix'>
          <source mode='bind' path='/tmp/powermonitor/ubuntu.1'/>
          <target type='virtio' name='virtio.serial.port.poweragent.1'/>
          <address type='virtio-serial' controller='0' bus='0' port='2'/>
        </channel>
          <channel type='unix'>
          <source mode='bind' path='/tmp/powermonitor/ubuntu.2'/>
          <target type='virtio' name='virtio.serial.port.poweragent.2'/>
          <address type='virtio-serial' controller='0' bus='0' port='3'/>
        </channel>
          <channel type='unix'>
          <source mode='bind' path='/tmp/powermonitor/ubuntu.3'/>
          <target type='virtio' name='virtio.serial.port.poweragent.3'/>
          <address type='virtio-serial' controller='0' bus='0' port='4'/>
        </channel>
          <channel type='unix'>
          <source mode='bind' path='/tmp/powermonitor/ubuntu.4'/>
          <target type='virtio' name='virtio.serial.port.poweragent.4'/>
          <address type='virtio-serial' controller='0' bus='0' port='5'/>
        </channel>
           <channel type='unix'>ak
          <source mode='bind' path='/tmp/powermonitor/ubuntu.5'/>
          <target type='virtio' name='virtio.serial.port.poweragent.5'/>
          <address type='virtio-serial' controller='0' bus='0' port='6'/>
        </channel>
           <channel type='unix'>
          <source mode='bind' path='/tmp/powermonitor/ubuntu.6'/>
          <target type='virtio' name='virtio.serial.port.poweragent.6'/>
          <address type='virtio-serial' controller='0' bus='0' port='7'/>
        </channel>
          <channel type='unix'>
          <source mode='bind' path='/tmp/powermonitor/ubuntu.7'/>
          <target type='virtio' name='virtio.serial.port.poweragent.7'/>
          <address type='virtio-serial' controller='0' bus='0' port='8'/>
        </channel>


sys_min=/sys/devices/system/cpu/cpu{}/cpufreq/cpuinfo_min_freq
sys_max=/sys/devices/system/cpu/cpu{}/cpufreq/cpuinfo_max_freq

no_turbo_max=$(rdmsr -p 1 0x0CE -f 15:8 -d)00000

cur_min=sys/devices/system/cpu/cpu{}/cpufreq/scaling_min_freq
cur_max=sys/devices/system/cpu/cpu{}/cpufreq/scaling_max_freq

Test Case 1 : Basic Branch-Ratio Test based on one NIC pass-through into VM Scenario
====================================================================================
1. Launch VM by using libvirt, one NIC should be configured as PCI
pass-throughput to the VM::

   virsh start [VM name]

2. Launch VM power manager sample on the host to monitor the channel from VM::

    ./examples/vm_power_manager/build/vm_power_mgr -l 12-14 -n 4 --no-pci
    
    >add_vm [vm name]
    >add_channels [vm name] all 
    >set_channel_status [vm name] all enabled
    >show_vm [vm name]

3. In the VM, launch guest_vm_power_mgr to set and send the power manager policy
to the host power sample, the policy is set to BRANCH_RATIO, the default
BRANCH_RATIO threshold is 0.25::

    ./examples/vm_power_manager/guest_cli/build/guest_vm_power_mgr -c 0xff -n 4 -m 1024 --no-pci --file-prefix=yaolei -- --vm-name=[vm name] --policy=BRANCH_RATIO --vcpu-list=0-7
    > send_policy now

4. Bind one NIC to DPDK driver in VM, launch testpmd with fwd io mode::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 0-1 -n 4 -m 1024 --file-prefix=test2 -- -i
    > start

5. Inject packet with packet generator to the NIC, with line rate(For example),
check the branch ratio and the related CPU frequency, in this case, the
core 1 will be used by testpmd as worker core, branch ratio will be shown as
following in vm_power_mgr's log output::

    1: 0.0048 {250065} {20001}
    0: 0.0307 {35782} {20000}
    1: 0.0042 {259798} {0}
    1: 0.0045 {242642} {20001}

6. [Check Point]Inject packets with packet generator with Line Rate(10G), check
the core 1 frequency use following cmd, The Frequency reported should be at the
highest frequency::

   [no_turbo_max]: cur_min=cur_max=no_turbo_max 
   cat /sys/devices/system/cpu/cpu2/cpufreq/cpuinfo_cur_freq

7. [Check Point]Stopped the traffic from packet generator. Check the core 1
frequency again, the Frequency reported should be::

    [sys_min]:cur_min=cur_max=sys_min


Test Case 2: Set Branch-Ratio Rate by User
==========================================
The same as test case1, the only difference is at step2 2. Launch VM power
manager sample on the host to monitor the channel from VM, set the branch
ration at host side::

    ./examples/vm_power_manager/build/vm_power_mgr -l 12-14 -n 4 -m 1024 --no-pci -- --branch-ratio=0.1

