.. Copyright (c) <2010-2019>, Intel Corporation
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

========================
Power Negative Test Plan
========================

Preparation work
================
1. Turn on Speedstep option in BIOS
2. Turn on CPU C3 and C6
3. Turn on Turbo in BIOS
4. Disable intel_pstate in Linux kernel command: intel_pstate=disable
5. modprobe msr module to let the application can get the CPU HW info
6. Let user space can control the CPU frequency: cpupower frequency-set -g userspace


Test Case1: Inject Malformed JSON Command file to fifo channel
===============================================================
Step 1. Create powermonitor fold for dpdk-vm_power_manager sample::

    mkdir /tmp/powermonitor
    chmod 777 /tmp/powermonitor

Step 2. Luanch VM power manager sample::

    ./<build_target>/examples/dpdk-vm_power_manager -l 1-3 -n 4 --file-prefix=test1 --no-pci

Step 3. Prepare policy in JSON format then send it to the fifo channel:
    Prepare different command in JSON format then send it to the fifo channel
    Modify "name", "resource_id", "command" to large character string to check if the dpdk-vm_power_manager sample will crash
    For example::

      {"policy": {
        "name": "01234567890123445678901234567890123456789001234567890",
        "command": "create",
        "policy_type": "WORKLOAD",
        "workload": "MEDIUM",
      }}

Step 4. Send Json format command to the fifo channel::

  cat command.json > /tmp/powermonitor/fifo22

Check point: no crash at the dpdk-vm_power_manager application side.

Potential issue: no warning for the user for the name too long, now is char[32], but no crash as strlcpy is uesed

Test Case2: Send invalid command through JSON channel
======================================================
Step 1. Create powermonitor fold for dpdk-vm_power_manager sample::

    mkdir /tmp/powermonitor
    chmod 777 /tmp/powermonitor

Step 2. Luanch VM power manager sample::

    ./<build_target>/examples/dpdk-vm_power_manager -l 1-3 -n 4 --file-prefix=test1 --no-pci

Step 3. Prepare policy in JSON format then send it to the fifo channel:

Prepare invalid power command, for example, core list above the max core number. For example::

    {"policy": {
        "name": "Ubutnu",
        "command": "create",
        "policy_type": "WORKLOAD",
        "workload": "MEDIUM_111",
    }}

    {"policy": {
        "name": "Ubutnu",
        "command": "create",
        "policy_type": "WORKLOAD_111",
        "workload": "MEDIUM",
    }}

Step 4. Send Json format command to the fifo channel::

	cat command.json > /tmp/powermonitor/fifo22

Test Case3: Check if host power APP have check point for the power policy sent from untrusted VM
===================================================================================================
Step 1. Launch VM by using libvirt, one NIC should be configured as PCI pass-throughput to the VM::

    virsh start [VM name]

Note: For the VM xml file which will be used for creating the VM, it can re-use the vm0.xml generated in the branch ratio DTS script

Step 2. Luanch VM power manager sample on the host to monitor the channel from VM::

    ./<build_taget>/examples/dpdk-vm_power_manager -l 12-14 -n 4 --no-pci
      >　add_vm [vm name]
      >　add_channels [vm name] all
      >　set_channel_status [vm name] all enabled
      >　show_vm [vm name]

   Check the invalid input command for dpdk-vm_power_manager sample::

    > add_channels ubuntu 128
    > add_channel ubuntu 10000000000000000

Check point:　No crash should be occur at dpdk-vm_power_manager sample

Step 3. In the VM, launch dpdk-guest_cli to set and send the power manager policy to the host power sample::

    ./<build_target>/examples/dpdk-guest_cli -c 0xff -n 4 -m 1024 --no-pci --file-prefix=yaolei \
      -- --vm-name=ubuntu --vcpu-list=0-7
      > set_cpu_freq 128 down
      > set_cpu_freq 1000000000000 down
      > set_cpu_freq -1 down

   also try other commands::

     "<up|down|min|max|enable_turbo|disable_turbo>"


Test Case4: TRAFFIC Policy Test based on JSON configure file with large integer number
========================================================================================
Step 1. Generate 1 VF under vfio-pci driver, launch dpdk-vm_power_manager sample with PF, for example::

    echo 1 > /sys/bus/pci/drivers/vfio-pci/0000\:82\:00.0/max_vfs
    ./<build_target>/examples/dpdk-vm_power_manager -l 1-4 -n 4 --socket-mem=1024,1024 --file-prefix=test1 -a 82:00.0 -- -p 0x01

Step 2. Launch testpmd with VF::

     ./<build_target>/app/dpdk-testpmd  -l 5-6 -n 4 --socket-mem=1024,1024 --file-prefix=test2 -a 0000:82:02.0 -- -i
       > set fwd macswap
       > start

Step 3. Prepare traffic policy in JSON format then send it to the power demon sample, put the VF MAC into the mac_list::

      {"policy": {
          "name": "ubuntu",
          "command": "create",
          "policy_type": "TRAFFIC",
          "max_packet_thresh": 500000000000000000000000000000,
          "avg_packet_thresh": 300000000000000000000000000000,
          "mac_list":[ "E0:E0:E0:E0:F0:F0"]
      }}

Step 4. Send Json format command to the fifo channel::

  cat traffic.json > /tmp/powermonitor/fifo6

Check point:　No crash should be occur at dpdk-vm_power_manager sample
