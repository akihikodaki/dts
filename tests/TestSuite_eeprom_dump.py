#BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved
# Copyright © 2020 The University of New Hampshire. All rights reserved.
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
"""
import utils
import re
from pmd_output import PmdOutput
from test_case import TestCase


class TestEEPROMDump(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.ports = self.dut.get_ports()

        self.pmdout = PmdOutput(self.dut)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def clean_up_and_compare(self, testname, port):
        # comapre the two files
        result = self.dut.send_expect(f"diff testpmd_{testname}_{port}.txt ethtool_{testname}_{port}.txt", "#") 

        # Clean up files
        self.dut.send_expect(f"rm ethtool_{testname}_raw_{port}.txt", "#")
        self.dut.send_expect(f"rm ethtool_{testname}_hex_{port}.txt", "#")
        self.dut.send_expect(f"rm ethtool_{testname}_{port}.txt", "#")
        self.dut.send_expect(f"rm testpmd_{testname}_{port}.txt", "#")

        self.verify(not result, "Testpmd dumped is not same as linux dumped")

    def dump_to_file(self, regex, get, to):
            # Get testpmd output to have only hex value
            for line in re.findall(regex, get):
                line = line.replace(" ", "").lower()
                self.dut.send_expect(f"echo {line} >> {to}", "#")

    def check_output(self, testname, ethcommand):
        self.pmdout.start_testpmd("Default")
        portsinfo = []

        for port in self.ports:
            pmdout = self.dut.send_expect(f"show port {port} {testname}", "testpmd>") 
            self.verify("Finish --" in pmdout, f"{testname} dump failed")

            # get length from testpmd outout
            length = re.findall(r'(?<=length: )\d+', pmdout)[0]

            # Store the output and length
            portinfo = {'port': port, 'length' : length, 'pmdout' :pmdout}
            portsinfo.append(portinfo)

        self.dut.send_expect("quit", "# ")

        # Bind to the default driver to use ethtool after quit testpmd
        for port in self.ports:
            netdev = self.dut.ports_info[port]['port']
            portinfo = portsinfo[port]

            # strip original driver
            portinfo['ori_driver'] = netdev.get_nic_driver()
            portinfo['net_dev'] = netdev

            # bind to default driver
            netdev.bind_driver()

            # get interface
            iface = netdev.get_interface_name()

            # Get testpmd output to have only hex value
            self.dump_to_file(r'(?<=: )(.*)(?= \| )', portinfo['pmdout'], f"testpmd_{testname}_{port}.txt")

            self.dut.send_expect(f"ethtool {ethcommand} {iface} raw on length {portinfo['length']} >> ethtool_{testname}_raw_{port}.txt", "#")
            self.dut.send_expect(f"xxd ethtool_{testname}_raw_{port}.txt >> ethtool_{testname}_hex_{port}.txt", "#")
            portinfo['ethout'] = self.dut.send_expect(f"cat ethtool_{testname}_hex_{port}.txt", "#")
            
            self.dump_to_file(r'(?<=: )(.*)(?=  )', portinfo['ethout'], f"ethtool_{testname}_{port}.txt")

            # Compare the files and delete the files after
            self.clean_up_and_compare(testname, port)

            # bind to original driver
            portinfo['net_dev'].bind_driver(portinfo['ori_driver'])
        
    def test_eeprom_dump(self):
        self.check_output("eeprom", "-e")

    def test_module_eeprom_dump(self):
        self.check_output("module_eeprom", "-m")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
