.. Copyright (c) <2019-2020>, Intel Corporation
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
DPDK ABI Stable Tests
=====================

Description
===========

This test suite includes both functional and performance test cases to
ensure that DPDK point releases (xx.02, xx.05, xx.08) are not only binary
compatible, but are also functionally and reasonably performance
compatibly with the previous vxx.11 release.


Compiling Steps
===============

Compile shared library/application from DPDK xx.11 release.
Change the option in config/common_base configuration file::

  CONFIG_RTE_BUILD_SHARED_LIB=y

And then, compile the DPDK::

  make install -j T=x86_64-native-linuxapp-gcc

Keep this DPDK folder as <dpdk_xx11>, e.g. <dpdk_1911>.

Compile shared library from DPDK point releasees (xx.02, xx.05, xx.08).
Command lines are same to above.
Keep this DPDK folder as <dpdk_xxxx>. e.g. <dpdk_2002>

Setup library path in environment::

  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH,<dpdk_2002>


Common Test Steps
=================

Comparing to test static dpdk application, ABI stable checking use
dynamic dpdk application, and shared library. Launching dynamic dpdk
application steps are below,

Go into <dpdk_1911> directory, launch application with specific library::

  testpmd -c 0xf -n 4 -d <dpdk_2002> -- -i

Expect the application could launch successfully.

Then, execute test steps with the application.

Reuse our existing test suites for ABI stable checking.


Execute Test Suites
===================

  +===============================+========================+
  |       Test Suites              |          Type           |
  +===============================+========================+
  |   unit_tests_cmdline           |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_crc               |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_dump              |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_eal               |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_kni               |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_loopback          |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_lpm               |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_mbuf              |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_mempool           |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_pmd_perf          |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_power             |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_qos               |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_ringpmd           |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_ring              |     functional          |
  +-------------------------------+------------------------+
  |   unit_tests_timer             |     functional          |
  +-------------------------------+------------------------+
  |   vhost_1024_ethports          |     functional          |
  +-------------------------------+------------------------+
  |   vhost_dequeue_zero_copy      |     functional          |
  +-------------------------------+------------------------+
  |   vhost_enqueue_interrupt      |     functional          |
  +-------------------------------+------------------------+
  |   vhost_event_idx_interrupt    |     functional          |
  +-------------------------------+------------------------+
  |   vhost_multi_queue_qemu       |     functional          |
  +-------------------------------+------------------------+
  |   vhost_pmd_xstats             |     functional          |
  +-------------------------------+------------------------+
  |   vhost_virtio_user_interrupt  |     functional          |
  +-------------------------------+------------------------+
  |   vhost_user_live_migration    |     functional          |
  +-------------------------------+------------------------+
  |   flow_classify                |     functional          |
  +-------------------------------+------------------------+
  |   flow_classify_softnic        |     functional          |
  +-------------------------------+------------------------+
  |   vhost_virtio_pmd_interrupt   |     functional          |
  +-------------------------------+------------------------+
  |   l2fwd                        |     performance         |
  +-------------------------------+------------------------+
  |   nic_single_core_perf         |     performance         |
  +-------------------------------+------------------------+
  |   l3fwd                        |     performance         |
  +-------------------------------+------------------------+
