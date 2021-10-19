# Copyright (c) <2020> Intel Corporation
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# - Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# - Neither the name of Intel Corporation nor the names of its
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.


import time

import tests.rte_flow_common as rfc
from framework.test_case import TestCase, check_supported_nic, skip_unsupported_pkg

from .flexible_common import FlexibleRxdBase


class TestFlexibleRxd(TestCase, FlexibleRxdBase):
    supported_nic = ['columbiaville_100g', 'columbiaville_25g', 'columbiaville_25gx2', 'foxville']

    def preset_compilation(self):
        """
        Modify the dpdk code.
        """
        cmds = [
            "cd " + self.dut.base_dir,
            "cp ./app/test-pmd/util.c .",
            r"""sed -i "/if dpdk_conf.has('RTE_NET_IXGBE')/i\if dpdk_conf.has('RTE_NET_ICE')\n\tdeps += 'net_ice'\nendif" app/test-pmd/meson.build""",
            "sed -i '/#include <rte_flow.h>/a\#include <rte_pmd_ice.h>' app/test-pmd/util.c",
            "sed -i '/if (is_timestamp_enabled(mb))/i\                rte_net_ice_dump_proto_xtr_metadata(mb);' app/test-pmd/util.c",
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
            "sed -i '/pmd_ice/d' app/test-pmd/meson.build",
            "rm -rf  ./util.c",
        ]
        [self.dut.send_expect(cmd, "#", 15, alt_session=True) for cmd in cmds]
        self.dut.build_install_dpdk(self.dut.target)

    @check_supported_nic(supported_nic)
    def set_up_all(self):
        """
        run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("1S/3C/1T", socket=self.ports_socket)
        self.verify(len(self.cores) >= 3, "Insufficient cpu cores for testing")
        self.preset_compilation()
        self.pci = self.dut.ports_info[0]['pci']
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.init_base(self.pci, self.dst_mac, 'pf')

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.restore_compilation()

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

    @skip_unsupported_pkg('os default')
    def test_check_single_VLAN_fields_in_RXD_8021Q(self):
        """
        Check single VLAN fields in RXD (802.1Q)
        """
        self.check_single_VLAN_fields_in_RXD_8021Q()

    @skip_unsupported_pkg('os default')
    def test_check_double_VLAN_fields_in_RXD_8021Q_1_VLAN_tag(self):
        """
        Check double VLAN fields in RXD (802.1Q) only 1 VLAN tag
        """
        self.check_double_VLAN_fields_in_RXD_8021Q_1_VLAN_tag()

    @skip_unsupported_pkg('os default')
    def test_check_double_VLAN_fields_in_RXD_8021Q_2_VLAN_tag(self):
        """
        Check double VLAN fields in RXD (802.1Q) 2 VLAN tags
        """
        self.check_double_VLAN_fields_in_RXD_8021Q_2_VLAN_tag()

    @skip_unsupported_pkg('os default')
    def test_check_double_VLAN_fields_in_RXD_8021ad(self):
        """
        Check double VLAN fields in RXD (802.1ad)
        """
        self.check_double_VLAN_fields_in_RXD_8021ad()

    @skip_unsupported_pkg('os default')
    def test_check_IPv4_fields_in_RXD(self):
        """
        Check IPv4 fields in RXD
        """
        self.check_IPv4_fields_in_RXD()

    @skip_unsupported_pkg('os default')
    def test_check_IPv6_fields_in_RXD(self):
        """
        Check IPv6 fields in RXD
        """
        self.check_IPv6_fields_in_RXD()

    @skip_unsupported_pkg('os default')
    def test_check_IPv6_flow_field_in_RXD(self):
        """
        Check IPv6 flow field in RXD
        """
        self.check_IPv6_flow_field_in_RXD()

    @skip_unsupported_pkg('os default')
    def test_check_TCP_fields_in_IPv4_in_RXD(self):
        """
        Check TCP fields in IPv4 in RXD
        """
        self.check_TCP_fields_in_IPv4_in_RXD()

    @skip_unsupported_pkg('os default')
    def test_check_TCP_fields_in_IPv6_in_RXD(self):
        """
        Check TCP fields in IPv6 in RXD
        """
        self.check_TCP_fields_in_IPv6_in_RXD()

    @skip_unsupported_pkg('os default')
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

    def test_check_effect_replace_pkg_RXID_22_to_RXID_16(self):
        """
        Check replace pkg RXID #22 to RXID #16 effect of testpmd
        """
        self.check_effect_replace_pkg_RXID_22_to_RXID_16()