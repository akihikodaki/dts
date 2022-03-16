# BSD LICENSE
#
# Copyright(c) 2010-2022 Intel Corporation. All rights reserved.
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


import re

from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, check_supported_nic


class TestCVL1PPS(TestCase):
    supported_nic = ["columbiaville_100g", "columbiaville_25g"]

    @check_supported_nic(supported_nic)
    def set_up_all(self):
        """
        Run at the start of each test suite.
        prerequisites.
        """
        # Based on h/w type, chose how many ports to use
        dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(dut_ports) >= 1, "Insufficient ports for testing")
        # Verify that enough threads are available
        self.cores = self.dut.get_core_list("1S/2C/1T")
        self.verify(self.cores, "Insufficient cores for speed testing")
        self.pci = self.dut.ports_info[dut_ports[0]]["pci"]
        self.pmd_output = PmdOutput(self.dut)
        self.GLTSYN_AUX = re.compile(r"0x00000007\s+\(7\)")
        self.GLTSYN_CLKO = re.compile(r"0x1DCD6500\s+\(500000000\)")
        self.pattern = re.compile(
            "register\s+at\s+offset\s+.*:\s+(?P<hex>0x\w+)\s+\(\d+\)"
        )

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def read_register(self, addr, port_id=0):
        cmd = "read reg {} {}".format(port_id, addr)
        return self.pmd_output.execute_cmd(cmd)

    def launch_testpmd(self, pin_id, rxq=4, txq=4):
        self.out = self.pmd_output.start_testpmd(
            cores="1S/2C/1T",
            param="--rxq={} --txq={} ".format(rxq, txq),
            eal_param="-a {},pps_out='[pin:{}]'".format(self.pci, pin_id),
        )
        # Check the GLTSYN_AUX_OUT, GLTSYN_CLKO and other two registers

    def check_four_registers(self, pin_id, addrs, port_id=0):
        self.launch_testpmd(pin_id)
        for i in range(len(addrs)):
            out = self.read_register(addrs[i], port_id=port_id)
            if i == 0:
                pattern = self.GLTSYN_AUX
            elif i == 1:
                pattern = self.GLTSYN_CLKO
            else:
                pattern = self.pattern
            res = pattern.search(out)
            self.verify(
                res, "pattern:{} not found in output info: {}".format(pattern, out)
            )
            if i > 1:
                actual_value = int(res.group("hex"), 16)
                self.verify(
                    actual_value != 0,
                    "check pin id:{0} register address:{1} failed, expected value is non-zero, actual value is:{2}".format(
                        pin_id, addrs[i], actual_value
                    ),
                )
            self.logger.info(
                "check pin id: {0} register address: {1} pass".format(pin_id, addrs[i])
            )
        # complete checking registers
        self.quit_testpmd()
        return res

    def check_GLGEN_GPIO_CTL_value(self, hex_value, target_value):
        self.verify(
            hex_value[-3] == target_value,
            "check register failed, target value is {} not match expected value {}".format(
                hex_value[-3], target_value
            ),
        )
        bit_5th = bin(int(hex_value, 16))[-5]
        self.verify(
            bit_5th == "1",
            "check register failed, the 5th bit is {} not match expected value {}".format(
                bit_5th, 1
            ),
        )
        self.logger.info("check register value {} pass".format(hex_value))

    def test_check_register_with_pin_id_0(self):
        addrs = ["0x00088998", "0x000889B8", "0x00088928", "0x00088930", "0x000880C8"]
        res = self.check_four_registers(pin_id=0, addrs=addrs)
        # 3rd Hexadecimal digit of GLGEN_GPIO_CTL[0] 0x000880C8 is 8. And the 5th binary digit is 1.
        self.check_GLGEN_GPIO_CTL_value(hex_value=res.group("hex"), target_value="8")

    def test_check_register_with_pin_id_1(self):
        addrs = ["0x000889A0", "0x000889C0", "0x00088938", "0x00088940", "0x000880CC"]
        res = self.check_four_registers(pin_id=1, addrs=addrs)
        # 3rd Hexadecimal digit of GLGEN_GPIO_CTL[1] 0x000880CC is 9. And the 5th binary digit is 1.
        self.check_GLGEN_GPIO_CTL_value(hex_value=res.group("hex"), target_value="9")

    def test_check_register_with_pin_id_2(self):
        addrs = ["0x000889A8", "0x000889C8", "0x00088948", "0x00088950", "0x000880D0"]
        res = self.check_four_registers(pin_id=2, addrs=addrs)
        # 3rd Hexadecimal digit of GLGEN_GPIO_CTL[2] 0x000880D0 is A. And the 5th binary digit is 1.
        self.check_GLGEN_GPIO_CTL_value(hex_value=res.group("hex"), target_value="A")

    def test_check_register_with_pin_id_3(self):
        addrs = ["0x000889B0", "0x000889D0", "0x00088958", "0x00088960", "0x000880D4"]
        res = self.check_four_registers(pin_id=3, addrs=addrs)
        # 3rd Hexadecimal digit of GLGEN_GPIO_CTL[3] 0x000880D4 is B. And the 5th binary digit is 1.
        self.check_GLGEN_GPIO_CTL_value(hex_value=res.group("hex"), target_value="B")

    def quit_testpmd(self):
        self.pmd_output.quit()

    def tear_down(self):
        self.dut.kill_all()

    def tear_down_all(self):
        self.dut.kill_all()
