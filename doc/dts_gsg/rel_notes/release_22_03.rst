.. SPDX-License-Identifier: BSD-3-Clause
   Copyright 2022 The DTS contributors

DTS Release 22.03
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

**Removed Makefile Builds.**

Support for makefile builds has been removed.


Deprecation Notices
-------------------

**Unit Testing**

DPDK provide 2 ways to run unit test, one is `dpdk-test` app, the other is `meson test` command.
Support for running unit tests through `dpdk-test` app is now deprecated and will be removed in the next release.
Instead `meson test` command will be executed.
