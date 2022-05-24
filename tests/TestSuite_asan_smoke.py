# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

from .smoke_base import SmokeTest


class TestASanSmoke(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
        """
        self.smoke_dut_ports = self.dut.get_ports(self.nic)
        self.ports_pci = [self.dut.ports_info[self.smoke_dut_ports[0]]["pci"]]
        # Verify that enough ports are available
        self.verify(len(self.smoke_dut_ports) >= 1, "Insufficient ports")
        self.tester_port0 = self.tester.get_local_port(self.smoke_dut_ports[0])
        self.smoke_tester_nic = self.tester.get_interface(self.tester_port0)
        self.smoke_tester_mac = self.tester.get_mac(self.smoke_dut_ports[0])
        self.smoke_dut_mac = self.dut.get_mac_address(self.smoke_dut_ports[0])
        self.cores = "1S/5C/1T"
        # check core num
        core_list = self.dut.get_core_list(self.cores)
        self.verify(len(core_list) >= 5, "Insufficient cores for testing")

        # init Packet(), SmokeTest(), PmdOutput()
        self.pkt = Packet()
        self.smoke_base = SmokeTest(self)
        self.pmd_out = PmdOutput(self.dut)

        # build dpdk with ASan tool
        self.dut.build_install_dpdk(
            target=self.target,
            extra_options="-Dbuildtype=debug -Db_lundef=false -Db_sanitize=address",
        )

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def tear_down(self):
        """
        Run after each test case.
        """
        self.pmd_out.execute_cmd("stop")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("quit", "#")
        self.dut.kill_all()
        self.dut.build_install_dpdk(self.target)

    def check_testpmd_status(self):
        cmd = "ps -aux | grep testpmd | grep -v grep"
        out = self.dut.send_expect(cmd, "#", 15, alt_session=True)
        self.verify(
            "testpmd" in out, "After build dpdk with ASan, start testpmd failed"
        )

    def test_rxtx_with_ASan_enable(self):
        out = self.pmd_out.start_testpmd(cores=self.cores, ports=self.ports_pci)
        self.check_testpmd_status()
        self.verify(
            all(
                [
                    error_key not in out
                    for error_key in ["heap-buffer-overflow", "use-after-free"]
                ]
            ),
            "the testpmd have error key words",
        )
        self.pmd_out.execute_cmd("set fwd mac")
        self.pmd_out.execute_cmd("set verbose 1")
        self.pmd_out.execute_cmd("start")
        queues, stats = self.smoke_base.send_pkg_return_stats()
        self.verify(
            stats["RX-packets"] != 0 and stats["RX-packets"] == stats["TX-packets"],
            "RX-packets: {} "
            "TX-packets : {}, rx tx test failed".format(
                stats["RX-packets"], stats["TX-packets"]
            ),
        )
