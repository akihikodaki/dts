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

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

from .smoke_base import (
    DEFAULT_MTU_VALUE,
    JUMBO_FRAME_LENGTH,
    JUMBO_FRAME_MTU,
    LAUNCH_QUEUE,
    SmokeTest,
)

VF_MAC_ADDR = '00:11:22:33:44:55'


class TestVfSmoke(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.


        Smoke Prerequisites
        """

        # Based on h/w type, choose how many ports to use
        self.smoke_dut_ports = self.dut.get_ports(self.nic)
        self.check_session = None

        # Verify that enough ports are available
        self.verify(len(self.smoke_dut_ports) >= 1, "Insufficient ports")
        self.pf_interface = self.dut.ports_info[self.smoke_dut_ports[0]]['intf']
        self.smoke_tester_port = self.tester.get_local_port(self.smoke_dut_ports[0])
        self.smoke_tester_nic = self.tester.get_interface(self.smoke_tester_port)
        self.smoke_tester_mac = self.tester.get_mac(self.smoke_dut_ports[0])
        self.smoke_dut_mac = VF_MAC_ADDR

        # Verify that enough core
        self.cores = self.dut.get_core_list("1S/4C/1T")
        self.verify(self.cores is not None, "Insufficient cores for speed testing")

        # init pkt
        self.pkt = Packet()

        # generate vf
        self.dut.bind_interfaces_linux(self.kdriver)
        self.dut.generate_sriov_vfs_by_port(self.smoke_dut_ports[0], 1, self.kdriver)
        self.vf_ports = self.dut.ports_info[self.smoke_dut_ports[0]]['vfs_port']
        self.verify(len(self.vf_ports) != 0, "VF create failed")
        for port in self.vf_ports:
            port.bind_driver(self.drivername)
        self.vf0_prop = {'opt_host': self.vf_ports[0].pci}
        self.dut.send_expect("ifconfig %s up" % self.pf_interface, "# ")
        self.tester.send_expect("ifconfig %s up" % self.smoke_tester_nic, "# ")

        # set vf mac address
        self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.pf_interface, self.smoke_dut_mac), "# ")

        # set default app parameter
        if self.vf0_prop is not None:
            self.ports = [self.vf0_prop['opt_host']]

        self.pmd_out = PmdOutput(self.dut)
        self.param = '--max-pkt-len={} --tx-offloads=0x8000 --rxq={} --txq={}'.format(JUMBO_FRAME_LENGTH,
                                                                                      LAUNCH_QUEUE,
                                                                                      LAUNCH_QUEUE)
        self.test_func = SmokeTest(self)
        self.check_session = self.dut.new_session(suite="vf_smoke_test")

    def set_up(self):
        """
        Run before each test case.
        """
        # verify app launch state.
        out = self.check_session.send_expect("ls -l /var/run/dpdk |awk '/^d/ {print $NF}'", '# ', 1)
        if out == '' or 'No such file or directory' in out:
            self.vf_launch_dpdk_app()

        if self._suite_result.test_case == "test_vf_jumbo_frames":
            self.tester.send_expect("ifconfig {} mtu {}".format(self.smoke_tester_nic, JUMBO_FRAME_MTU), '# ')

    def vf_launch_dpdk_app(self):
        self.pmd_out.start_testpmd(cores=self.cores, ports=self.ports, param=self.param)

        # set default param
        self.dut.send_expect("set promisc all off", "testpmd> ")
        self.pmd_out.wait_link_status_up(self.smoke_dut_ports[0])

    def test_vf_jumbo_frames(self):
        """
        This case aims to test transmitting jumbo frame packet on testpmd with
        jumbo frame support.
        """
        self.dut.send_expect("set verbose 3", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.pmd_out.wait_link_status_up(self.smoke_dut_ports[0])
        result = self.test_func.check_jumbo_frames()
        self.verify(result, "enable disable jumbo frames failed")

    def test_vf_rss(self):
        """
        Check default rss function.
        """
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.pmd_out.wait_link_status_up(self.smoke_dut_ports[0])
        result = self.test_func.check_rss()
        self.verify(result, "enable disable rss failed")

    def test_vf_tx_rx_queue(self):
        """
        Check dpdk queue configure.
        """
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.pmd_out.wait_link_status_up(self.smoke_dut_ports[0])
        result = self.test_func.check_tx_rx_queue()
        self.verify(result, "check tx rx queue failed")

    def tear_down(self):
        # set tester mtu to default value
        self.pmd_out.execute_cmd("stop")
        if self._suite_result.test_case == "test_vf_jumbo_frames":
            self.tester.send_expect("ifconfig {} mtu {}".format(self.smoke_tester_nic, DEFAULT_PKG_LEN), '# ')

        # set dpdk queues to launch value
        if self._suite_result.test_case == "test_vf_tx_rx_queue":
            self.dut.send_expect("port stop all", "testpmd> ")
            self.dut.send_expect("port config all rxq {}".format(LAUNCH_QUEUE), "testpmd> ")
            self.dut.send_expect("port config all txq {}".format(LAUNCH_QUEUE), "testpmd> ")
            self.dut.send_expect("port start all", "testpmd> ")

    def tear_down_all(self):
        if self.check_session:
            self.dut.close_session(self.check_session)
            self.check_session = None
        self.dut.kill_all()
        if self.vf0_prop:
            self.dut.destroy_sriov_vfs_by_port(self.smoke_dut_ports[0])
        self.dut.bind_interfaces_linux(self.drivername)
