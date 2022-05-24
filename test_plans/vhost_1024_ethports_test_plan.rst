.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

=============================
vhost 1023 ethports test plan
=============================

This test plan test function of launch vhost with 1023 ethports.
Note: Because the value of MAX_FDS is 1024 and there is an extra gobal fd, the number of vdev is limit to 1023. 
So when vhost-user ports number > 1023, it will report an error "failed to add listen fd".

Test Case1:  Basic test for launch vhost with 1023 ethports
===========================================================

1. SW preparation::
    build dpdk with '-Dmax_ethports=1024'

2. Launch vhost with 1023 vdev::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3000 -n 4 --file-prefix=vhost --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' ... -- -i # only list two vdev, here ommit other 1021 vdevs, from eth_vhost2 to eth_vhost1022

3. restore dpdk::
    build dpdk with '-Dmax_ethports=32'
