.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

===================
Unit Tests: Mempool
===================

This is the test plan for the Intel® DPDK mempool library.

Description
===========

#. Basic tests: done on one core with and without cache:

   - Get one object, put one object
   - Get two objects, put two objects
   - Get all objects, test that their content is not modified and
     put them back in the pool.

#. Performance tests:

   Each core get *n_keep* objects per bulk of *n_get_bulk*. Then,
   objects are put back in the pool per bulk of *n_put_bulk*.

   This sequence is done during TIME_S seconds.

   This test is done on the following configurations:

   - Cores configuration (*cores*)

     - One core with cache
     - Two cores with cache
     - Max. cores with cache
     - One core without cache
     - Two cores without cache
     - Max. cores without cache

   - Bulk size (*n_get_bulk*, *n_put_bulk*)

     - Bulk get from 1 to 32
     - Bulk put from 1 to 32

   - Number of kept objects (*n_keep*)

     - 32
     - 128
