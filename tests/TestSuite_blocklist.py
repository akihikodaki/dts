# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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
        [arch, machine, self.env, toolchain] = self.target.split('-')
        self.regexp_blocklisted_port = "Probe PCI driver: net.*%s \(%s\) device: .*%s \(socket [-0-9]+\)"
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
            port_pci = self.dut.ports_info[port]['pci']
            regexp_blocklisted_port = self.regexp_blocklisted_port % (
                DRIVERS.get(self.nic), self.dut.ports_info[port]['type'],
                port_pci)
            matching_ports = utils.regexp(output, regexp_blocklisted_port, True)
            if blocklisted:
                self.verify(len(matching_ports) == 0,
                            "Blocklisted port is being initialized")
            else:
                self.verify(len(matching_ports) == 1,
                            "Not blocklisted port is being blocklisted")

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
        out = self.pmdout.start_testpmd("Default", eal_param="-b %s" % self.dut.ports_info[0]['pci'])
        self.check_blocklisted_ports(out, self.ports[1:])

    def test_bl_allbutoneportblocklisted(self):
        """
        Run testpmd with all but one port blocklisted.
        """
        self.dut.kill_all()
        ports_to_blocklist = self.ports[:-1]
        cmdline = ""
        for port in ports_to_blocklist:
            cmdline += " -b %s" % self.dut.ports_info[port]['pci']
        out = self.pmdout.start_testpmd("Default", eal_param=cmdline)
        blocklisted_ports = self.check_blocklisted_ports(out,
                                              ports_to_blocklist, True)

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
