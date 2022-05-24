.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

=================
ACL Test Plan
=================

Overview
---------
This document contains the test plan for DPDK ACL library via ``test-acl``
application.


Ref links:
https://doc.dpdk.org/guides/prog_guide/packet_classif_access_ctrl.html


Prerequisites
=============

1. Machine with AVX-512 ISA is required to test avx-512 speciific methods.
2. test-acl rules and traces input files: ``deps/test-acl-input.tar.gz``
3. ``test-acl.sh`` shell script provided with DPDK.


Test Case: scalar method
========================

1. Unpack deps/test-acl-input.tar.gz into temporary directory:

.. code-block:: console

   gzip -cd deps/test-acl-input.tar.gz | tar xfv -

2. Launch the "run_tes.sh" script several times as follows:

.. code-block:: console

   for i in 15 16 17 18 23 24 25 31 32 33 34 35 47 48 51 255 256 257; do \
      /bin/bash ${DPDK}/app/test-acl/test-acl.sh \
      ${DPDK}/<build>/app/dpdk-test-acl test-acl-input scalar ${i}; \
      done 2>&1 | tee test-acl.out

3. Remove temporary directory ``test-acl-input``:

.. code-block:: console

   rm -rf test-acl-input

Pass criteria: no "``FAILED``" present in the output.

Test Case: sse method
=====================

1. Unpack deps/test-acl-input.tar.gz into temporary directory:

.. code-block:: console

   gzip -cd deps/test-acl-input.tar.gz | tar xfv -

2. Launch the "run_tes.sh" script several times as follows:

.. code-block:: console

   for i in 15 16 17 18 23 24 25 31 32 33 34 35 47 48 51 255 256 257; do \
      /bin/bash ${DPDK}/app/test-acl/test-acl.sh \
      ${DPDK}/<build>/app/dpdk-test-acl test-acl-input sse ${i}; \
      done 2>&1 | tee test-acl.out

3. Remove temporary directory ``test-acl-input``:

.. code-block:: console

   rm -rf test-acl-input

Pass criteria: no "``FAILED``" present in the output.

Test Case: avx2 method
======================

1. Unpack deps/test-acl-input.tar.gz into temporary directory:

.. code-block:: console

   gzip -cd deps/test-acl-input.tar.gz | tar xfv -

2. Launch the "run_tes.sh" script several times as follows:

.. code-block:: console

   for i in 15 16 17 18 23 24 25 31 32 33 34 35 47 48 51 255 256 257; do \
      /bin/bash ${DPDK}/app/test-acl/test-acl.sh \
      ${DPDK}/<build>/app/dpdk-test-acl test-acl-input avx2 ${i}; \
      done 2>&1 | tee test-acl.out

3. Remove temporary directory ``test-acl-input``:

.. code-block:: console

   rm -rf test-acl-input

Pass criteria: no "``FAILED``" present in the output.

Test Case: avx512x16 method
===========================

1. Unpack deps/test-acl-input.tar.gz into temporary directory:

.. code-block:: console

   gzip -cd deps/test-acl-input.tar.gz | tar xfv -

2. Launch the "run_tes.sh" script several times as follows:

.. code-block:: console

   for i in 15 16 17 18 23 24 25 31 32 33 34 35 47 48 51 255 256 257; do \
      /bin/bash ${DPDK}/app/test-acl/test-acl.sh \
      ${DPDK}/<build>/app/dpdk-test-acl test-acl-input avx512x16 ${i}; \
      done 2>&1 | tee test-acl.out

3. Remove temporary directory ``test-acl-input``:

.. code-block:: console

   rm -rf test-acl-input

Pass criteria: no "``FAILED``" present in the output.

Test Case: avx512x32 method
===========================

1. Unpack deps/test-acl-input.tar.gz into temporary directory:

.. code-block:: console

   gzip -cd deps/test-acl-input.tar.gz | tar xfv -

2. Launch the "run_tes.sh" script several times as follows:

.. code-block:: console

   for i in 15 16 17 18 23 24 25 31 32 33 34 35 47 48 51 255 256 257; do \
      /bin/bash ${DPDK}/app/test-acl/test-acl.sh \
      ${DPDK}/<build>/app/dpdk-test-acl test-acl-input avx512x32 ${i}; \
      done 2>&1 | tee test-acl.out

3. Remove temporary directory ``test-acl-input``:

.. code-block:: console

   rm -rf test-acl-input

Pass criteria: no "``FAILED``" present in the output.
