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

meson: CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=shared <build_target>;ninja -C <build_target>

Common Test Steps
=================

Comparing to test static dpdk application, ABI stable checking use
dynamic dpdk application, and shared library. Launching dynamic dpdk
application steps are below,

Go into <dpdk_1911> directory, launch application with specific library::

  ./<build_target>/app/dpdk-testpmd -c 0xf -n 4 -d <dpdk_2002> -- -i

Expect the application could launch successfully.

Then, execute test steps with the application.

Reuse our existing test suites for ABI stable checking.


Execute Test Suites
===================

.. table::

  +-------------------------------+------------------------+
  |       Test Suites             |          Type          |
  +===============================+========================+
  |   unit_tests_cmdline          |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_crc              |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_dump             |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_eal              |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_kni              |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_loopback         |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_lpm              |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_mbuf             |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_mempool          |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_pmd_perf         |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_power            |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_qos              |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_ringpmd          |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_ring             |     functional         |
  +-------------------------------+------------------------+
  |   unit_tests_timer            |     functional         |
  +-------------------------------+------------------------+
  |   vhost_1024_ethports         |     functional         |
  +-------------------------------+------------------------+
  |   vhost_dequeue_zero_copy     |     functional         |
  +-------------------------------+------------------------+
  |   vhost_enqueue_interrupt     |     functional         |
  +-------------------------------+------------------------+
  |   vhost_event_idx_interrupt   |     functional         |
  +-------------------------------+------------------------+
  |   vhost_multi_queue_qemu      |     functional         |
  +-------------------------------+------------------------+
  |   vhost_pmd_xstats            |     functional         |
  +-------------------------------+------------------------+
  |   vhost_virtio_user_interrupt |     functional         |
  +-------------------------------+------------------------+
  |   vhost_user_live_migration   |     functional         |
  +-------------------------------+------------------------+
  |   flow_classify               |     functional         |
  +-------------------------------+------------------------+
  |   flow_classify_softnic       |     functional         |
  +-------------------------------+------------------------+
  |   vhost_virtio_pmd_interrupt  |     functional         |
  +-------------------------------+------------------------+
  |   l2fwd                       |     performance        |
  +-------------------------------+------------------------+
  |   nic_single_core_perf        |     performance        |
  +-------------------------------+------------------------+
  |   l3fwd                       |     performance        |
  +-------------------------------+------------------------+


Negative Test Case
==================

Prepare 1 patch file, 0001-rte_tx_burst_t_add-one-argument-at-the-end.patch ::

  From 56eb4b14c2344fddc9f8ee1c6b5cf9ef4999ee80 Mon Sep 17 00:00:00 2001
  From: Herakliusz Lipiec <herakliusz.lipiec@intel.com>
  Date: Thu, 30 Jan 2020 17:19:19 +0000
  Subject: [PATCH] eth_tx_burst_t add one argument at the end

  compile with:
  meson configure -Ddisable_drivers=net/af_packet,net/ark,net/atlantic,net/avp,net/axgbe,net/bond,net/bnx2x,net/bnxt,net/cxgbe,net/dpaa,net/dpaa2,net/e1000,net/ena,net/enetc,net/enic,net/i40e,net/hinic,net/hns3,net/iavf,net/ice,net/kni,net/liquidio,net/memif,net/netvsc,net/nfp,net/null,net/octeontx,net/octeontx2,net/pcap,net/pfe,net/qede,net/sfc,net/softnic,net/tap,net/thunderx,net/vdev_netvsc,net/vhost,net/virtio,net/vmxnet3,common/cpt,common/dpaax,common/iavf,common/octeontx2,bus/dpaa,bus/fslmc,bus/ifpga,bus/vmbus,mempool/bucket,mempool/dpaa,mempool/dpaa2,mempool/octeontx2,mempool/stack,raw/dpaa2_cmdif,raw/dpaa2_qdma,raw/ioat,raw/ntb,raw/octeontx2_dma,raw/octeontx2_ep,raw/skeleton,crypto/caam_jr,crypto/ccp,crypto/dpaa_sec,crypto/dpaa2_sec,crypto/nitrox,crypto/null_crypto,crypto/octeontx_crypto,crypto/octeontx2_crypto,crypto/openssl,crypto/crypto_scheduler,crypto/virtio_crypto,vdpa/ifc,event/dpaa,event/dpaa2,event/octeontx2,event/opdl,event/skeleton,event/sw,event/dsw,event/octeontx,baseband/null,baseband/turbo_sw,baseband/fpga_lte_fec,net/failsafe

  Signed-off-by: Herakliusz Lipiec <herakliusz.lipiec@intel.com>
  ---
  drivers/net/ixgbe/ixgbe_ethdev.h         |  4 ++--
  drivers/net/ixgbe/ixgbe_rxtx.c           | 10 +++++-----
  drivers/net/ixgbe/ixgbe_vf_representor.c |  2 +-
  lib/librte_ethdev/rte_ethdev.h           |  2 +-
  lib/librte_ethdev/rte_ethdev_core.h      |  2 +-
  5 files changed, 10 insertions(+), 10 deletions(-)

  diff --git a/drivers/net/ixgbe/ixgbe_ethdev.h b/drivers/net/ixgbe/ixgbe_ethdev.h
  index e1cd8fd16..f5fce74fc 100644
  --- a/drivers/net/ixgbe/ixgbe_ethdev.h
  +++ b/drivers/net/ixgbe/ixgbe_ethdev.h
  @@ -642,10 +642,10 @@ uint16_t ixgbe_recv_pkts_lro_bulk_alloc(void *rx_queue,
      struct rte_mbuf **rx_pkts, uint16_t nb_pkts);

  uint16_t ixgbe_xmit_pkts(void *tx_queue, struct rte_mbuf **tx_pkts,
  -		uint16_t nb_pkts);
  +		uint16_t nb_pkts, uint32_t dummy);

  uint16_t ixgbe_xmit_pkts_simple(void *tx_queue, struct rte_mbuf **tx_pkts,
  -		uint16_t nb_pkts);
  +		uint16_t nb_pkts, uint32_t dummy);

  uint16_t ixgbe_prep_pkts(void *tx_queue, struct rte_mbuf **tx_pkts,
      uint16_t nb_pkts);
  diff --git a/drivers/net/ixgbe/ixgbe_rxtx.c b/drivers/net/ixgbe/ixgbe_rxtx.c
  index 7b398f1a1..198be146a 100644
  --- a/drivers/net/ixgbe/ixgbe_rxtx.c
  +++ b/drivers/net/ixgbe/ixgbe_rxtx.c
  @@ -315,10 +315,10 @@ tx_xmit_pkts(void *tx_queue, struct rte_mbuf **tx_pkts,

  uint16_t
  ixgbe_xmit_pkts_simple(void *tx_queue, struct rte_mbuf **tx_pkts,
  -		       uint16_t nb_pkts)
  +		       uint16_t nb_pkts, uint32_t dummy)
  {
    uint16_t nb_tx;
  -
  +	dummy += 1;
    /* Try to transmit at least chunks of TX_MAX_BURST pkts */
    if (likely(nb_pkts <= RTE_PMD_IXGBE_TX_MAX_BURST))
      return tx_xmit_pkts(tx_queue, tx_pkts, nb_pkts);
  @@ -341,7 +341,7 @@ ixgbe_xmit_pkts_simple(void *tx_queue, struct rte_mbuf **tx_pkts,

  static uint16_t
  ixgbe_xmit_pkts_vec(void *tx_queue, struct rte_mbuf **tx_pkts,
  -		    uint16_t nb_pkts)
  +		    uint16_t nb_pkts, __rte_unused uint32_t dummy)
  {
    uint16_t nb_tx = 0;
    struct ixgbe_tx_queue *txq = (struct ixgbe_tx_queue *)tx_queue;
  @@ -622,7 +622,7 @@ ixgbe_xmit_cleanup(struct ixgbe_tx_queue *txq)

  uint16_t
  ixgbe_xmit_pkts(void *tx_queue, struct rte_mbuf **tx_pkts,
  -		uint16_t nb_pkts)
  +		uint16_t nb_pkts, uint32_t dummy)
  {
    struct ixgbe_tx_queue *txq;
    struct ixgbe_tx_entry *sw_ring;
  @@ -648,7 +648,7 @@ ixgbe_xmit_pkts(void *tx_queue, struct rte_mbuf **tx_pkts,
  #ifdef RTE_LIBRTE_SECURITY
    uint8_t use_ipsec;
  #endif
  -
  +	dummy += 1;
    tx_offload.data[0] = 0;
    tx_offload.data[1] = 0;
    txq = tx_queue;
  diff --git a/drivers/net/ixgbe/ixgbe_vf_representor.c b/drivers/net/ixgbe/ixgbe_vf_representor.c
  index dbbef294a..47b41992d 100644
  --- a/drivers/net/ixgbe/ixgbe_vf_representor.c
  +++ b/drivers/net/ixgbe/ixgbe_vf_representor.c
  @@ -164,7 +164,7 @@ ixgbe_vf_representor_rx_burst(__rte_unused void *rx_queue,

  static uint16_t
  ixgbe_vf_representor_tx_burst(__rte_unused void *tx_queue,
  -	__rte_unused struct rte_mbuf **tx_pkts, __rte_unused uint16_t nb_pkts)
  +	__rte_unused struct rte_mbuf **tx_pkts, __rte_unused uint16_t nb_pkts, __rte_unused uint32_t dummy)
  {
    return 0;
  }
  diff --git a/lib/librte_ethdev/rte_ethdev.h b/lib/librte_ethdev/rte_ethdev.h
  index d1a593ad1..ba6c36155 100644
  --- a/lib/librte_ethdev/rte_ethdev.h
  +++ b/lib/librte_ethdev/rte_ethdev.h
  @@ -4663,7 +4663,7 @@ rte_eth_tx_burst(uint16_t port_id, uint16_t queue_id,
    }
  #endif

  -	return (*dev->tx_pkt_burst)(dev->data->tx_queues[queue_id], tx_pkts, nb_pkts);
  +	return (*dev->tx_pkt_burst)(dev->data->tx_queues[queue_id], tx_pkts, nb_pkts, 5);
  }

  /**
  diff --git a/lib/librte_ethdev/rte_ethdev_core.h b/lib/librte_ethdev/rte_ethdev_core.h
  index 7bf97e24e..8a173574c 100644
  --- a/lib/librte_ethdev/rte_ethdev_core.h
  +++ b/lib/librte_ethdev/rte_ethdev_core.h
  @@ -344,7 +344,7 @@ typedef uint16_t (*eth_rx_burst_t)(void *rxq,

  typedef uint16_t (*eth_tx_burst_t)(void *txq,
            struct rte_mbuf **tx_pkts,
  -				   uint16_t nb_pkts);
  +				   uint16_t nb_pkts, uint32_t dummy);
  /**< @internal Send output packets on a transmit queue of an Ethernet device. */

  typedef uint16_t (*eth_tx_prep_t)(void *txq,
  --
  2.17.2


Apply negative patch to rte_eth_dev structure and ixgbe pmd driver,
inject 4 bytes in tx_burst.
::

  git apply 0001-rte_tx_burst_t_add-one-argument-at-the-end.patch

Build shared libraries, (just enable i40e pmd for testing)::

  meson configure -Ddisable_drivers=net/af_packet,net/ark,net/atlantic,net/avp,net/axgbe,net/bond,net/bnx2x,net/bnxt,net/cxgbe,net/dpaa,net/dpaa2,net/e1000,net/ena,net/enetc,net/enic,net/hinic,net/hns3,net/iavf,net/ice,net/kni,net/liquidio,net/memif,net/netvsc,net/nfp,net/null,net/octeontx,net/octeontx2,net/pcap,net/pfe,net/qede,net/sfc,net/softnic,net/tap,net/thunderx,net/vdev_netvsc,net/vhost,net/virtio,net/vmxnet3,common/cpt,common/dpaax,common/iavf,common/octeontx2,bus/dpaa,bus/fslmc,bus/ifpga,bus/vmbus,mempool/bucket,mempool/dpaa,mempool/dpaa2,mempool/octeontx2,mempool/stack,raw/dpaa2_cmdif,raw/dpaa2_qdma,raw/ioat,raw/ntb,raw/octeontx2_dma,raw/octeontx2_ep,raw/skeleton,crypto/caam_jr,crypto/ccp,crypto/dpaa_sec,crypto/dpaa2_sec,crypto/nitrox,crypto/null_crypto,crypto/octeontx_crypto,crypto/octeontx2_crypto,crypto/openssl,crypto/crypto_scheduler,crypto/virtio_crypto,vdpa/ifc,event/dpaa,event/dpaa2,event/octeontx2,event/opdl,event/skeleton,event/sw,event/dsw,event/octeontx,baseband/null,baseband/turbo_sw,baseband/fpga_lte_fec,net/failsafe
  meson  --werror -Dexamples=all --buildtype=debugoptimized --default-library=shared ./devtools/.. ./build-gcc-shared
  ninja -C ./build-gcc-shared

Run testpmd application refer to Common Test steps with ixgbe pmd NIC.::

  ./<build_target>/app/dpdk-testpmd -c 0xf -n 4 -d <dpdk_2002> -a 18:00.0 -- -i

Test txonly::

  set fwd txonly
  start

Expect there is no error happended
