.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2020 Intel Corporation

==============================
PMD power management test plan
==============================

This test plan intends to test the PMD power management functionality by
measuring total power consumption on the system with `turbostat`.

Preparation Work
================

1. Tests require that your hardware does support WAITPKG instruction set
    - to check if CPU supports WAITPKG, run the following command::

        cat /proc/cpuinfo | grep waitpkg

      if the output is not empty, the platform supports WAITPKG instructions.
2. Ensure Hardware P-States (HWP) is enabled in the BIOS
3. Ensure Intel(R) VT-d is enabled in the BIOS
4. Ensure the kernel command-line includes "intel_iommu=on iommu=pt" parameters
5. Ensure the VFIO PCI driver is available and loaded

    - To check if VFIO PCI module is loaded, run the following command::

        lsmod | grep vfio

      The output should contain at least the following drivers: `vfio-pci`,
      `vfio` and `vfio_iommu_type1`
6. Ensure the `turbostat` tool is present on your platform, and reports average
   core frequency as well as platform power consumption

    - This can be checked by issuing the following command::

        turbostat -l

      and checking if the list of available columns has `PkgWatt`, `Core` (or
      `CPU`), and `Bzy_MHz` columns
7. Check if MSR driver is built-in or is loaded

    - To check if the module is built-in, run the following command::

        cat /usr/lib/modules/$(uname -r)/modules.builtin | grep msr.ko

      if the output is not empty, the MSR module is built into the kernel, and
      no further action is necessary.
    - To check if the module is loaded, run the following command::

        lsmod | grep msr

      Non-empty output will indicate that MSR kernel module is loaded.
    - If the MSR driver is not loaded but is available as a module, the
      following command will load it::

        modprobe msr

8. At least one physical NIC port is required, and should be bound to the VFIO
   PCI driver

    - Use `dpdk-devbind.py` to bind physical NIC ports to VFIO PCI driver::

        dpdk-devbind.py -b vfio-pci <PCI address 1> <PCI address 2> ...

    - In a situation where number of logical CPU cores on a platform exceeds the
      maximum number of queues a physical NIC port can have, use more NIC ports
      in the same way (i.e. bind them to VFIO PCI driver)


Test Case 1 : Test PMD power management in pstate mode
======================================================
Step 1. Reset all pstate min/max frequency assignments for all cores

- This can be done by overwriting lowest and highest frequencies in the CPU
  scaling driver::

        # assume min/max frequencies are 1.2GHz/3.6GHz respectively
        for d in /sys/bus/cpu/devices/cpu*/cpufreq/
        do
            cat $d/cpuinfo_min_freq > $d/scaling_min_freq
            cat $d/cpuinfo_max_freq > $d/scaling_max_freq
        done

Step 2. Launch l3fwd-power and enable "scale" PMD power management mode, and
assign each forwarding lcore (including main lcore) exactly one queue::

    ./examples/dpdk-l3fwd-power -l 0-... -- --pmd-mgmt=scale -P -p 0x1 --config="(0,0,0),(0,1,1),(0,2,2),..."
    Example:
    ./examples/dpdk-l3fwd-power  -l 0-63 -- --pmd-mgmt=scale -P -p 0x1 --config="(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16),(0,16,17),(0,17,18),(0,18,19),(0,19,20),(0,20,21),(0,21,22),(0,22,23),(0,23,24),(0,24,25),(0,25,26),(0,26,27),(0,27,28),(0,28,29),(0,29,30),(0,30,31),(0,31,32),(0,32,33),(0,33,34),(0,34,35),(0,35,36),(0,36,37),(0,37,38),(0,38,39),(0,39,40),(0,40,41),(0,41,42),(0,42,43),(0,43,44),(0,44,45),(0,45,46),(0,46,47),(0,47,48),(0,48,49),(0,49,50),(0,50,51),(0,51,52),(0,52,53),(0,53,54),(0,54,55),(0,55,56),(0,56,57),(0,57,58),(0,58,59),(0,59,60),(0,60,61),(0,61,62),(0,62,63)"

- The DPDK core mask must include all cores (e.g. for a machine with 64 cores, the
  parameter should be set to `-l 0-63`)
- The port mask must include all physical ports that will be used by the test
- The `--config` parameter must reflect the number of queues used by each port.
  For example, if the maximum number of queues is 32 while the platform has 64
  cores, the test will require two physical ports, and the first 32 cores will
  use port 0 (`--config="(0,0,0),(0,1,1),(0,2,2)..."`) while the next 32 cores
  will use port 1 (`--config="(1,0,32),(1,1,33),(1,2,34)..."`)

Step 3. Ensure all cores operate at lowest frequency available. To find lowest
frequency, read the `cpuinfo_min_freq` value for core 0 from sysfs::

    # find lowest frequency available, in KHz
    cat /sys/bus/cpu/devices/cpu0/cpufreq/cpuinfo_min_freq
    1200000

Then, *while running `dpdk-l3fwd-power` as described in Step 2*, also run
`turbostat` and ensure that all forwarding cores are running at lowest frequency
available for those cores::

    # assume min frequency is 1.2GHz
    turbostat -i 1 -n 1 -s "Core,Bzy_MHz"
    CPU     Bzy_MHz
    -       1200
    0       1200
    1       1200
    2       1200
    3       1200
    4       1200
    5       1200
    6       1200
    7       1200
    ...

Step 4. Repeat Step 1 to reset the pstate scaling settings.

Pass Criteria: average frequency on all cores is roughly equal to minimum
frequency (there is some variance to be expected, values within 100MHz are
acceptable)


Test Case 2 : Test PMD power management in pause mode with WAITPKG
=====================================================================
Requirement: this test requires that the platform *must* support WAITPKG instruction set

Step 1. Launch l3fwd-power in "baseline" mode, and assign each forwarding lcore
(not including main lcore) exactly one queue::

    ./examples/dpdk-l3fwd-power -l 0-... -- --pmd-mgmt=baseline -P -p 0x1 --config="(0,0,1),(0,1,2),(0,2,3),..."
    Example:
    ./examples/dpdk-l3fwd-power  -l 0-63 -- --pmd-mgmt=baseline -P -p 0x1 --config="(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16),(0,16,17),(0,17,18),(0,18,19),(0,19,20),(0,20,21),(0,21,22),(0,22,23),(0,23,24),(0,24,25),(0,25,26),(0,26,27),(0,27,28),(0,28,29),(0,29,30),(0,30,31),(0,31,32),(0,32,33),(0,33,34),(0,34,35),(0,35,36),(0,36,37),(0,37,38),(0,38,39),(0,39,40),(0,40,41),(0,41,42),(0,42,43),(0,43,44),(0,44,45),(0,45,46),(0,46,47),(0,47,48),(0,48,49),(0,49,50),(0,50,51),(0,51,52),(0,52,53),(0,53,54),(0,54,55),(0,55,56),(0,56,57),(0,57,58),(0,58,59),(0,59,60),(0,60,61),(0,61,62),(0,62,63)"

- Note that lcore 0 is used by telemetry, so the `--config` parameter will skip
  the lcore 0 and start from lcore 1
- See notes for Test Case 1 for more information about how to correctly set up
  the command-line parameters

Step 2. While Step 1 is in progress, also run `turbostat` and make note of the
power consumption to establish a baseline against which further measurements
will be compared to::

    turbostat -i 1 -n 1 -s "PkgWatt"

- The PkgWatt value will be per-socket, as well as aggregate per platform::

    ...
    PkgWatt
    16.31  # aggregate
    8.83   # socket 0
    7.48   # socket 1
    ...

    The value that should be noted is the topmost value (aggregate power usage
    across all sockets).

Step 3. Relaunch l3fwd-power and enable "pause" PMD power management mode, and
assign each forwarding lcore (including main lcore) exactly one queue::

    ./examples/dpdk-l3fwd-power -l 0-... -- --pmd-mgmt=pause -P -p 0x1 --config="(0,0,0),(0,1,1),(0,2,2),..."
    Example:
    ./examples/dpdk-l3fwd-power  -l 0-63 -- --pmd-mgmt=pause -P -p 0x1 --config="(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16),(0,16,17),(0,17,18),(0,18,19),(0,19,20),(0,20,21),(0,21,22),(0,22,23),(0,23,24),(0,24,25),(0,25,26),(0,26,27),(0,27,28),(0,28,29),(0,29,30),(0,30,31),(0,31,32),(0,32,33),(0,33,34),(0,34,35),(0,35,36),(0,36,37),(0,37,38),(0,38,39),(0,39,40),(0,40,41),(0,41,42),(0,42,43),(0,43,44),(0,44,45),(0,45,46),(0,46,47),(0,47,48),(0,48,49),(0,49,50),(0,50,51),(0,51,52),(0,52,53),(0,53,54),(0,54,55),(0,55,56),(0,56,57),(0,57,58),(0,58,59),(0,59,60),(0,60,61),(0,61,62),(0,62,63)"

- See notes for Test Case 1 Step 2 for more information about how to correctly
  set up the command-line parameters

Step 4. While Step 3 is in progress, repeat Step 2 to measure power consumption
with "pause" PMD power management mode.

Pass Criteria: PkgWatt number has measurably (e.g. >5%) decreased from the
baseline.

Test Case 3 : Test PMD power management in monitor mode
=======================================================
Requirement: this test requires that the platform *must* support WAITPKG instruction set

Step 1. Repeat Step 1 of Test Case 2 to run l3fwd-power in "baseline" mode.
Step 2. While Step 1 is in progress, repeat Step 2 of Test Case 2 to measure
power usage baseline.

Step 3. Relaunch l3fwd-power and enable "monitor" PMD power management mode, and
assign each forwarding lcore (including main lcore) exactly one queue::

    ./examples/dpdk-l3fwd-power -l 0-... -- --pmd-mgmt=monitor -P -p 0x1 --config="(0,0,0),(0,1,1),(0,2,2),..."
    Example:
    ./examples/dpdk-l3fwd-power  -l 0-63 -- --pmd-mgmt=monitor -P -p 0x1 --config="(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16),(0,16,17),(0,17,18),(0,18,19),(0,19,20),(0,20,21),(0,21,22),(0,22,23),(0,23,24),(0,24,25),(0,25,26),(0,26,27),(0,27,28),(0,28,29),(0,29,30),(0,30,31),(0,31,32),(0,32,33),(0,33,34),(0,34,35),(0,35,36),(0,36,37),(0,37,38),(0,38,39),(0,39,40),(0,40,41),(0,41,42),(0,42,43),(0,43,44),(0,44,45),(0,45,46),(0,46,47),(0,47,48),(0,48,49),(0,49,50),(0,50,51),(0,51,52),(0,52,53),(0,53,54),(0,54,55),(0,55,56),(0,56,57),(0,57,58),(0,58,59),(0,59,60),(0,60,61),(0,61,62),(0,62,63)"

- See notes for Test Case 1 Step 2 for more information about how to correctly
  set up the command-line parameters

Step 4. While Step 3 is in progress, repeat Step 2 of Test Case 2 to measure
power consumption with PMD power management.

Pass Criteria: PkgWatt number has measurably (e.g. >5%) decreased from the
baseline.
