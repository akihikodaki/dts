# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2016 Intel Corporation
#

"""
DPDK Test suite.
Test external memory.
"""

import re
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, skip_unsupported_host_driver


class TestExternalMemory(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.pmdout = PmdOutput(self.dut)
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    @skip_unsupported_host_driver(["vfio-pci"])
    def test_IGB_UIO_xmem(self):
        """
        Verifier IGB_UIO and anonymous memory allocation
        """
        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.dut.send_expect(
            r"./%s %s -- --mp-alloc=xmem -i" % (self.app_testpmd_path, self.eal_para),
            "testpmd>",
            60,
        )
        self.verifier_result()

    @skip_unsupported_host_driver(["vfio-pci"])
    def test_IGB_UIO_xmemhuage(self):
        """
        Verifier IGB_UIO and anonymous hugepage memory allocation
        """
        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.dut.send_expect(
            r"./%s %s -- --mp-alloc=xmemhuge -i"
            % (self.app_testpmd_path, self.eal_para),
            "testpmd>",
            60,
        )
        self.verifier_result()

    def test_VFIO_PCI_xmem(self):
        """
        Verifier VFIO_PCI and anonymous memory allocation
        """
        self.dut.send_expect(
            "echo 655359 > /sys/module/vfio_iommu_type1/parameters/dma_entry_limit",
            "#",
            10,
        )

        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.dut.send_expect(
            r"./%s %s -- --mp-alloc=xmem -i" % (self.app_testpmd_path, self.eal_para),
            "testpmd>",
            60,
        )

        self.verifier_result()

    def test_VFIO_PCI_xmemhuge(self):
        """
        Verifier VFIO and anonymous hugepage memory allocation
        """
        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.dut.send_expect(
            r"./%s %s -- --mp-alloc=xmemhuge -i"
            % (self.app_testpmd_path, self.eal_para),
            "testpmd>",
            60,
        )

        self.verifier_result()

    def verifier_result(self):
        self.dut.send_expect("start", "testpmd>", 10)
        self.pmdout.wait_link_status_up(self.dut_ports[0])
        self.scapy_send_packet(20)
        out = self.dut.send_expect("stop", "testpmd>", 10)

        p = re.compile(r"\d+")
        result = p.findall(out)
        amount = 20 * len(self.dut_ports)
        self.verify(str(amount) in result, "Wrong: can't get <%d> package" % amount)

        self.dut.send_expect("quit", "#", 10)

    def scapy_send_packet(self, nu):
        """
        Send a packet to port
        """
        for i in range(len(self.dut_ports)):
            txport = self.tester.get_local_port(self.dut_ports[i])
            mac = self.dut.get_mac_address(self.dut_ports[i])
            txItf = self.tester.get_interface(txport)
            self.tester.scapy_append(
                "sendp([Ether()/IP()/UDP()/Raw('X'*18)], iface=\"%s\",count=%s)"
                % (txItf, nu)
            )
            self.tester.scapy_execute()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        time.sleep(2)
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
