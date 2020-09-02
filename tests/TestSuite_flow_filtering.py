# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation. All rights reserved.
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

import os
import utils
import time
import re
import os
import packet
from test_case import TestCase
from settings import HEADER_SIZE


class TestFlowFiltering(TestCase):

    def set_up_all(self):
        """
        Run before each test suite
        """
        # initialize ports topology
        self.dut_ports = self.dut.get_ports(self.nic)
        self.dts_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.txitf = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0]))
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        out = self.dut.build_dpdk_apps("./examples/flow_filtering")
        self.verify('Error' not in out, "Compilation failed")

    def set_up(self):
        """
        Run before each test case.
        """
        cmd = self.dut.apps_name['flow_filtering'] + "-l 1 -n 1"
        out = self.dut.send_command(cmd, timeout=15)
        self.verify("Error" not in out, "flow launch failed")

    def send_packet(self, pkg):
        """
        Send packets according to parameters.
        """
        self.pkt = packet.Packet()
        for packet_type in list(pkg.keys()):
            self.pkt.append_pkt(pkg[packet_type])
        self.pkt.send_pkt(crb=self.tester, tx_port=self.txitf, count=1)

        time.sleep(2)

    def check_flow_queue(self):
        '''
        Get dut flow result
        '''
        result = self.dut.get_session_output(timeout=2)
        if str.upper(self.dts_mac) in result:
            self.verify("queue" in result, "Dut receive flow failed!")
            queue_result = re.findall(r"queue=(\S+)", result)
            return queue_result
        else:
            raise Exception("Dut not receive correct package!")

    def test_flow_filtering_match_rule(self):
        pkg = {'IP/src1': 'Ether(dst="%s")/IP(src="0.0.0.0", dst="192.168.1.1")/Raw("x"*20)' % self.dts_mac,
               'IP/src2': 'Ether(dst="%s")/IP(src="0.0.0.1", dst="192.168.1.1")/Raw("x"*20)' % self.dts_mac}
        self.send_packet(pkg)
        queue_list = self.check_flow_queue()
        self.verify(len(queue_list) == 2, "Dut receive flow queue error!")
        self.verify(queue_list[0] == queue_list[1] and queue_list[0] == "0x1", "Flow filter not match rule!")

    def test_flow_filtering_dismatch_rule(self):
        pkg = {'IP/dst': 'Ether(dst="%s")/IP(src="0.0.0.0", dst="192.168.1.2")/Raw("x"*20)' % self.dts_mac}
        self.send_packet(pkg)
        queue_list = self.check_flow_queue()
        self.verify(len(queue_list) == 1 and queue_list[0] != "0x1", "Dismatch rule failed!")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("^C", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
