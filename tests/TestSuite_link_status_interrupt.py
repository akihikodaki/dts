# BSD LICENSE
#
# Copyright(c) 2010-2017 Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""
DPDK Test suite.
Test link status.
"""

import re
import string
import time

import framework.utils as utils
from framework.packet import Packet
from framework.test_case import TestCase


class TestLinkStatusInterrupt(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        cores = self.dut.get_core_list("1S/4C/1T")
        self.coremask = utils.create_mask(cores)
        self.portmask = utils.create_mask(self.dut_ports)
        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.app_link_status_interrupt_path = self.dut.apps_name[
            "link_status_interrupt"
        ]

        # build sample app
        out = self.dut.build_dpdk_apps("./examples/link_status_interrupt")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")
        # from kernel 4.8+, kernel will not support legacy intr mode.
        # detailed info:https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git/commit/drivers/pci/quirks.c?id=8bcf4525c5d43306c5fd07e132bc8650e3491aec
        if self.nic in [
            "ICE_25G-E810C_SFP",
            "ICE_100G-E810C_QSFP",
            "I40E_10G-SFP_XL710",
            "I40E_40G-QSFP_A",
            "I40E_40G-QSFP_B",
            "I40E_25G-25G_SFP28",
            "I40E_10G-10G_BASE_T_BC",
        ]:
            self.basic_intr_mode = ["msix"]
        else:
            self.basic_intr_mode = ["msix", "legacy"]
        if self.drivername == "vfio-pci":
            self.basic_intr_mode.append("msi")
        self.intfs = [
            self.tester.get_interface(self.tester.get_local_port(i))
            for i in self.dut_ports
        ]
        # check link-down-on-close flag
        self.flag = "link-down-on-close"
        for intf in self.intfs:
            set_flag = "ethtool --set-priv-flags %s %s on" % (intf, self.flag)
            self.flag_default_stats = self.tester.get_priv_flags_state(intf, self.flag)
            if self.flag_default_stats == "off":
                self.tester.send_expect(set_flag, "# ")
                time.sleep(0.5)
                self.verify(
                    self.tester.get_priv_flags_state(intf, self.flag) == "on",
                    "set %s %s on failed" % (intf, self.flag),
                )

    def set_link_status_and_verify(self, dutPort, status):
        """
        set link status verify results
        """
        self.intf = self.tester.get_interface(self.tester.get_local_port(dutPort))
        if self.dut.get_os_type() != "freebsd" and self.flag_default_stats:
            self.tester.send_expect(
                "ethtool --set-priv-flags %s link-down-on-close on" % self.intf, "#", 10
            )
        self.tester.send_expect(
            "ifconfig %s %s" % (self.intf, status.lower()), "# ", 10
        )
        verify_point = "Port %s Link %s" % (dutPort, status.lower())
        out = self.dut.get_session_output(timeout=60)
        self.verify(verify_point in out, "link status update error")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_link_status_interrupt_change(self):
        """
        Verify Link status change
        """

        if self.drivername == "igb_uio":
            cmdline = self.app_link_status_interrupt_path + " %s -- -p %s " % (
                self.eal_para,
                self.portmask,
            )
            for mode in self.basic_intr_mode:
                self.dut.send_expect("rmmod -f igb_uio", "#", 20)
                self.dut.send_expect(
                    'insmod %s/kmod/igb_uio.ko "intr_mode=%s"' % (self.target, mode),
                    "# ",
                )
                self.dut.bind_interfaces_linux()
                self.dut.send_command(cmdline, 180)
                out = self.dut.get_session_output(timeout=60)
                self.verify("Port statistics" in out, "setup example error")
                time.sleep(10)
                self.set_link_status_and_verify(self.dut_ports[0], "Down")
                self.set_link_status_and_verify(self.dut_ports[0], "Up")
                self.dut.send_expect("^C", "#", 60)
        elif self.drivername == "vfio-pci":
            for mode in self.basic_intr_mode:
                cmdline = (
                    self.app_link_status_interrupt_path
                    + " %s --vfio-intr=%s -- -p %s"
                    % (self.eal_para, mode, self.portmask)
                )
                self.dut.send_expect(cmdline, "statistics", 120)
                self.set_link_status_and_verify(self.dut_ports[0], "Down")
                self.set_link_status_and_verify(self.dut_ports[0], "Up")
                self.dut.send_expect("^C", "#", 60)

    def test_link_status_interrupt_port_available(self):
        """
        interrupt all port link, then link them,
        sent packet, check packets received.
        """
        if self.drivername == "igb_uio":
            cmdline = self.app_link_status_interrupt_path + "%s -- -p %s " % (
                self.eal_para,
                self.portmask,
            )
            for mode in self.basic_intr_mode:
                self.dut.send_expect("rmmod -f igb_uio", "#", 20)
                self.dut.send_expect(
                    'insmod %s/kmod/igb_uio.ko "intr_mode=%s"' % (self.target, mode),
                    "# ",
                )
                self.dut.bind_interfaces_linux()
                self.dut.send_expect(cmdline, "Aggregate statistics", 60)
                for port in self.dut_ports:
                    self.set_link_status_and_verify(self.dut_ports[port], "Down")
                time.sleep(10)
                for port in self.dut_ports:
                    self.set_link_status_and_verify(self.dut_ports[port], "Up")
                self.scapy_send_packet(1)
                out = self.dut.get_session_output(timeout=60)
                pkt_send = re.findall("Total packets sent:\s*(\d*)", out)
                pkt_received = re.findall("Total packets received:\s*(\d*)", out)
                self.verify(
                    pkt_send[-1] == pkt_received[-1] == "1",
                    "Error: sent packets != received packets",
                )
                self.dut.send_expect("^C", "#", 60)
        elif self.drivername == "vfio-pci":
            for mode in self.basic_intr_mode:
                cmdline = (
                    self.app_link_status_interrupt_path
                    + " %s --vfio-intr=%s -- -p %s"
                    % (self.eal_para, mode, self.portmask)
                )
                self.dut.send_expect(cmdline, "Aggregate statistics", 60)
                for port in self.dut_ports:
                    self.set_link_status_and_verify(self.dut_ports[port], "Down")
                time.sleep(10)
                for port in self.dut_ports:
                    self.set_link_status_and_verify(self.dut_ports[port], "Up")
                self.scapy_send_packet(1)
                out = self.dut.get_session_output(timeout=60)
                pkt_send = re.findall("Total packets sent:\s*(\d*)", out)
                pkt_received = re.findall("Total packets received:\s*(\d*)", out)
                self.verify(
                    pkt_send[-1] == pkt_received[-1] == "1",
                    "Error: sent packets != received packets",
                )
                self.dut.send_expect("^C", "#", 60)

    def scapy_send_packet(self, num=1):
        """
        Send a packet to port
        """
        self.dmac = self.dut.get_mac_address(self.dut_ports[0])
        txport = self.tester.get_local_port(self.dut_ports[0])
        self.txItf = self.tester.get_interface(txport)
        pkt = Packet(pkt_type="UDP")
        pkt.config_layer("ether", {"dst": self.dmac})
        pkt.send_pkt(self.tester, tx_port=self.txItf, count=num)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        time.sleep(2)
        for port in self.dut_ports:
            intf = self.tester.get_interface(self.tester.get_local_port(port))
            self.tester.send_expect("ifconfig %s up" % intf, "# ", 10)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        if self.dut.get_os_type() != "freebsd" and self.flag_default_stats:
            for intf in self.intfs:
                self.tester.send_expect(
                    "ethtool --set-priv-flags %s %s %s"
                    % (intf, self.flag, self.flag_default_stats),
                    "# ",
                )
