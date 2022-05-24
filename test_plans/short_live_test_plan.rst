.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

=============================
Short-lived Application Tests
=============================

This feature is to reduce application start-up time, and do more
cleanup when exit so that it could rerun many times.

Prerequisites
-------------

To test this feature, need to use linux time and start testpmd by: create
and mount hugepage, must create more hugepages so that could measure time more
obviously::

        # echo 8192 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
        # mount -t hugetlbfs hugetlbfs /mnt/huge

Bind nic to DPDK::

        ./usertools/dpdk-devbind.py -b vfio-pci device_bus_id

Start testpmd using time::

        # echo quit | time ./app/dpdk-testpmd -c 0x3 -n 4 -- -i


Test Case 1: basic fwd testing
------------------------------

1. Start testpmd::

      ./app/dpdk-testpmd -c 0x3 -n 4 -- -i

2. Set fwd mac
3. Send packet from pkg
4. Check all packets could be fwd back

Test Case 2: Get start up time
------------------------------

1. Start testpmd::

    echo quit | time ./app/dpdk-testpmd -c 0x3 -n 4 --huge-dir /mnt/huge -- -i

2. Get the time stats of the startup
3. Repeat step 1~2 for at least 5 times to get the average

Test Case 3: Clean up with Signal -- testpmd
--------------------------------------------

1. Create 4G hugepages, so that could save times when repeat::

    echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
    mount -t hugetlbfs hugetlbfs /mnt/huge1

2. Start testpmd::

    ./app/dpdk-testpmd -c 0x3 -n 4 --huge-dir /mnt/huge1 -- -i

3. Set fwd mac
4. Send packets from pkg
5. Check all packets could be fwd back
6. Kill the testpmd in shell using below commands alternately::

      SIGINT:  pkill -2  dpdk-testpmd
      SIGTERM: pkill -15 dpdk-testpmd

7. Repeat step 1-6 for 20 times, and packet must be fwd back with no error for each time.


Test Case 4: Clean up with Signal -- l2fwd
------------------------------------------

0. Build l2fwd example::

    meson configure -Dexamples=l2fwd x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc

1. Create 4G hugepages, so that could save times when repeat::

    echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
    mount -t hugetlbfs hugetlbfs /mnt/huge1

2. Start testpmd::

    ./examples/dpdk-l2fwd -c 0x3 -n 4 --huge-dir /mnt/huge1 -- -p 0x01

3. Set fwd mac
4. Send packets from pkg
5. Check all packets could be fwd back
6. Kill the testpmd in shell using below commands alternately::

      SIGINT:  pkill -2  dpdk-l2fwd
      SIGTERM: pkill -15 dpdk-l2fwd

7. Repeat step 1-6 for 20 times, and packet must be fwd back with no error for each time.

Test Case 5: Clean up with Signal -- l3fwd
------------------------------------------

0. Build l3fwd example::

    meson configure -Dexamples=l3fwd x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc

1. Create 4G hugepages, so that could save times when repeat::

      echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
      mount -t hugetlbfs hugetlbfs /mnt/huge1

2. Start testpmd::

     ./examples/dpdk-l3fwd -c 0x3 -n 4 --huge-dir /mnt/huge1 -- -p 0x01 --config="(0,0,1)"

3. Set fwd mac
4. Send packets from pkg
5. Check all packets could be fwd back
6. Kill the testpmd in shell using below commands alternately::

     SIGINT:  pkill -2  dpdk-l3fwd
     SIGTERM: pkill -15 dpdk-l3fwd

7. Repeat step 1-6 for 20 times, and packet must be fwd back with no error for each time.
