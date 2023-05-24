.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2023 Intel Corporation

============================
Power Intel Uncore Test Plan
============================
Uncore is a term used by Intel to describe the functions of a microprocessor that are
not in the core, but which must be closely connected to the core to achieve high performance;
L3 cache, on-die memory controller, etc.
L3fwd-power facilitates setting uncores frequency using DPDK Intel Uncore API.

There is a test for each of the three options that are available for setting the uncore frequency,
along with one final test to check successful exiting of Uncore API.

Uncore is changed per socket level, this test suite is designed to change the uncore value 
for each socket, however only socket 0 is verified to see if a change has been made.
To view changed frequency, using MSR can be done on any core of the socket.
See "Useful MSR 0x620 Information" section for more information.

Preperation work
================
1. Check kernel version to make sure that it's greater than 5.6
   uname -r
2. Check if uncore is enabled.
   cd /sys/devices/system/cpu/intel_uncore_frequency
   if not:
   check if kernel flag is enabled:
   cat /boot/config-$(uname -r) | grep -i CONFIG_INTEL_UNCORE_FREQ_CONTROL
   Otherwise add uncore sysfs driver
   modprobe intel-uncore-frequency
3. Check if MSR driver is built-in or is loaded
   modprobe msr

Useful MSR 0x620 Information
============================
* MSR 0x620 is a seperate register interface to configure uncore P-state ratio
  limits and read back the current set uncore ratio limits.
* Bits 0:6 are for max ratio and bits 8:14 for min ratio.
* MSR 0x620 value is a ratio value, which means it must be multiplied by the base clock 
  to get the uncore frequency in KHz. In this example 100000.
* When reading MSR 0x620 during this test suite core 0 on socket 0 is only checked
  for the uncore max and min ratio limits. When no core is specified for rdmsr,
  then it defaults to core 0.

Test Case 1: Validate_power_uncore_freq_max
===========================================
Step 1. Check current max set uncore frequency versus max possible frequency

   "rdmsr 0x620 -f 6:0 -d" * 100000
   cat /sys/devices/system/cpu/intel_uncore_frequency/package_00_die_00/initial_max_freq_khz

   If these are equal, then change the value of each sysfs file by bringing them down 1 bin (100MHz).

      echo {lower_uncore_max} > /sys/devices/system/cpu/intel_uncore_frequency/package_XX_die_XX/max_freq_khz

Step 2. Run basic l3fwd-power configuration to set min/max uncore frequency to max limit

   ./<build_target>/examples/dpdk-l3fwd-power -c 0x6 -n 1 -- -p 0x1 -P --config="(0,0,2)" -U

Step 3. Confirm uncore min/max frequencies are set to max limit

   "rdmsr 0x620 -f 6:0 -d" * 100000
   "rdmsr 0x620 -f 14:8" * 100000


Test Case 2: Validate_power_uncore_freq_min
===========================================

Step 1. Check current min set uncore frequency versus min possible frequency

   "rdmsr 0x620 -f 14:8" * 100000
   cat /sys/devices/system/cpu/intel_uncore_frequency/package_00_die_00/initial_min_freq_khz

   If these are equal, then change the value of each sysfs file by bringing them up 1 bin (100MHz) .

      echo {higher_uncore_min} > /sys/devices/system/cpu/intel_uncore_frequency/package_XX_die_XX/min_freq_khz

Step 2. Run basic l3fwd-power configuration to set min/max uncore frequency to min limit

   ./<build_target>/examples/dpdk-l3fwd-power -c 0x6 -n 1 -- -p 0x1 -P --config="(0,0,2)" -u

Step 3. Confirm uncore min/max frequencies are set to min limit

   "rdmsr 0x620 -f 14:8" * 100000
   "rdmsr 0x620 -f 6:0 -d" * 100000


Test Case 3: Validate_power_uncore_freq_idx
===========================================

Step 1. Check current max uncore frequency versus index 2.
        Index 2 is equal to the frequency at index 2.
        This is equal to => max possible freq - 200000(2 bin (200MHz)).
        For example index range is [2400000, 2300000, 2200000,......,900000,800000], index 2 is 2200000.

   "rdmsr 0x620 -f 6:0 -d" * 100000
   (cat /sys/devices/system/cpu/intel_uncore_frequency/package_00_die_00/initial_max_freq_khz) - 200000

   If these are equal, then change the value of each sysfs file by bringing them up 1 bin (100MHz).

      echo {higher_uncore_idx} > /sys/devices/system/cpu/intel_uncore_frequency/package_XX_die_XX/max_freq_khz

Step 2. Run basic l3fwd-power configuration to set min/max uncore frequency to index value

   ./<build_target>/examples/dpdk-l3fwd-power -c 0x6 -n 1 -- -p 0x1 -P --config="(0,0,2)" -i 2

Step 3. Confirm uncore min/max frequencies are set to index value

   "rdmsr 0x620 -f 6:0 -d" * 100000
   "rdmsr 0x620 -f 14:8" * 100000


Test Case 4: Validate_power_uncore_exit
=======================================

Step 1. Run basic l3fwd-power configuration. Doesn't matter just want to get l3fwd-power running

   ./<build_target>/examples/dpdk-l3fwd-power -c 0x6 -n 1 -- -p 0x1 -P --config="(0,0,2)" -U

Step 2. Exit program and ensure there are no errors/ right output is recieved

   Ctrl-C
   Check for line "mode and been set back to the original"
   Which should be the last line the program outputs when exiting correctly.
   The start of the line is omitted as it won't be known which mode/which lcore will be set
   back to the original.
