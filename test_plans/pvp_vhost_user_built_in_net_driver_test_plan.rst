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

========================================
Vhost-user built-in net driver test plan
========================================

Description
===========

This feature test a very simple vhost-user net driver which demonstrates how to use the generic
vhost APIs by adding option "--builtin-net-driver" when launch vswitch.
This feature only can test with vswitch, and it is disabled by default.

Prerequisites
=============
Device start fails if NIC’s max queues > the default number of 128.
mbuf pool size is dependent on the MAX_QUEUES configuration, if NIC’s max queue number is larger than 128, device start will fail due to insufficient mbuf.
Change the default number to make it work as below, just set the number according to the NIC’s property:
For niantic 82599ES，#define MAX_QUEUES 128
For fortville X710, #define MAX_QUEUES 192
For fortville XXV710, #define MAX_QUEUES 352
For fortville XL710, #define MAX_QUEUES 512

Modify the testpmd code as following::

        --- a/examples/vhost/main.c
        +++ b/examples/vhost/main.c
        @@ -28,7 +28,7 @@
         #include "main.h"
         #ifndef MAX_QUEUES
        -#define MAX_QUEUES 128
        +#define MAX_QUEUES 512
         #endif

Test Case1: PVP test with vhost built-in net driver
===================================================

1. Bind one port to igb_uio, launch vswitch::

    ./vhost-switch -l 1-2 -n 4 --socket-mem 2048,2048 -- \
    -p 0x1 --mergeable 0 --vm2vm 1 --builtin-net-driver  --socket-file ./vhost-net

2. Launch virtio-user::

    ./testpmd -l 3-4 -n 4  --no-pci --socket-mem 2048,2048 --file-prefix=virtio-user \
    --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1 -- -i --rxq=1 --txq=1
    testpmd>set fwd mac      # ixia can't receive packets when io fwd, packtes still fwd to virtio-user with the dest mac addr
    testpmd>start tx_first   # send packets from virtio-user first to let vswitch know the mac addr

3. Send traffic with (vlan_id = 1000, dest mac addr = 00:11:22:33:44:10) and different packet size includes [64, 128, 256, 512, 1024, 1518] by packet generator, check the throughput with below command::

    testpmd>show port stats all
