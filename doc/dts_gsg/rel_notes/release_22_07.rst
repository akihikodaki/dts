.. SPDX-License-Identifier: BSD-3-Clause
   Copyright 2022 The DTS contributors

DTS Release 22.07
=================

New Features
------------

* **Add new test plans.**

  * af_xdp_test_plan.rst
  * iavf_fdir_protocol_agnostic_flow_test_plan.rst
  * iavf_rss_protocol_agnostic_flow_test_plan.rst
  * ice_fdir_protocol_agnostic_flow_test_plan.rst
  * ice_rss_protocol_agnostic_flow_test_plan.rst
  * ice_iavf_packet_pacing_test_plan.rst
  * ice_iavf_rx_timestamp_test_plan.rst
  * ice_rx_timestamp_test_plan.rst
  * rx_timestamp_perf_test_plan.rst
  * power_pmd_test_plan.rst
  * power_throughput_test_plan.rst
  * ice_enable_basic_hqos_on_pf_test_plan.rst
  * vhost_virtio_user_interrupt_with_power_monitor_test_plan.rst
  * vm2vm_virtio_net_perf_dsa_test_plan.rst
  * vm2vm_virtio_pmd_dsa_test_plan.rst

* **Add new test suites.**

  * TestSuite_af_xdp.py
  * TestSuite_iavf_fdir_protocol_agnostic_flow.py
  * TestSuite_iavf_rss_protocol_agnostic_flow.py
  * TestSuite_ice_fdir_protocol_agnostic_flow.py
  * TestSuite_ice_rss_protocol_agnostic_flow.py
  * TestSuite_ice_iavf_packet_pacing.py
  * TestSuite_ice_iavf_rx_timestamp.py
  * TestSuite_ice_rx_timestamp.py
  * TestSuite_rx_timestamp_perf.py
  * TestSuite_power_pmd.py
  * TestSuite_power_throughput.py
  * TestSuite_vhost_virtio_user_interrupt_with_power_monitor.py


Removed Items
-------------

* **Remove test plans.**

  * af_xdp_2_test_plan.rst
  * power_managerment_throughput_test_plan.rst
  * rteflow_priority_test_plan.rst
  * vhost_event_idx_interrupt_cbdma_test_plan.rst
  * vhost_user_interrupt_cbdma_test_plan.rst
  * vm2vm_virtio_net_dsa_test_plan.rst

* **Remove test suites.**

  * TestSuite_af_xdp_2.py
  * TestSuite_rteflow_priority.py
  * TestSuite_vhost_event_idx_interrupt_cbdma.py
  * TestSuite_vhost_user_interrupt_cbdma.py


Deprecation Notices
-------------------

**Unit Testing**

DPDK provide 2 ways to run unit test, one is `dpdk-test` app, the other is `meson test` command.
Support for running unit tests through `dpdk-test` app is now deprecated and will be removed in the next release.
Instead `meson test` command will be executed.
