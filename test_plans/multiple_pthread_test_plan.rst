.. Copyright (c) < 2017 >, Intel Corporation
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

=====================
Multiple Pthread Test
=====================


Description
-----------

This test is a basic multiple pthread test which demonstrates the basics 
of control group. Cgroup is a Linux kernel feature that limits, accounts 
for and isolates the resource usage, like CPU, memory, disk I/O, network, 
etc of a collection of processes. Now, it's focus on the CPU usage. 

Prerequisites
-------------
Support igb_uio driver, kernel is 3.11+. 
Use "modprobe uio" "modprobe igb_uio" and then
use "./tools/dpdk_nic_bind.py --bind=igb_uio device_bus_id" to bind the ports.

Assuming that an Intel's DPDK build has been set up and the testpmd
applications have been built.

Os required: Linux and FreeBSD.
The command used in the test plan is only for Linux OS.

The format pattern::

    –lcores=’<lcore_set>[@cpu_set][,<lcore_set>[@cpu_set],...]’

‘lcore_set’ and ‘cpu_set’ can be a single number, range or a group. 
A number is a “digit([0-9]+)”; a range is “<number>-<number>”;
a group is “(<number|range>[,<number|range>,...])”.
If a ‘@cpu_set’ value is not supplied, 
the value of ‘cpu_set’ will default to the value of ‘lcore_set’.
For example, "--lcores='1,2@(5-7),(3-5)@(0,2),(0,6),7-8'" 
which means start 9 EAL thread::

    lcore 0 runs on cpuset 0x41 (cpu 0,6);
    lcore 1 runs on cpuset 0x2 (cpu 1);
    lcore 2 runs on cpuset 0xe0 (cpu 5,6,7);
    lcore 3,4,5 runs on cpuset 0x5 (cpu 0,2);
    lcore 6 runs on cpuset 0x41 (cpu 0,6);
    lcore 7 runs on cpuset 0x80 (cpu 7);
    lcore 8 runs on cpuset 0x100 (cpu 8).

Test Case 1: Basic operation
----------------------------

To run the application, start the testpmd with the lcores all running with
threads and also the unique core assigned, command as follows::

    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='0@8,(4-5)@9' -n 4 -- -i

Using the command to make sure the lcore are init on the correct cpu::

    ps -C testpmd -L -opid,tid,%cpu,psr,args

Result as follows::

    PID     TID    %CPU   PSR COMMAND
    31038   31038  22.5   8   ./x86_64-native-linuxapp-gcc/app/testpmd --lcores=0@8,(4-5)@9 -n 4 -- -i
    31038   31039  0.0    8   ./x86_64-native-linuxapp-gcc/app/testpmd --lcores=0@8,(4-5)@9 -n 4 -- -i
    31038   31040  0.0    9   ./x86_64-native-linuxapp-gcc/app/testpmd --lcores=0@8,(4-5)@9 -n 4 -- -i
    31038   31041  0.0    9   ./x86_64-native-linuxapp-gcc/app/testpmd --lcores=0@8,(4-5)@9 -n 4 -- -i
    31038   31042  0.0    8   ./x86_64-native-linuxapp-gcc/app/testpmd --lcores=0@8,(4-5)@9 -n 4 -- -i

Their TIDs are for these threads as below::

    +------------------------+
    | TID   | THREAD         |
    +-------+----------------+
    | 31038 | Master thread  |
    +-------+----------------+
    | 31039 |Eal-intr-thread |
    +------+-----------------+
    | 31040 | Lcore-slave-4  |
    +-------+----------------+
    | 31041 | Lcore-slave-5  |
    +-------+----------------+
    | 31042 | Pdump-thread   |
    +-------+----------------+

Before running the test, make sure the core is a unique one otherwise, 
the throughput will be floating on different cores,
configure lcore 4&5 used for packet forwarding, command as follows::

    testpmd>set corelist 4,5

Pay attention that set corelist need to be configured before start, 
otherwise, it will not work::

    testpmd>start

Check forward configuration::

    testpmd>show config fwd
    Logical Core 4 (socket 0) forwards packets on 1 streams:
      RX P=0/Q=0 (socket 1) -> TX P=1/Q=0 (socket 1) peer=02:00:00:00:00:01
    Logical Core 5 (socket 0) forwards packets on 1 streams:
      RX P=1/Q=0 (socket 1) -> TX P=0/Q=0 (socket 1) peer=02:00:00:00:00:00

Send packets continuous::

    PID    TID   %CPU   PSR COMMAND
    31038  31038  0.6   8   ./x86_64-native-linuxapp-gcc/app/testpmd --lcores=0@8,(4-5)@9 -n 4 -- -i
    31038  31039  0.0   8   ./x86_64-native-linuxapp-gcc/app/testpmd --lcores=0@8,(4-5)@9 -n 4 -- -i
    31038  31040  1.5   9   ./x86_64-native-linuxapp-gcc/app/testpmd --lcores=0@8,(4-5)@9 -n 4 -- -i
    31038  31041  1.5   9   ./x86_64-native-linuxapp-gcc/app/testpmd --lcores=0@8,(4-5)@9 -n 4 -- -i
    31038  31042  0.0   8   ./x86_64-native-linuxapp-gcc/app/testpmd --lcores=0@8,(4-5)@9 -n 4 -- -i

You can see TID 31040(Lcore 4), 31041(Lore 5) are running.


Test Case 2: Positive Test
--------------------------
Input random valid commands to make sure the commands can work,
Give examples, suppose DUT have 128 cpu core.

Case 1::

    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='0@8,(4-5)@(8-11)' -n 4 -- -i

It means start 3 EAL thread::

    lcore 0 runs on cpuset 0x100 (cpu 8);
    lcore 4,5 runs on cpuset 0x780 (cpu 8,9,10,11).

Case 2::

    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='1,2@(0-4,6),(3-4,6)@5,(7,8)' -n 4 -- -i

It means start 7 EAL thread::

    lcore 1 runs on cpuset 0x2 (cpu 1);
    lcore 2 runs on cpuset 0x5f (cpu 0,1,2,3,4,6);
    lcore 3,4,6 runs on cpuset 0x10 (cpu 5);
    lcore 7 runs on cpuset 0x80 (cpu 7);
    lcore 8 runs on cpuset 0x100 (cpu 8).

Case 3::

    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0,CONFIG_RTE_MAX_LCORE-1)@(4,5)' -n 4 -- -i

(default CONFIG_RTE_MAX_LCORE=128).
It means start 2 EAL thread::

    lcore 0,127 runs on cpuset 0x30 (cpu 4,5).

Case 4::

    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0,64-66)@(4,5)' -n 4 -- -i

It means start 4 EAL thread::

    lcore 0,64,65,66 runs on cpuset 0x30 (cpu 4,5).

Case 5::

    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='2-5,6,7-9' -n 4 -- -i

It means start 8 EAL thread::

    lcore 2 runs on cpuset 0x4 (cpu 2);
    lcore 3 runs on cpuset 0x8 (cpu 3);
    lcore 4 runs on cpuset 0x10 (cpu 4);
    lcore 5 runs on cpuset 0x20 (cpu 5);
    lcore 6 runs on cpuset 0x40 (cpu 6);
    lcore 7 runs on cpuset 0x80 (cpu 7);
    lcore 8 runs on cpuset 0x100 (cpu 8);
    lcore 9 runs on cpuset 0x200 (cpu 9).

Case 6::    

    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='2,(3-5)@3' -n 4 -- -i

It means start 4 EAL thread::

    lcore 2 runs on cpuset 0x4 (cpu 2);
    lcore 3,4,5 runs on cpuset 0x8 (cpu 3).

Case 7::

    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0,7-4)@(4,5)' -n 4 -- -i

It means start 5 EAL thread::

    lcore 0,4,5,6,7 runs on cpuset 0x30 (cpu 4,5)



Test Case 3: Negative Test
--------------------------
Input invalid commands to make sure the commands can't work::

    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0-,4-7)@(4,5)' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(-1,4-7)@(4,5)' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0,4-7-9)@(4,5)' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0,abcd)@(4,5)' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0,4-7)@(1-,5)' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0,4-7)@(-1,5)' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0,4-7)@(4,5-8-9)' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0,4-7)@(abc,5)' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0,4-7)@(4,xyz)' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0,4-7)=(8,9)' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='2,3 at 4,(0-1,,4))' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='[0-,4-7]@(4,5)' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='(0-,4-7)@[4,5]' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='3-4 at 3,2 at 5-6' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='2,,3''2--3' -n 4 -- -i
    ./x86_64-native-linuxapp-gcc/app/testpmd --lcores='2,,,3''2--3' -n 4 -- -i
