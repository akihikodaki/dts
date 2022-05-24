.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2019 Intel Corporation

=========================
Power Lib Empty Poll Test
=========================

Inband Policy Control
=====================

For packet processing workloads such as DPDK polling is continuous. This means
CPU cores always show 100% busy independent of how much work those cores are
doing. It is critical to accurately determine how busy a core is hugely
important for the following reasons:

   * No indication of overload conditions

   * User do not know how much real load is on a system meaning resulted in
     wasted energy as no power management is utilized

Tried and failed schemes include calculating the cycles required from the load
on the core, in other words the busyness. For example, how many cycles it costs
to handle each packet and determining the frequency cost per core. Due to the
varying nature of traffic, types of frames and cost in cycles to process, this
mechanism becomes complex quickly where a simple scheme is required to solve
the problems.

For all polling mechanism, the proposed solution focus on how many times empty
poll executed instead of calculating how many cycles it cost to handle each
packet. The less empty poll number means current core is busy with processing
workload, therefore,  the higher frequency is needed. The high empty poll
number indicate current core has lots spare time, therefore, we can lower the
frequency.

2.1 Power state definition:

LOW:  the frequency is used for purge mode.

MED:  the frequency is used to process modest traffic workload.

HIGH: the frequency is used to process busy traffic workload.

2.2 There are two phases to establish the power management system:

a.Initialization/Training phase. There is no traffic pass-through, the system
will test average empty poll numbers  with LOW/MED/HIGH  power state. Those
average empty poll numbers will be the baseline for the normal phase. The
system will collect all core's counter every 100ms. The Training phase will
take 5 seconds.

b.Normal phase. When the real traffic pass-though, the system will compare
run-time empty poll moving average value with base line then make decision to
move to HIGH power state of MED  power state. The system will collect all
core's counter every 10ms.

``training_flag`` : optional, enable/disable training mode. Default value is 0.
 If the training_flag is set as 1(true), then the application will start in
 training mode and print out the trained threshold values. If the training_flag
 is set as 0(false), the application will start in normal mode, and will use
 either the default thresholds or those supplied on the command line. The
 trained threshold values are specific to the user’s system, may give a better
 power profile when compared to the default threshold values.

``med_threshold`` : optional, sets the empty poll threshold of a modestly busy
system state. If this is not supplied, the application will apply the default
value of 350000.

``high_threshold`` : optional, sets the empty poll threshold of a busy system
state. If this is not supplied, the application will apply the default value of
580000.


Preparation Work for Settings
=============================
BIOS setting::

    1. Turn on Speedstep option in BIOS
    2. Turn on Turbo in BIOS
    3. Turn off Hyper Threading

Linux setting::

    1. Use intel_pstate driver for CPU frequency control
    2. modprobe msr

sys_min=/sys/devices/system/cpu/cpu{}/cpufreq/cpuinfo_min_freq
sys_max=/sys/devices/system/cpu/cpu{}/cpufreq/cpuinfo_max_freq
no_turbo_max=$(rdmsr -p 1 0x0CE -f 15:8 -d)00000

cur_min=/sys/devices/system/cpu/cpu{}/cpufreq/scaling_min_freq
cur_max=/sys/devices/system/cpu/cpu{}/cpufreq/scaling_max_freq


Test Case1 : Basic Training mode test based on one NIC with l3fwd-power
=======================================================================
Step 1. Bind One NIC to DPDK driver, launch l3fwd-power with empty-poll enabled

    ./<build_target>/examples/dpdk-l3fwd-power -l 1-2 -n 4 -- -p 0x1 -P --config="(0,0,2)" --empty-poll="1,0,0" -l 10 -m 6 -h 1

Step 2. Check the log also when changing the inject packet rate as following:

    Injected Rate(1024B, dst_ip=1.1.1.1): 10G -> 0.1G -> 10G -> 0.1G -> 10G ->
    0.1G The frequency will be set to MED when we inject 0.1G and return to HGH
    when inject 10G Rate, check the frequency of the forwarding core(core 2)
    When traffic is 10G:  cur_min=cur_max=no_turbo_max
    When traffic is 0.1G: cur_min=cur_max=[no_turbo_max-500000]


Test Case2: No-Training mode test based on one NIC with l3fwd-power
===================================================================
Step 1. Bind One NIC to DPDK driver, launch l3fwd-power with empty-poll enabled

   ./<build_target>/examples/dpdk-l3fwd-power -l 1-2 -n 4  -- -p 0x1 -P --config="(0,0,2)" --empty-poll="0,350000,500000" -l 10 -m 6 -h 1

Step 2. Check no training steps are executed in sample's launch log.
