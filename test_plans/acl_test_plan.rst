.. Copyright (c) <2021>, Intel Corporation
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
