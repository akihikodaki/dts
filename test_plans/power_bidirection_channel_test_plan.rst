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

===================================
power bidirection channel test plan
===================================

preparation work
================
1. Turn on speedstep option in BIOS.
2. Turn on CPU C3 and C6.
3. Turn on turbo in BIOS.
4. Disable intel_pstate in Linux kernel command ``intel_pstate=disable``.
5. modprobe msr module to let the application can get the CPU HW info.
6. Let user space can control the CPU frequency::

    cpupower frequency-set -g userspace

7. set a folder::

    mkdir /tmp/powermonitor
    chmod 777 /tmp/powermonitor


Test Case 1 : Check VM can send power policy command to host and get acked
==========================================================================
Step 1. Launch VM using libvirt::

    virsh start [VM name]

Step 2. Launch VM power manager example on the host to monitor the channel from VM::

    ./examples/vm_power_manager/build/vm_power_mgr -c 0xfffe -n 4 --no-pci
    vmpower> add_vm [vm name]
    vmpower> add_channels [vm name] all
    vmpower> set_channel_status [vm name] all enabled
    vmpower> show_vm [vm name]

    If VM name is ubuntu, the command as following:
    vmpower> add_vm ubuntu
    vmpower> add_channels ubuntu all
    vmpower> set_channel_status ubuntu all enabled
    vmpower> show_vm ubuntu

Step 3. In the VM, launch guest_vm_power_mgr to set and send the power manager policy to the host power example::

   ./examples/vm_power_manager/guest_cli/build/guest_vm_power_mgr -c 0xfe -n 4 -m 1024 --no-pci --file-prefix=vm_power -- --vm-name=ubuntu --vcpu-list=0-7

    Send command to the core 7 on host APP:
    vmpower(guest)> set_cpu_freq 7 down

    Check following info will be returned for the ACK activity, as following:
    ACK received for message sent to host.

    If command can't be executed, NACK will be returned, as following:
    NACK received for message sent to host.

Step 4. Set frequency on core which is out of the VM's core scope::

    For example, the vcpu range is 0-7, we set command to vcpu number 8 as following:
    vmpower(guest)> set_cpu_freq 8 down
    GUEST_CHANNEL: Channel is not connected
    Error sending message: Unknown error -1


Test Case 2 : Query Host CPU frequency list from VM
===================================================
Step 1. Launch VM using libvirt::

    virsh start [VM name]

Step 2. Launch VM power manager example on the host to monitor the channel from VM::

    ./examples/vm_power_manager/build/vm_power_mgr -c 0xfffe -n 4 --no-pci
    vmpower> add_vm [vm name]
    vmpower> add_channels [vm name] all
    vmpower> set_channel_status [vm name] all enabled
    vmpower> show_vm [vm name]
    vmpower> set_query <vm_name> <enable|disable>

Step 3. Enable the query permission for target VM from host vm_power_mgr example::

    Command format: set_query <vm_name> <enable|disable>
    if vm name is ubuntu,command as following:
    vmpower> set_query ubuntu enable

Step 4. Query the CPU frequency for all CPU cores from VM side::

   ./examples/vm_power_manager/guest_cli/build/guest_vm_power_mgr -c 0xfe -n 4 -m 1024 --no-pci --file-prefix=vm_power -- --vm-name=ubuntu --vcpu-list=0-7
    vmpower> query_cpu_freq <core_num> | all

    Check vcpu 0~7 frequency info will be returned, for example:
        Frequency of [0] vcore is 2300000.
        Frequency of [1] vcore is 2200000.
        Frequency of [2] vcore is 2800000.
        Frequency of [3] vcore is 2300000.
        Frequency of [4] vcore is 2300000.
        Frequency of [5] vcore is 2300000.
        Frequency of [6] vcore is 2300000.
        Frequency of [7] vcore is 2300000.

Step 5. Disable query permission from VM, check the host CPU frequency won't be returned::

    at host side, disable query permission by vm_power_mgr example:
    vmpower> set_query ubuntu disable

    at VM side, query CPU frequency again, this action should not be executed successfully, log as following:
    vmpower(guest)> query_cpu_freq all
    GUEST_CLI: Error receiving message.
    Error during frequency list reception.


Test Case 3: Query CPU capability from VM
=========================================
Step1~3. The same as test case 2

Step4: Query all the valid CPU core capability of host, check all cores' information is returned. Check the high priority core is recognized correctly::

    For example, core 2 is returned as high priority core:
    vmpower(guest)> query_cpu_caps all
    Capabilities of [0] vcore are: turbo possibility: 1, is priority core: 0.
    Capabilities of [1] vcore are: turbo possibility: 1, is priority core: 0.
    Capabilities of [2] vcore are: turbo possibility: 1, is priority core: 1.
    Capabilities of [3] vcore are: turbo possibility: 1, is priority core: 0.
    Capabilities of [4] vcore are: turbo possibility: 1, is priority core: 0.
    Capabilities of [5] vcore are: turbo possibility: 1, is priority core: 0.
    Capabilities of [6] vcore are: turbo possibility: 1, is priority core: 0.
    Capabilities of [7] vcore are: turbo possibility: 1, is priority core: 0.

Step 5: Query CPU capability for core out of scope, check no CPU info will be return::

    For example, the valid vcpu range is 0~7, query cpu capability of core 8 should return error as following:
    vmpower(guest)> query_cpu_caps 8
    Invalid parameter provided.

Step 6: Disable query permission from VM, check the host CPU capability won't be returned::

    at host side, disable query permission by vm_power_mgr example:
    vmpower> set_query ubuntu disable
    
    at VM side, query CPU capability again, this action should not be executed successfully, log as following:
    vmpower(guest)> query_cpu_caps all
    GUEST_CLI: Error receiving message.
    Error during capabilities reception.
