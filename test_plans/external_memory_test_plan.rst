.. Copyright (c) <2015-2018>, Intel Corporation
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
Ability to use external memory test plan
=========================================

Description:
------------
Provide an abstraction for DPDK hugepage allocation, to have a "default" memory
allocator that will allocate hugepages, but also have custom allocator support for
external memory.

Test case 1: IGB_UIO and anonymous memory allocation
-----------------------------------------------------
Bind the ports to IGB_UIO driver

Start testpmd with --mp-alloc=xmem flag::

   ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -- --mp-alloc=xmem -i

Start forward in testpmd

Start send traffic from outside to test the forward function


Test case 2: IGB_UIO and anonymous hugepage memory allocation
--------------------------------------------------------------

Bind the ports to IGB_UIO driver

Start testpmd with --mp-alloc=xmemhuge flag::

   ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -- --mp-alloc=xmemhuge -i

Start forward in testpmd

Start send traffic from outside to test the forward function


Test case 3: VFIO and anonymous memory allocation
--------------------------------------------------
Bind the ports to vfio-pci driver

Start testpmd with --mp-alloc=xmem flag::

   ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -- --mp-alloc=xmem -i

Start forward in testpmd

Start send traffic from outside to test the forward function


Test case 4: VFIO and anonymous hugepage memory allocation
-----------------------------------------------------------
Bind the ports to vfio-pci driver

Start testpmd with --mp-alloc=xmemhuge flag::

   ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -- --mp-alloc=xmemhuge -i

Start forward in testpmd

Start send traffic from outside to test the forward function