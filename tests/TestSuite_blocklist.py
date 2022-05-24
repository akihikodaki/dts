# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.
Test device blocklisting.
"""
import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.settings import DRIVERS
from framework.test_case import TestCase


class TestBlockList(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        Blocklist Prerequisites.
        Requirements:
            Two Ports
        """
        self.ports = self.dut.get_ports(self.nic)
        self.verify(len(self.ports) >= 2, "Insufficient ports for testing")
        [arch, machine, self.env, toolchain] = self.target.split("-")
        self.regexp_blocklisted_port = (
            "Probe PCI driver: net.*%s \(%s\) device: .*%s \(socket [-0-9]+\)"
        )
        self.pmdout = PmdOutput(self.dut)

    def set_up(self):
        """
        Run before each test case.
        Nothing to do.
        """
        pass

    def check_blocklisted_ports(self, output, ports, blocklisted=False):
        """
        Check if any of the ports in `ports` have been blocklisted, if so, raise
        exception.
        If `blocklisted` is True, then raise an exception if any of the ports
        in `ports` have not been blocklisted.
        """
        for port in ports:
            # Look for the PCI ID of each card followed by
            # "Device is blocklisted, not initializing" but avoid to consume more
            # than one device.
            port_pci = self.dut.ports_info[port]["pci"]
            regexp_blocklisted_port = self.regexp_blocklisted_port % (
                DRIVERS.get(self.nic),
                self.dut.ports_info[port]["type"],
                port_pci,
            )
            matching_ports = utils.regexp(output, regexp_blocklisted_port, True)
            if blocklisted:
                self.verify(
                    len(matching_ports) == 0, "Blocklisted port is being initialized"
                )
            else:
                self.verify(
                    len(matching_ports) == 1,
                    "Not blocklisted port is being blocklisted",
                )

    def test_bl_noblocklisted(self):
        """
        Run testpmd with no blocklisted device.
        """
        out = self.pmdout.start_testpmd("Default")
        rexp = r"Link"
        match_status = utils.regexp(out, rexp, True)

        self.check_blocklisted_ports(out, self.ports)

    def test_bl_oneportblocklisted(self):
        """
        Run testpmd with one port blocklisted.
        """
        self.dut.kill_all()
        out = self.pmdout.start_testpmd(
            "Default", eal_param="-b %s" % self.dut.ports_info[0]["pci"]
        )
        self.check_blocklisted_ports(out, self.ports[1:])

    def test_bl_allbutoneportblocklisted(self):
        """
        Run testpmd with all but one port blocklisted.
        """
        self.dut.kill_all()
        ports_to_blocklist = self.ports[:-1]
        cmdline = ""
        for port in ports_to_blocklist:
            cmdline += " -b %s" % self.dut.ports_info[port]["pci"]
        out = self.pmdout.start_testpmd("Default", eal_param=cmdline)
        blocklisted_ports = self.check_blocklisted_ports(out, ports_to_blocklist, True)

    def tear_down(self):
        """
        Run after each test case.
        Quit testpmd.
        """
        self.dut.send_expect("quit", "# ", 10)

    def tear_down_all(self):
        """
        Run after each test suite.
        Nothing to do.
        """
        pass
