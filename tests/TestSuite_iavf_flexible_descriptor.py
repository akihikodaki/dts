# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
#

import time
import traceback

from framework.test_case import TestCase, check_supported_nic, skip_unsupported_pkg

from .flexible_common import FlexibleRxdBase


class TestIavfFlexibleDescriptor(TestCase, FlexibleRxdBase):
    supported_nic = [
        "ICE_100G-E810C_QSFP",
        "ICE_25G-E810C_SFP",
        "ICE_25G-E810_XXV_SFP",
        "IGC-I225_LM",
    ]

    def preset_compilation(self):
        """
        Modify the dpdk code.
        """
        cmds = [
            "cd " + self.dut.base_dir,
            "cp ./app/test-pmd/util.c .",
            r"""sed -i "/if dpdk_conf.has('RTE_NET_IXGBE')/i\if dpdk_conf.has('RTE_NET_ICE')\n\tdeps += ['net_ice', 'net_iavf']\nendif" app/test-pmd/meson.build""",
            "sed -i '/#include <rte_flow.h>/a\#include <rte_pmd_iavf.h>' app/test-pmd/util.c",
            "sed -i '/if (ol_flags & PKT_RX_RSS_HASH)/i\                rte_pmd_ifd_dump_proto_xtr_metadata(mb);' app/test-pmd/util.c",
        ]
        [self.dut.send_expect(cmd, "#", 15, alt_session=True) for cmd in cmds]
        self.dut.build_install_dpdk(self.dut.target)

    def restore_compilation(self):
        """
        Resume editing operation.
        """
        cmds = [
            "cd " + self.dut.base_dir,
            "cp ./util.c ./app/test-pmd/",
            "sed -i '/pmd_iavf/d' app/test-pmd/meson.build",
            "rm -rf  ./util.c",
        ]
        [self.dut.send_expect(cmd, "#", 15, alt_session=True) for cmd in cmds]
        self.dut.build_install_dpdk(self.dut.target)

    def create_vf(self):
        # vf relevant content
        dut_index = 0
        used_dut_port = self.dut_ports[dut_index]
        self.dut.send_expect("modprobe vfio-pci", "#")
        # bind pf to kernel
        for port in self.dut_ports:
            netdev = self.dut.ports_info[port]["port"]
            netdev.bind_driver(driver=self.kdriver)
        # set vf assign method and vf driver
        vf_driver = "vfio-pci"
        self.pf0_intf = self.dut.ports_info[self.dut_ports[dut_index]]["intf"]
        # get priv-flags default stats
        if self.is_eth_series_nic(800):
            self.flag = "vf-vlan-pruning"
        else:
            self.flag = "vf-vlan-prune-disable"
        self.default_stats = self.dut.get_priv_flags_state(self.pf0_intf, self.flag)
        if self.is_eth_series_nic(800) and self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s off" % (self.pf0_intf, self.flag), "# "
            )
        else:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s on" % (self.pf0_intf, self.flag), "# "
            )
        # generate 2 VFs on PF
        self.dut.generate_sriov_vfs_by_port(used_dut_port, 1, driver=self.kdriver)
        vf_mac = "00:11:22:33:44:55"
        self.dut.send_expect(
            "ip link set {} vf 0 mac {}".format(self.pf0_intf, vf_mac), "#"
        )
        sriov_vf0 = self.dut.ports_info[used_dut_port]["vfs_port"][0]
        sriov_vf0.bind_driver(vf_driver)
        return sriov_vf0, vf_mac

    def destroy_vf(self):
        try:
            port_id = 0
            self.dut.destroy_sriov_vfs_by_port(port_id)
            port_obj = self.dut.ports_info[port_id]["port"]
            port_obj.bind_driver(self.drivername)
        except Exception as e:
            self.logger.info(traceback.format_exc())

    @check_supported_nic(supported_nic)
    def set_up_all(self):
        """
        run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.preset_compilation()
        self.sriov_vf0, vf_mac = self.create_vf()
        self.init_base(self.sriov_vf0.pci, vf_mac, "iavf")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.destroy_vf()
        self.restore_compilation()
        if self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s %s"
                % (self.pf0_intf, self.flag, self.default_stats),
                "# ",
            )

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def tear_down(self):
        """
        Run after each test case.
        """
        self.close_testpmd()
        time.sleep(2)
        self.dut.kill_all()

    @skip_unsupported_pkg("os default")
    def test_check_single_VLAN_fields_in_RXD_8021Q(self):
        """
        Check single VLAN fields in RXD (802.1Q)
        """
        self.check_single_VLAN_fields_in_RXD_8021Q()

    @skip_unsupported_pkg("os default")
    def test_check_single_VLAN_fields_in_RXD_8021ad(self):
        """
        Check single VLAN fields in RXD (802.1ad)
        """
        self.check_single_VLAN_fields_in_RXD_8021ad()

    @skip_unsupported_pkg("os default")
    def test_check_double_VLAN_fields_in_RXD_8021Q_1_VLAN_tag(self):
        """
        Check double VLAN fields in RXD (802.1Q) only 1 VLAN tag
        """
        self.check_double_VLAN_fields_in_RXD_8021Q_1_VLAN_tag()

    @skip_unsupported_pkg("os default")
    def test_check_double_VLAN_fields_in_RXD_8021Q_2_VLAN_tag(self):
        """
        Check double VLAN fields in RXD (802.1Q) 2 VLAN tags
        """
        self.check_double_VLAN_fields_in_RXD_8021Q_2_VLAN_tag()

    @skip_unsupported_pkg("os default")
    def test_check_double_VLAN_fields_in_RXD_8021ad(self):
        """
        Check double VLAN fields in RXD (802.1ad)
        """
        self.check_double_VLAN_fields_in_RXD_8021ad()

    @skip_unsupported_pkg("os default")
    def test_check_IPv4_fields_in_RXD(self):
        """
        Check IPv4 fields in RXD
        """
        self.check_IPv4_fields_in_RXD()

    @skip_unsupported_pkg("os default")
    def test_check_IPv6_fields_in_RXD(self):
        """
        Check IPv6 fields in RXD
        """
        self.check_IPv6_fields_in_RXD()

    @skip_unsupported_pkg("os default")
    def test_check_IPv6_flow_field_in_RXD(self):
        """
        Check IPv6 flow field in RXD
        """
        self.check_IPv6_flow_field_in_RXD()

    @skip_unsupported_pkg("os default")
    def test_check_TCP_fields_in_IPv4_in_RXD(self):
        """
        Check TCP fields in IPv4 in RXD
        """
        self.check_TCP_fields_in_IPv4_in_RXD()

    @skip_unsupported_pkg("os default")
    def test_check_TCP_fields_in_IPv6_in_RXD(self):
        """
        Check TCP fields in IPv6 in RXD
        """
        self.check_TCP_fields_in_IPv6_in_RXD()

    @skip_unsupported_pkg("os default")
    def test_check_IPv4_IPv6_TCP_fields_in_RXD_on_specific_queues(self):
        """
        Check IPv4, IPv6, TCP fields in RXD on specific queues
        """
        self.check_IPv4_IPv6_TCP_fields_in_RXD_on_specific_queues()

    def test_check_testpmd_use_different_parameters(self):
        """
        Check testpmd use different parameters start
        """
        self.check_testpmd_use_different_parameters()

    def test_check_ip_offset_of_ip(self):
        """
        Check ip offset of ip
        """
        self.check_ip_offset_of_ip()

    def test_check_ip_offset_with_vlan(self):
        """
        check ip offset with vlan
        """
        self.check_ip_offset_with_vlan()

    def test_check_ip_offset_with_2_vlan_tag(self):
        """
        check offset with 2 vlan tag
        """
        self.check_ip_offset_with_2_vlan_tag()

    def test_check_ip_offset_with_multi_MPLS(self):
        """
        check ip offset with multi MPLS
        """
        self.check_ip_offset_with_multi_MPLS()

    def test_check_ip_offset_with_multi_MPLS_with_vlan_tag(self):
        """
        check ip offset with multi MPLS with vlan tag
        """
        self.check_ip_offset_with_multi_MPLS_with_vlan_tag()

    def test_check_ip_offset_with_multi_MPLS_with_2_vlan_tag(self):
        """
        check ip offset with multi MPLS with 2 vlan tag
        """
        self.check_ip_offset_with_multi_MPLS_with_2_vlan_tag()
