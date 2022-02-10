.. SPDX-License-Identifier: BSD-3-Clause
   Copyright 2022 The DTS contributors

DTS Release 21.11
=================

New Features
------------

* **Add new test plans.**

  * cvl_1pps_signal_test_plan.rst
  * cvl_advanced_iavf_rss_pppol2tpoudp_test_plan.rst
  * cvl_flow_priority_test_plan.rst

* **Add new test suites.**

  * TestSuite_cvl_1pps_signal.py
  * TestSuite_cvl_advanced_iavf_rss_pppol2tpoudp.py
  * TestSuite_cvl_dcf_qos.py
  * TestSuite_cvl_flow_priority.py

* **Update test plans to adapt meson build.**

  Makefile builds are removed in DPDK 20.11, so update test plan accordingly.

* **Fix pylama errors.**

  Fix most pylama errors in framework.

* **Make DTS a python standard project.**

  Update DTS to a standard structure.


Removed Items
-------------

* **Remove test plans.**

  * fdir_test_plan.rst
  * fortville_rss_granularity_config_test_plan.rst
  * generic_filter_test_plan.rst
  * virtio_1.0_test_plan.rst

* **Remove test suites.**

  * TestSuite_fdir.py
  * TestSuite_fortville_rss_granularity_config.py
  * TestSuite_generic_filter.py


Deprecation Notices
-------------------

* Makefile builds are deprecated and will be removed in DTS 22.03,
  please use meson builds instead.
