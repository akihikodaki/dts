# BSD LICENSE
#
# Copyright(c) 2010-2016 Intel Corporation. All rights reserved.
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
Test external memory.
"""

import re
import time

import framework.utils as utils
from framework.test_case import TestCase
from framework.pmd_output import PmdOutput


class TestExternalMemory(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.pmdout = PmdOutput(self.dut)
        self.app_testpmd_path = self.dut.apps_name['test-pmd']

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def insmod_modprobe(self,modename=''):
        """
        Insmod modProbe before run test case
        """
        if modename == "igb_uio":
            self.dut.send_expect("modprobe uio", "#", 10)
            out = self.dut.send_expect("lsmod | grep igb_uio", "#")
            if "igb_uio" in out:
                self.dut.send_expect("rmmod -f igb_uio", "#", 10)
            self.dut.send_expect("insmod ./" + self.target + "/kmod/igb_uio.ko", "#", 10)

            out = self.dut.send_expect("lsmod | grep igb_uio", "#")
            assert ("igb_uio" in out), "Failed to insmod igb_uio"

            self.dut.bind_interfaces_linux(driver="igb_uio")

        if modename == "vfio-pci":
            self.dut.send_expect("rmmod vfio_pci", "#", 10)
            self.dut.send_expect("rmmod vfio_iommu_type1", "#", 10)
            self.dut.send_expect("rmmod vfio", "#", 10)
            self.dut.send_expect("modprobe vfio", "#", 10)
            self.dut.send_expect("modprobe vfio_pci", "#", 10)
            out = self.dut.send_expect("lsmod | grep vfio_iommu_type1", "#")
            if not out:
                out = self.dut.send_expect("ls /sys/module |grep vfio_pci", "#")
            assert ("vfio_pci" in out), "Failed to insmod vfio_pci"

            self.dut.bind_interfaces_linux(driver="vfio-pci")

    def test_IGB_UIO_xmem(self):
        """
        Verifier IGB_UIO and anonymous memory allocation
        """
        self.insmod_modprobe(modename="igb_uio")
        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.dut.send_expect(r'./%s %s -- --mp-alloc=xmem -i'
                             % (self.app_testpmd_path, self.eal_para), "testpmd>", 60)
        self.verifier_result()

    def test_IGB_UIO_xmemhuage(self):
        """
        Verifier IGB_UIO and anonymous hugepage memory allocation
        """
        self.insmod_modprobe(modename="igb_uio")
        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.dut.send_expect(r'./%s %s -- --mp-alloc=xmemhuge -i'
                             % (self.app_testpmd_path, self.eal_para), "testpmd>", 60)
        self.verifier_result()

    def test_VFIO_PCI_xmem(self):
        """
        Verifier VFIO_PCI and anonymous memory allocation
        """
        self.insmod_modprobe(modename="vfio-pci")
        self.dut.send_expect("echo 655359 > /sys/module/vfio_iommu_type1/parameters/dma_entry_limit", "#", 10)

        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.dut.send_expect(r'./%s %s -- --mp-alloc=xmem -i'
                             % (self.app_testpmd_path, self.eal_para),"testpmd>",60)

        self.verifier_result()

    def test_VFIO_PCI_xmemhuge(self):
        """
        Verifier VFIO and anonymous hugepage memory allocation
        """
        self.insmod_modprobe(modename="vfio-pci")

        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.dut.send_expect(r'./%s %s -- --mp-alloc=xmemhuge -i'
                             % (self.app_testpmd_path, self.eal_para),"testpmd>",60)

        self.verifier_result()

    def verifier_result(self):
        self.dut.send_expect("start", "testpmd>",10)
        self.pmdout.wait_link_status_up(self.dut_ports[0])
        self.scapy_send_packet(20)
        out = self.dut.send_expect("stop", "testpmd>", 10)

        p = re.compile(r'\d+')
        result = p.findall(out)
        amount = 20 * len(self.dut_ports)
        self.verify(str(amount) in result, "Wrong: can't get <%d> package" % amount)

        self.dut.send_expect("quit", "#", 10)

        self.dut.unbind_interfaces_linux(self.dut_ports)

    def scapy_send_packet(self, nu):
        """
        Send a packet to port
        """
        for i in range(len(self.dut_ports)):
            txport = self.tester.get_local_port(self.dut_ports[i])
            mac = self.dut.get_mac_address(self.dut_ports[i])
            txItf = self.tester.get_interface(txport)
            self.tester.scapy_append(
                'sendp([Ether()/IP()/UDP()/Raw(\'X\'*18)], iface="%s",count=%s)' % ( txItf, nu))
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
        self.dut.bind_interfaces_linux(driver=self.drivername)
        pass
