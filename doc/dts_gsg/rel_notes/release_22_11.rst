.. SPDX-License-Identifier: BSD-3-Clause
   Copyright 2023 The DTS contributors

DTS Release 22.11
=================

Key Takeaway
------------

* **Unit Testing**

DPDK provide 2 ways to run unit test, one is `dpdk-test` app, the other is `meson test` command.
Support for running unit tests through `dpdk-test` app is removed.
`tests/TestSuite_meson_tests.py` is now used for unit testing.

* **New Features**

  * Support Docker Container.
  * Pin cpu cores to VM threads for better performance.
  * Testpmd command changed in port representor action.
  * Add test points to imporve testing coverage.

Added Items
-----------

* **Add new test plans.**

  * vhost_dsa_test_plan.rst
  * vhost_user_interrupt_cbdma_test_plan.rst
  * vhost_event_idx_interrupt_cbdma_test_plan.rst
  * ice_buffer_split_test_plan.rst
  * ice_header_split_perf_test_plan.rst
  * ice_dcf_disable_acl_filter_test_plan.rst
  * ice_iavf_flow_subscribe_test_plan.rst

* **Add new test suites.**

  * TestSuite_vhost_dsa.py
  * TestSuite_vhost_user_interrupt_cbdma.py
  * TestSuite_vhost_event_idx_interrupt_cbdma.py
  * TestSuite_basic_4k_pages_dsa.py
  * TestSuite_loopback_virtio_user_server_mode_dsa.py
  * TestSuite_vm2vm_virtio_net_perf_dsa.py
  * TestSuite_vm2vm_virtio_user_dsa.py
  * TestSuite_vm2vm_virtio_pmd_dsa.py
  * TestSuite_ice_buffer_split.py
  * TestSuite_ice_header_split_perf.py
  * TestSuite_ice_dcf_disable_acl_filter.py
  * TestSuite_ice_iavf_flow_subscribe.py
  * TestSuite_ice_enable_basic_hqos_on_pf.py

Removed Items
-------------

* **Remove test plans.**

  * vswitch_sample_dsa_test_plan.rst
  * pvp_vhost_dsa_test_plan.rst
  * kni_test_plan.rst
  * ice_1pps_signal_test_plan.rst
  * ice_qinq_test_plan.rst
  * flow_classify_softnic_test_plan.rst
  * metering_and_policing_test_plan.rst
  * unit_tests_*.rst

* **Remove test suites.**

  * TestSuite_kni.py
  * TestSuite_ice_1pps_signal.py
  * TestSuite_ice_qinq.py
  * TestSuite_flow_classify_softnic.py
  * TestSuite_metering_and_policing.py
  * TestSuite_unit_test_*.py
