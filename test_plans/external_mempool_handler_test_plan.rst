.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2017 Intel Corporation

==============================
External Mempool Handler Tests
==============================

External Mempool Handler feature is an extension to the mempool API that
allows users to add and use an alternative mempool handler, which allows
external memory subsystems such as external hardware memory management
systems and software based memory allocators to be used with DPDK.

Test Case 1: Multiple producers and multiple consumers
======================================================

1. Default mempool handler operations RTE_MBUF_DEFAULT_MEMPOOL_OPS is "ring_mp_mc"::

      Launch test app with mempool operation "ring_mp_mc":
      parameter: --mbuf-pool-ops-name ring_mp_mc

2. Start test app and verify mempool autotest passed::

      ./<build_target>/app/test/dpdk-test -n 4 -c f --mbuf-pool-ops-name ring_mp_mc
      RTE>> mempool_autotest

3. Start testpmd with two ports and start forwarding::

      ./<build_target>/app/dpdk-testpmd -c 0x6 -n 4  -- -i --portmask=0x3
      testpmd> set fwd mac
      testpmd> start

4. Send hundreds of packets from tester ports
5. verify forwarded packets sequence and integrity

Test Case 2: Single producer and Single consumer
================================================

1. Launch test app with mempool operation "ring_sp_sc"::

      parameter: --mbuf-pool-ops-name ring_sp_sc

2. Start test app and verify mempool autotest passed::

      ./<build_target>/app/test/dpdk-test -n 4 -c f --mbuf-pool-ops-name ring_sp_sc
      RTE>> mempool_autotest

3. Start testpmd with two ports and start forwarding::

      ./<build_target>/app/dpdk-testpmd -c 0x6 -n 4  -- -i --portmask=0x3
      testpmd> set fwd mac
      testpmd> start

4. Send hundreds of packets from tester ports
5. verify forwarded packets sequence and integrity

Test Case 3: Single producer and Multiple consumers
===================================================

1. Launch test app with mempool operation "ring_sp_mc"::

      parameter: --mbuf-pool-ops-name ring_sp_mc

2. Start test app and verify mempool autotest passed::

      ./<build_target>/app/test/dpdk-test -n 4 -c f --mbuf-pool-ops-name ring_sp_mc
      RTE>> mempool_autotest

3. Start testpmd with two ports and start forwarding::

      ./<build_target>/app/dpdk-testpmd -c 0x6 -n 4  -- -i --portmask=0x3
      testpmd> set fwd mac
      testpmd> start

4. Send hundreds of packets from tester ports
5. verify forwarded packets sequence and integrity

Test Case 4: Multiple producers and single consumer
===================================================

1. Launch test app with mempool operation "ring_mp_sc"::

      parameter: --mbuf-pool-ops-name ring_mp_sc

2. Start test app and verify mempool autotest passed::

      ./<build_target>/app/test/dpdk-test -n 4 -c f --mbuf-pool-ops-name ring_mp_sc
      RTE>> mempool_autotest

3. Start testpmd with two ports and start forwarding::

      ./<build_target>/app/dpdk-testpmd -c 0x6 -n 4  -- -i --portmask=0x3
      testpmd> set fwd mac
      testpmd> start

4. Send hundreds of packets from tester ports
5. verify forwarded packets sequence and integrity

Test Case 4: Stack mempool handler
==================================

1. Launch test app with mempool operation "stack"::

      parameter: --mbuf-pool-ops-name stack

2. Start test app and verify mempool autotest passed::

      ./<build_target>/app/test/dpdk-test -n 4 -c f --mbuf-pool-ops-name stack
      RTE>> mempool_autotest

3. Start testpmd with two ports and start forwarding::

      ./<build_target>/app/dpdk-testpmd -c 0x6 -n 4  -- -i --portmask=0x3
      testpmd> set fwd mac
      testpmd> start

4. Send hundreds of packets from tester ports
5. verify forwarded packets sequence and integrity
