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

This TestSuite runs the unit tests included in DPDK for KNI feature.
"""

import framework.utils as utils
from framework.test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsKni(TestCase):

    #
    #
    # Utility methods and other non-test code.
    #

    def insmod_kni(self):

        out = self.dut.send_expect('lsmod | grep rte_kni', "# ")

        if "rte_kni" in out:
            self.dut.send_expect('rmmod rte_kni.ko', "# ")

        out = self.dut.send_expect('insmod ./%s/kmod/rte_kni.ko lo_mode=lo_mode_fifo' % (self.target), "# ")

        self.verify("Error" not in out, "Error loading KNI module: " + out)

    #
    #
    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Run at the start of each test suite.

        KNI Prerequisites
        """
        self.dut.send_expect("sed -i -e 's/KNI_KMOD_ETHTOOL=n$/KNI_KMOD_ETHTOOL=y/' config/common_base", "# ", 30)
        self.dut.send_expect("sed -i -e 's/CONFIG_RTE_KNI_KMOD=n$/CONFIG_RTE_KNI_KMOD=y/' config/common_base", "# ", 30)
        self.dut.set_build_options({'KNI_KMOD_ETHTOOL': 'y'})
        self.dut.set_build_options({'RTE_KNI_KMOD': 'y'})
        self.dut.build_install_dpdk(self.target)
        self.cores = self.dut.get_core_list("all")
        self.insmod_kni()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_kni(self):
        """
        Run kni autotest.
        """
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params,"R.*T.*E.*>.*>", 60)        
        out = self.dut.send_expect("kni_autotest", "RTE>>", 60)
        self.dut.send_expect("quit", "# ")

        self.verify('Test OK' in out, 'Test Failed')

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("rmmod rte_kni", "# ", 5)
