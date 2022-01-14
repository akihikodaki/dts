.. Copyright (c) <2019>, Intel Corporation
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

=============================
vhost 1023 ethports test plan
=============================

This test plan test function of launch vhost with 1023 ethports.
Note: Because the value of MAX_FDS is 1024 and there is an extra gobal fd, the number of vdev is limit to 1023. 
So when vhost-user ports number > 1023, it will report an error "failed to add listen fd".

Test Case1:  Basic test for launch vhost with 1023 ethports
===========================================================

1. SW preparation: change "CONFIG_RTE_MAX_ETHPORTS" to 1023 in DPDK configure file::

    vi ./config/common_base
    -CONFIG_RTE_MAX_ETHPORTS=32
    +CONFIG_RTE_MAX_ETHPORTS=1023

2. Launch vhost with 1023 vdev::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3000 -n 4 --file-prefix=vhost --vdev 'eth_vhost0,iface=vhost-net,queues=1' \
    --vdev 'eth_vhost1,iface=vhost-net1,queues=1' ... -- -i # only list two vdev, here ommit other 1021 vdevs, from eth_vhost2 to eth_vhost1022

3. Change "CONFIG_RTE_MAX_ETHPORTS" back to 32 in DPDK configure file::

    vi ./config/common_base
    +CONFIG_RTE_MAX_ETHPORTS=32
    -CONFIG_RTE_MAX_ETHPORTS=1023
