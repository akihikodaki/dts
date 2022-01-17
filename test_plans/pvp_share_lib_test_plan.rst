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

=========================================
Vhost/virtio-user pvp share lib test plan
=========================================

Description
===========

The feature need compile dpdk as shared libraries, then application should use option ``-d`` to load the dynamic pmd that are built as shared libraries.

Test Case1: Vhost/virtio-user pvp share lib test with niantic
=============================================================

1. Enable the shared lib in DPDK configure file::

    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dc_args='-DRTE_BUILD_SHARED_LIB=1' --default-library=shared x86_64-native-linuxapp-gcc

2. Recompile dpdk code::

    ninja -C x86_64-native-linuxapp-gcc -j 55

3. Export shared lib files into host environment::

    export LD_LIBRARY_PATH=/root/dpdk/x86_64-native-linuxapp-gcc/drivers:$LD_LIBRARY_PATH

4. Bind niantic port with vfio-pci, use option ``-d`` to load the dynamic pmd when launch vhost::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -c 0x03 -n 4 -d librte_net_vhost.so.21.0 -d librte_net_i40e.so.21.0 -d librte_mempool_ring.so.21.0 \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i
    testpmd>start

5. Launch virtio-user::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x0c -n 4 -d librte_net_virtio.so.21.0 -d librte_mempool_ring.so.21.0 \
    --no-pci --file-prefix=virtio  --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net -- -i
    testpmd>start

6. Send traffic by packet generator, check the throughput with below command::

    testpmd>show port stats all

Test Case2: Vhost/virtio-user pvp share lib test with fortville
===============================================================

Similar as Test Case1, all steps are similar except step 4:

4. Bind fortville port with vfio-pci, use option ``-d`` to load the dynamic pmd when launch vhost::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -c 0x03 -n 4 -d librte_net_vhost.so -d librte_net_i40e.so -d librte_mempool_ring.so \
    --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i
    testpmd>start
