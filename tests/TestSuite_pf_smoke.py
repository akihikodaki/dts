# BSD LICENSE
#
# Copyright(c)2021 Intel Corporation. All rights reserved.
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

from packet import Packet
from pmd_output import PmdOutput
from test_case import TestCase
from smoke_base import SmokeTest
from smoke_base import JUMBO_FRAME_LENGTH
from smoke_base import JUMBO_FRAME_MTU
from smoke_base import DEFAULT_MTU_VALUE
from smoke_base import LAUNCH_QUEUE


class TestPfSmoke(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.


        Smoke Prerequisites
        """

        # Based on h/w type, choose how many ports to use
        self.smoke_dut_ports = self.dut.get_ports(self.nic)

        # Verify that enough ports are available
        self.verify(len(self.smoke_dut_ports) >= 1, "Insufficient ports")
        self.smoke_tester_port = self.tester.get_local_port(self.smoke_dut_ports[0])
        self.smoke_tester_nic = self.tester.get_interface(self.smoke_tester_port)
        self.smoke_tester_mac = self.tester.get_mac(self.smoke_dut_ports[0])
        self.smoke_dut_mac = self.dut.get_mac_address(self.smoke_dut_ports[0])

        # Verify that enough core
        self.cores = self.dut.get_core_list("1S/4C/1T")
        self.verify(self.cores is not None, "Insufficient cores for speed testing")

        # init pkt
        self.pkt = Packet()

        # set default app parameter
        self.pmd_out = PmdOutput(self.dut)
        self.ports = [self.dut.ports_info[self.smoke_dut_ports[0]]['pci']]
        self.param = '--max-pkt-len={} --tx-offloads=0x8000 --rxq={} --txq={}'.format(JUMBO_FRAME_LENGTH,
                                                                                      LAUNCH_QUEUE,
                                                                                      LAUNCH_QUEUE)
        self.test_func = SmokeTest(self)
        self.check_session = self.dut.new_session(suite="pf_smoke_test")

    def set_up(self):
        """
        Run before each test case.
        """
        # verify app launch state.
        out = self.check_session.send_expect("ls -l /var/run/dpdk |awk '/^d/ {print $NF}'", '# ', 1)
        if out == '' or 'No such file or directory' in out:
            self.pf_launch_dpdk_app()

        # set tester mtu
        if self._suite_result.test_case == "test_pf_jumbo_frames":
            self.tester.send_expect("ifconfig {} mtu {}".format(self.smoke_tester_nic, JUMBO_FRAME_MTU), '# ')

    def pf_launch_dpdk_app(self):
        self.pmd_out.start_testpmd(cores=self.cores, ports=self.ports, param=self.param)

        # set default param
        self.dut.send_expect("set promisc all off", "testpmd> ")
        self.pmd_out.wait_link_status_up(self.smoke_dut_ports[0])

    def test_pf_jumbo_frames(self):
        """
        This case aims to test transmitting jumbo frame packet on testpmd with
        jumbo frame support.
        """
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("set verbose 3", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.pmd_out.wait_link_status_up(self.smoke_dut_ports[0])
        result = self.test_func.check_jumbo_frames()
        self.verify(result, "enable disable jumbo frames failed")

    def test_pf_rss(self):
        """
        Check default rss function.
        """
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.pmd_out.wait_link_status_up(self.smoke_dut_ports[0])
        result = self.test_func.check_rss()
        self.verify(result, "enable disable rss failed")

    def test_pf_tx_rx_queue(self):
        """
        Check dpdk queue configure.
        """
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.pmd_out.wait_link_status_up(self.smoke_dut_ports[0])
        result = self.test_func.check_tx_rx_queue()
        self.verify(result, "check tx rx queue failed")

    def tear_down(self):
        self.pmd_out.execute_cmd("stop")

        # set tester mtu to default value
        if self._suite_result.test_case == "test_pf_jumbo_frames":
            self.tester.send_expect("ifconfig {} mtu {}".format(self.smoke_tester_nic, DEFAULT_MTU_VALUE), '# ')

        # set dpdk queues to launch value
        if self._suite_result.test_case == "test_pf_tx_rx_queue":
            self.dut.send_expect("stop", "testpmd> ")
            self.dut.send_expect("port stop all", "testpmd> ")
            self.dut.send_expect("port config all rxq {}".format(LAUNCH_QUEUE), "testpmd> ")
            self.dut.send_expect("port config all txq {}".format(LAUNCH_QUEUE), "testpmd> ")
            self.dut.send_expect("port start all", "testpmd> ")

    def tear_down_all(self):
        if self.check_session:
            self.dut.close_session(self.check_session)
            self.check_session = None
        self.dut.kill_all()
