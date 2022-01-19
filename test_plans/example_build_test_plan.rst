.. Copyright (c) <2011>, Intel Corporation
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

=============
Example Build
=============

This test case is for testing that all applications under DPDK examples compile successfully.
Such as these applications::

    - bbdev_app
    - bond
    - cmdline
    - distributor
    ...

Prerequisites
=============

Dependency package requirements:

    - libvert: https://libvirt.org/
    - intel-cmt-cat: https://github.com/01org/intel-cmt-cat

Test case: example build
========================

compile the applications of examples  successfully::

    meson configure -Dexamples=all x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc

If the compilation is successful, it will be the same as the shown in the terminal. ::

    ...
    [188/193] Linking target examples/dpdk-efd_node
    [189/193] Linking target examples/dpdk-vhost_crypto
    [190/193] Linking target examples/dpdk-pipeline
    [191/193] Linking target examples/dpdk-efd_server
    [192/193] Linking target examples/dpdk-vhost
    [193/193] Linking target examples/dpdk-vmdq
