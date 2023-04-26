.. SPDX-License-Identifier: BSD-3-Clause
   Copyright 2023 The DTS contributors

DTS Release 23.03
=================

.. **Read this first.**

   The text in the sections below explains how to update the release notes.

   Use proper spelling, capitalization and punctuation in all sections.


New Features
------------

.. This section should contain new features added in this release.

   Sample format:

   * **Add a title in the past tense with a full stop.**

     Add a short 1-2 sentence description in the past tense.
     The description should be enough to allow someone scanning
     the release notes to understand the new feature.

     If the feature adds a lot of sub-features you can use a bullet list
     like this:

     * Added feature foo to do something.
     * Enhanced feature bar to do something else.

     This section is a comment. Do not overwrite or remove it.
     Also, make sure to start the actual text at the margin.
     =======================================================

* **Add new test plan.**

  * pvp_vhost_async_multi_paths_performance_dsa_test_plan.rst
  * pvp_vhost_async_virtio_pmd_perf_dsa_test_plan.rst
  * loopback_vhost_async_perf_dsa_test_plan.rst
  * dsa_test_plan.rst
  * vswitch_sample_dsa_test_plan.rst
  * vhost_async_robust_cbdma_test_plan.rst

* **Add new test suites.**

  * TestSuite_pvp_vhost_async_multi_paths_performance_dsa.py
  * TestSuite_pvp_vhost_async_virtio_pmd_perf_dsa.py
  * TestSuite_loopback_vhost_async_perf_dsa_test_plan.py
  * TestSuite_dsa.py
  * TestSuite_vswitch_sample_dsa.py
  * TestSuite_vhost_async_robust_cbdma.py

* **Misc**

  * Refined bonding cases.
  * Refined offload cases.
  * Merged duplicated cases from execution file.
  * Supported new NICs IGB_1G-82576 and ConnectX6_MT2894

Removed Items
-------------

.. This section should contain removed items in this release.

   Sample format:

   * Add a short 1-2 sentence description of the removed item
     in the past tense.

   This section is a comment. Do not overwrite or remove it.
   Also, make sure to start the actual text at the margin.
   =======================================================

* **Remove test suites.**

  * TestSuite_power_empty_poll.py

Known Issues
------------

.. This section should contain new known issues in this release.

   Sample format:

   * Add a short 1-2 sentence description of the removed item
     in the past tense.

   This section is a comment. Do not overwrite or remove it.
   Also, make sure to start the actual text at the margin.
   =======================================================
