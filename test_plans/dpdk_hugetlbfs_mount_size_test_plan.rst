.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2016 Intel Corporation

===========================================
DPDK Hugetlbfs Mount Size Feature Test Plan
===========================================

This feature is to limit DPDK to use the exact size which is the mounted hugepage size.

Prerequisites
=============

To test this feature, following options need to pass the the kernel:
hugepagesz=1G hugepages=8 default_hugepagesz=1G

Test Case 1: default hugepage size w/ and w/o numa
==================================================

1. Create and mount hugepages::

    mount -t hugetlbfs hugetlbfs /mnt/huge

2. Bind one nic port to vfio-pci driver, launch testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 --huge-dir /mnt/huge --file-prefix=abc -- -i
    testpmd>start

3. Send packet with packet generator, check testpmd could forward packets correctly.

4. Goto step 2 resart testpmd with numa support::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 --huge-dir /mnt/huge --file-prefix=abc -- -i --numa
    testpmd>start

5. Send packets with packet generator, make sure testpmd could receive and fwd packets correctly.

Test Case 2: mount size exactly match total hugepage size with two mount points
===============================================================================

1. Create and mount hugepages::

    mount -t hugetlbfs -o size=4G hugetlbfs /mnt/huge1
    mount -t hugetlbfs -o size=4G hugetlbfs /mnt/huge2

2. Bind two nic ports to vfio-pci driver, launch testpmd with numactl::

    numactl --membind=1 ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 31-32 -n 4 --legacy-mem --socket-mem 0,2048 --huge-dir /mnt/huge1 --file-prefix=abc -a 82:00.0 -- -i --socket-num=1 --no-numa
    testpmd>start

    numactl --membind=1 ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 33-34 -n 4 --legacy-mem --socket-mem 0,2048  --huge-dir /mnt/huge2 --file-prefix=bcd -a 82:00.1 -- -i --socket-num=1 --no-numa
    testpmd>start

3. Send packets with packet generator, make sure two testpmd could receive and fwd packets correctly.

Test Case 3: mount size greater than total hugepage size with single mount point
================================================================================

1. Create and mount hugepage::

    mount -t hugetlbfs -o size=9G hugetlbfs /mnt/huge

2. Bind one nic port to vfio-pci driver, launch testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 --legacy-mem --huge-dir /mnt/huge --file-prefix=abc -- -i
    testpmd>start

3. Send packets with packet generator, make sure testpmd could receive and fwd packets correctly.

Test Case 4: mount size greater than total hugepage size with multiple mount points
===================================================================================

1. Create and mount hugepage::

    mount -t hugetlbfs -o size=4G hugetlbfs /mnt/huge1
    mount -t hugetlbfs -o size=4G hugetlbfs /mnt/huge2
    mount -t hugetlbfs -o size=1G hugetlbfs /mnt/huge3

2. Bind one nic port to vfio-pci driver, launch testpmd::

    numactl --membind=0 ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4  --legacy-mem --socket-mem 2048,0 --huge-dir /mnt/huge1 --file-prefix=abc -- -i --socket-num=0 --no-numa
    testpmd>start

    numactl --membind=0 ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc -n 4  --legacy-mem --socket-mem 2048,0 --huge-dir /mnt/huge2 --file-prefix=bcd -- -i --socket-num=0 --no-numa
    testpmd>start

    numactl --membind=0 ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4  --legacy-mem --socket-mem 1024,0 --huge-dir /mnt/huge3 --file-prefix=fgh -- -i --socket-num=0 --no-numa
    testpmd>start

3. Send packets with packet generator, check first and second testpmd will start correctly while third one will report error with not enough mem in socket 0.

Test Case 5: run dpdk app in limited hugepages controlled by cgroup
===================================================================

1. Bind one nic port to vfio-pci driver, launch testpmd in limited hugepages::

    cgcreate -g hugetlb:/test-subgroup
    cgset -r hugetlb.1GB.limit_in_bytes=2147483648 test-subgroup
    cgexec -g hugetlb:test-subgroup numactl -m 1 ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3000 -n 4 -- -i --socket-num=1 --no-numa

2. Start testpmd and send packets with packet generator, make sure testpmd could receive and fwd packets correctly.
