# BSD LICENSE
#
# Copyright (c) <2019-2020>, Intel Corporation
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
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
#
# =====================
# DPDK ABI Stable Tests
# =====================
#
# Description
# ===========
#
# This test suite includes both functional and performance test cases to
# ensure that DPDK point releases (xx.02, xx.05, xx.08) are not only binary
# compatible, but are also functionally and reasonably performance
# compatibly with the previous vxx.11 release.


"""
DPDK Test suite.

Test support of ABI .

"""
import utils
import time

from test_case import TestCase
from pmd_output import PmdOutput
from settings import load_global_setting, HOST_SHARED_LIB_SETTING, HOST_SHARED_LIB_PATH


class TestABIStable(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.pmdout = PmdOutput(self.dut)
        self.dut_ports = self.dut.get_ports(self.nic)
        self.port_mask = utils.create_mask([self.dut_ports[0]])
        use_shared_lib = load_global_setting(HOST_SHARED_LIB_SETTING)
        self.verify(use_shared_lib != 'ture', "The case only support ABI mode")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_negative(self):
        net_device = self.dut.ports_info[0]['port']
        nic_drive = net_device.get_nic_driver()
        shared_lib_path = load_global_setting(HOST_SHARED_LIB_PATH)
        self.verify(nic_drive != "ixgbe", "The case only support ixgbe drive")

        cmd = 'rm -rf {}'.format(shared_lib_path)
        self.dut.send_expect(cmd, "#")
        cmd = 'cp -a /root/shared_lib_negative {}'.format(shared_lib_path)
        self.dut.send_expect(cmd, "#")
        self.pmdout.start_testpmd("Default", "--portmask={} ".format(self.port_mask))
        time.sleep(1)
        self.dut.send_expect("set fwd txonly", "testpmd>")
        self.dut.send_expect("start", "testpmd>")
        time.sleep(1)
        try:
            self.dut.send_expect("quit", "#")
        except Exception as e:
            if 'TIMEOUT' in str(e):
                self.logger.info(str(e))
            else:
                self.verify(False, "No timeout")
            self.dut.kill_all()
            return

        self.verify(False, "negative test failed")
        self.dut.kill_all()

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
