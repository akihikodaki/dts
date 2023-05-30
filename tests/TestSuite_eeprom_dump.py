# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
# Copyright(c) 2020 The University of New Hampshire
#

"""
DPDK Test suite.
"""
import re
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestEepromDump(TestCase):
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
        result = self.dut.send_expect(
            f"diff testpmd_{testname}_{port}.txt ethtool_{testname}_{port}.txt", "#"
        )

        # Clean up files
        self.dut.send_expect(f"rm ethtool_{testname}_raw_{port}.txt", "#")
        self.dut.send_expect(f"rm ethtool_{testname}_hex_{port}.txt", "#")
        self.dut.send_expect(f"rm ethtool_{testname}_{port}.txt", "#")
        self.dut.send_expect(f"rm testpmd_{testname}_{port}.txt", "#")

        self.verify(not result, "Testpmd dumped is not same as linux dumped")

    def dump_to_file(self, regex, get, to, testname):
        # if nic is Intel® Ethernet 800 Series, eeprom_dump get testpmd output of the
        # first 1000 lines, module_eeprom_dump get testpmd output of the first 16 lines.
        if self.nic in [
            "ICE_25G-E810C_SFP",
            "ICE_100G-E810C_QSFP",
            "ICE_25G-E823C_QSFP",
        ]:
            if testname == "eeprom":
                count = 1000
            elif testname == "module_eeprom":
                count = 16
            n = 0
            # Get testpmd output to have only hex value
            for line in re.findall(regex, get):
                n = n + 1
                if n <= count:
                    line = line.replace(" ", "").lower()
                    self.dut.send_expect(f"echo {line} >> {to}", "#")

        # Get testpmd output to have only hex value
        else:
            for line in re.findall(regex, get):
                line = line.replace(" ", "").lower()
                self.dut.send_expect(f"echo {line} >> {to}", "#")

    def check_output(self, testname, ethcommand):
        self.pmdout.start_testpmd("Default")
        portsinfo = []

        for port in self.ports:
            # show port {port} eeprom has 10485760 bytes, and it takes about 13 minutes to show finish.
            pmdout = self.dut.send_expect(
                f"show port {port} {testname}", "testpmd>", timeout=800
            )
            self.verify("Finish --" in pmdout, f"{testname} dump failed")

            # get length from testpmd outout
            length = re.findall(r"(?<=length: )\d+", pmdout)[0]

            # Store the output and length
            portinfo = {"port": port, "length": length, "pmdout": pmdout}
            portsinfo.append(portinfo)

        self.dut.send_expect("quit", "# ")

        # Bind to the default driver to use ethtool after quit testpmd
        for port in self.ports:
            netdev = self.dut.ports_info[port]["port"]
            portinfo = portsinfo[port]

            # strip original driver
            portinfo["ori_driver"] = netdev.get_nic_driver()
            portinfo["net_dev"] = netdev

            # bind to default driver
            netdev.bind_driver()

            # get interface
            iface = netdev.get_interface_name()

            # Get testpmd output to have only hex value
            self.dump_to_file(
                r"(?<=: )(.*)(?= \| )",
                portinfo["pmdout"],
                f"testpmd_{testname}_{port}.txt",
                testname,
            )

            self.dut.send_expect(
                f"ethtool {ethcommand} {iface} raw on length {portinfo['length']} >> ethtool_{testname}_raw_{port}.txt",
                "#",
            )
            self.dut.send_expect(
                f"xxd ethtool_{testname}_raw_{port}.txt >> ethtool_{testname}_hex_{port}.txt",
                "#",
            )
            portinfo["ethout"] = self.dut.send_expect(
                f"cat ethtool_{testname}_hex_{port}.txt", "# ", trim_whitespace=False
            )

            self.dump_to_file(
                r"(?<=: )(.*?)(?=  )",
                portinfo["ethout"],
                f"ethtool_{testname}_{port}.txt",
                testname,
            )

            # Compare the files and delete the files after
            self.clean_up_and_compare(testname, port)

            # bind to original driver
            portinfo["net_dev"].bind_driver(portinfo["ori_driver"])

    def test_eeprom_dump(self):
        self.check_output("eeprom", "-e")

    def test_module_eeprom_dump(self):
        self.check_output("module_eeprom", "-m")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        self.dut.bind_interfaces_linux(self.drivername)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
