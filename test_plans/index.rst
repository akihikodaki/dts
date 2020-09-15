..  BSD LICENSE
    Copyright(c) 2017 Intel Corporation. All rights reserved.
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:

    * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.
    * Neither the name of Intel Corporation nor the names of its
    contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The DPDK Test Plans
===================

The following are the test plans for the DPDK DTS automated test system.

.. toctree::
    :maxdepth: 1
    :numbered:

    ABI_stable_test_plan
    blacklist_test_plan
    checksum_offload_test_plan
    cloud_filter_test_plan
    coremask_test_plan
    cvl_advanced_rss_test_plan
    cvl_advanced_rss_gtpu_test_plan
    cvl_advanced_iavf_rss_test_plan
    cvl_advanced_rss_pppoe_vlan_esp_ah_l2tp_pfcp_test_plan
    cvl_dcf_date_path_test_plan
    cvl_dcf_dp_test_plan
    cvl_dcf_switch_filter_test_plan
    cvl_fdir_test_plan
    cvl_iavf_rss_gtpu_test_plan
    cvl_rss_configure_test_plan
    cvl_switch_filter_test_plan
    cloud_filter_with_l4_port_test_plan
    dcf_lifecycle_test_plan
    crypto_perf_cryptodev_perf_test_plan
    ddp_gtp_qregion_test_plan
    ddp_gtp_test_plan
    ddp_mpls_test_plan
    ddp_ppp_l2tp_test_plan
    ddp_l2tpv3_test_plan
    dual_vlan_test_plan
    dynamic_config_test_plan
    dynamic_flowtype_test_plan
    dynamic_queue_test_plan
    etag_test_plan
    external_memory_test_plan
    external_mempool_handler_test_plan
    fdir_test_plan
    firmware_version_test_plan
    floating_veb_test_plan
    flow_classify_softnic_test_plan
    fortville_rss_granularity_config_test_plan
    fortville_rss_input_test_plan
    ftag_test_plan
    generic_filter_test_plan
    generic_flow_api_test_plan
    hotplug_mp_test_plan
    hotplug_test_plan
    iavf_fdir_test_plan
    iavf_package_driver_error_handle_test_plan
    ieee1588_test_plan
    inline_ipsec_test_plan
    interrupt_pmd_test_plan
    ip_pipeline_test_plan
    ipfrag_test_plan
    ipgre_test_plan
    ipsec_gw_cryptodev_func_test_plan
    ipv4_reassembly_test_plan
    ixgbe_vf_get_extra_queue_information_test_plan
    jumboframes_test_plan
    kni_test_plan
    l2fwd_cryptodev_func_test_plan
    l2fwd_test_plan
    l2tp_esp_coverage_test_plan
    l3fwd_em_test_plan
    l3fwd_test_plan
    l3fwdacl_test_plan
    link_flowctrl_test_plan
    link_status_interrupt_test_plan
    linux_modules_test_plan
    loopback_multi_paths_port_restart_test_plan
    loopback_virtio_user_server_mode_test_plan
    mac_filter_test_plan
    macsec_for_ixgbe_test_plan
    metering_and_policing_test_plan
    mtu_update_test_plan
    multiple_pthread_test_plan
    NICStatistics_test_plan
    ntb_test_plan
    nvgre_test_plan
    perf_virtio_user_loopback_test_plan
    perf_virtio_user_pvp_test_plan
    perf_vm2vm_virtio_net_perf_test_plan
    pvp_virtio_user_multi_queues_port_restart_test_plan
    pmd_bonded_8023ad_test_plan
    pmd_bonded_test_plan
    pmd_stacked_bonded_test_plan
    pmd_test_plan
    pmdpcap_test_plan
    pmdrss_hash_test_plan
    pmdrssreta_test_plan
    ptype_mapping_test_plan
    pvp_multi_paths_performance_test_plan
    pvp_multi_paths_vhost_single_core_performance_test_plan
    pvp_multi_paths_virtio_single_core_performance_test_plan
    qinq_filter_test_plan
    qos_api_test_plan
    qos_meter_test_plan
    qos_sched_test_plan
    queue_region_test_plan
    queue_start_stop_test_plan
    rss_to_rte_flow_test_plan
    rss_key_update_test_plan
    rxtx_offload_test_plan
    rteflow_priority_test_plan
    runtime_vf_queue_number_kernel_test_plan
    runtime_vf_queue_number_maxinum_test_plan
    runtime_vf_queue_number_test_plan
    rxtx_offload_test_plan
    scatter_test_plan
    short_live_test_plan
    shutdown_api_test_plan
    speed_capabilities_test_plan
    sw_hw_thash_consistence_test_plan
    vhost_cbdma_test_plan
    vhost_user_interrupt_test_plan
    sriov_kvm_test_plan
    stability_test_plan
    stats_checks_test_plan
    eventdev_pipeline_test_plan
    tso_test_plan
    tx_preparation_test_plan
    uni_pkt_test_plan
    userspace_ethtool_test_plan
    vlan_ethertype_config_test_plan
    vlan_test_plan
    vxlan_test_plan
    af_xdp_test_plan
    l2fwd_jobstats_test_plan
    loadbalancer_test_plan
    loopback_multi_queues_test_plan
    telemetry_test_plan
    compressdev_isal_pmd_test_plan
    compressdev_qat_pmd_test_plan
    compressdev_zlib_pmd_test_plan
    enable_package_download_in_ice_driver_test_plan
    multicast_test_plan
    ethtool_stats_test_plan
    metrics_test_plan.rst

    veb_switch_test_plan
    vf_daemon_test_plan
    vf_interrupt_pmd_test_plan
    vf_jumboframe_test_plan
    vf_kernel_test_plan
    vf_macfilter_test_plan
    vf_offload_test_plan
    vf_packet_rxtx_test_plan
    vf_pf_reset_test_plan
    vf_port_start_stop_test_plan
    vf_rss_test_plan
    vf_to_vf_nic_bridge_test_plan
    vf_vlan_test_plan
    kernelpf_iavf_test_plan
    vhost_multi_queue_qemu_test_plan
    vhost_qemu_mtu_test_plan
    vhost_user_live_migration_test_plan
    vhost_pmd_xstats_test_plan
    vm_power_manager_test_plan
    vm_pw_mgmt_policy_test_plan
    power_bidirection_channel_test_plan
    power_branch_ratio_test_plan
    power_empty_poll_test_plan
    power_pbf_test_plan
    power_pstate_test_plan
    power_telemetry_test_plan
    vmdq_test_plan
    vf_l3fwd_test_plan
    softnic_test_plan
    vm_hotplug_test_plan
    mdd_test_plan
    malicious_driver_event_indication_test_plan

    virtio_1.0_test_plan
    vhost_event_idx_interrupt_test_plan
    vhost_virtio_pmd_interrupt_test_plan
    vhost_virtio_user_interrupt_test_plan
    virtio_event_idx_interrupt_test_plan
    virtio_ipsec_cryptodev_func_test_plan
    virtio_perf_cryptodev_func_test_plan
    vm2vm_virtio_net_perf_test_plan
    vm2vm_virtio_pmd_test_plan
    dpdk_gro_lib_test_plan
    dpdk_gso_lib_test_plan
    vhost_dequeue_zero_copy_test_plan
    vxlan_gpe_support_in_i40e_test_plan
    pvp_diff_qemu_version_test_plan
    pvp_share_lib_test_plan
    pvp_vhost_user_built_in_net_driver_test_plan
    pvp_virtio_user_2M_hugepages_test_plan
    virtio_unit_cryptodev_func_test_plan
    virtio_user_for_container_networking_test_plan
    eventdev_perf_test_plan
    eventdev_pipeline_perf_test_plan
    pvp_qemu_multi_paths_port_restart_test_plan
    pvp_vhost_user_reconnect_test_plan
    pvp_virtio_bonding_test_plan
    pvp_virtio_user_4k_pages_test_plan
    vdev_primary_secondary_test_plan
    vhost_1024_ethports_test_plan
    virtio_pvp_regression_test_plan
    virtio_user_as_exceptional_path_test_plan

    unit_tests_cmdline_test_plan
    unit_tests_crc_test_plan
    unit_tests_cryptodev_func_test_plan
    unit_tests_dump_test_plan
    unit_tests_eal_test_plan
    unit_tests_event_timer_test_plan
    unit_tests_kni_test_plan
    unit_tests_loopback_test_plan
    unit_tests_lpm_test_plan
    unit_tests_mbuf_test_plan
    unit_tests_mempool_test_plan
    unit_tests_pmd_perf_test_plan
    unit_tests_power_test_plan
    unit_tests_qos_test_plan
    unit_tests_ringpmd_test_plan
    unit_tests_ring_test_plan
    unit_tests_timer_test_plan

    cmdline_test_plan
    hello_world_test_plan
    keep_alive_test_plan
    multiprocess_test_plan
    netmap_compat_test_plan
    rxtx_callbacks_test_plan
    skeleton_test_plan
    timer_test_plan
    vxlan_sample_test_plan
    ptpclient_test_plan
    distributor_test_plan
    efd_test_plan
    example_build_test_plan
    flow_classify_test_plan
    dpdk_hugetlbfs_mount_size_test_plan
    nic_single_core_perf_test_plan
    power_managerment_throughput_test_plan
    iavf_test_plan
    packet_capture_test_plan
    packet_ordering_test_plan
    bbdev_test_plan
    performance_thread_test_plan

    fips_cryptodev_test_plan
    flow_filtering_test_plan
    af_xdp_2_test_plan
    cbdma_test_plan
    flexible_rxd_test_plan
    ipsec_gw_and_library_test_plan
    port_control_test_plan
    port_representor_test_plan
    vm2vm_virtio_user_test_plan
    vmdq_dcb_test_plan
