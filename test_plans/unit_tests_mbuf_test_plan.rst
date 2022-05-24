.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

================
Unit Tests: Mbuf
================

This is the test plan for the Intel® DPDK mbuf library.

Description
===========

#. Allocate a mbuf pool.

   - The pool contains NB_MBUF elements, where each mbuf is MBUF_SIZE
     bytes long.

#. Test multiple allocations of mbufs from this pool.

   - Allocate NB_MBUF and store pointers in a table.
   - If an allocation fails, return an error.
   - Free all these mbufs.
   - Repeat the same test to check that mbufs were freed correctly.

#. Test data manipulation in pktmbuf.

   - Alloc an mbuf.
   - Append data using rte_pktmbuf_append().
   - Test for error in rte_pktmbuf_append() when len is too large.
   - Trim data at the end of mbuf using rte_pktmbuf_trim().
   - Test for error in rte_pktmbuf_trim() when len is too large.
   - Prepend a header using rte_pktmbuf_prepend().
   - Test for error in rte_pktmbuf_prepend() when len is too large.
   - Remove data at the beginning of mbuf using rte_pktmbuf_adj().
   - Test for error in rte_pktmbuf_adj() when len is too large.
   - Check that appended data is not corrupt.
   - Free the mbuf.
   - Between all these tests, check data_len and pkt_len, and
     that the mbuf is contiguous.
   - Repeat the test to check that allocation operations
     reinitialize the mbuf correctly.
