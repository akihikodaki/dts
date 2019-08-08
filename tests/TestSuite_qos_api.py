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

"""
DPDK Test suite.
Test QOS API in DPDK.
"""

import utils
import string
import re
import time
import os
from pktgen import PacketGeneratorHelper
from test_case import TestCase
from pmd_output import PmdOutput


class TestQosApi(TestCase):

    def set_up_all(self):
        """
        ip_fragmentation Prerequisites
        """

        # Based on h/w type, choose how many ports to use
        ports = self.dut.get_ports()
        self.dut_ports = self.dut.get_ports(self.nic)

        # Verify that enough ports are available
        self.verify(len(ports) >= 2, "Insufficient ports for testing")

        self.ports_socket = self.dut.get_numa_id(ports[0])
        # each flow to 200Mbps
        self.bps = 200000000
        self.bps_rate = [0, 0.1]
        self.eal_param = ' --master-lcore=1'
        # Verify that enough threads are available
        cores = self.dut.get_core_list("1S/1C/1T")
        self.verify(cores is not None, "Insufficient cores for speed testing")
        global P0, P1
        P0 = ports[0]
        P1 = ports[1]

        self.txItf = self.tester.get_interface(self.tester.get_local_port(P0))
        self.rxItf = self.tester.get_interface(self.tester.get_local_port(P1))
        self.dmac = self.dut.get_mac_address(P0)
        self.host_testpmd = PmdOutput(self.dut)

        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(
                                os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

    def set_up(self):
        """
        Run before each test case.
        """

    def add_root_non_leaf_node(self):
        self.dut.send_expect('add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0', 'testpmd> ')

    def add_private_shaper(self, n):
        for i in range(n):
            self.dut.send_expect('add port tm node shaper profile 1 %s 0 0 25000000 0 0' % str(i + 1), 'testpmd> ')

    def add_private_shaper_ixgbe(self, n):
        for i in range(n):
            self.dut.send_expect('add port tm node shaper profile 1 %s 0 0 25000000 0 0' % i, 'testpmd> ')

    def add_tc_node(self, n):
        for i in range(n):
            self.dut.send_expect('add port tm nonleaf node 1 %s 1000000 0 1 1 1 1 0 0' % (900000 + i), 'testpmd> ')

    def add_tc_node_ixgbe(self, n):
        for i in range(n):
            self.dut.send_expect('add port tm nonleaf node 1 %s 1000000 0 1 1 -1 1 0 0' % (900000 + i), 'testpmd> ')

    def set_dcb(self, n):
        """
        set DCB
        """
        self.dut.send_expect('port stop all', 'testpmd> ')
        self.dut.send_expect('port config 0 dcb vt off %s pfc off' % n, 'testpmd> ')
        self.dut.send_expect('port config 1 dcb vt off %s pfc off' % n, 'testpmd> ')
        self.dut.send_expect('port start all', 'testpmd> ')

    def scapy_send_packet_verify(self, n):
        self.tester.scapy_foreground()
        dmac = self.dut.get_mac_address(P0)
        queues_4tc = [0, 32, 64, 96]
        queues_8tc = [0, 16, 32, 48, 64, 80, 96, 112]
        print dmac
        for i in range(n):
            pkt = "Ether(dst='%s', src='00:02:00:00:00:01')/Dot1Q(prio=%s)/IP()/Raw('x'*20)" % (dmac, i)
            self.tester.scapy_append('sendp([%s], iface="%s")' % (pkt, self.txItf))
            self.tester.scapy_execute()
            time.sleep(2)
            out = self.dut.get_session_output()
            if self.kdriver == 'i40e':
                self.verify('queue %s' % i in out and dmac.upper() in out, 'wrong queue receive packet')
            else:
                if n == 4:
                    self.verify('queue %s' % queues_4tc[i] in out and dmac.upper() in out, 'wrong queue receive packet')
                else:
                    self.verify('queue %s' % queues_8tc[i] in out and dmac.upper() in out, 'wrong queue receive packet')

    def queue_map_test(self, n):
        self.set_dcb(n)
        self.dut.send_expect('port start all', 'testpmd> ')
        self.dut.send_expect('set fwd rxonly', 'testpmd> ')
        self.dut.send_expect('set verbose 1', 'testpmd> ')
        self.dut.send_expect('start', 'testpmd> ')
        self.scapy_send_packet_verify(n)

    def shaping_tc_test_i40e(self, n):
        self.set_dcb(n)
        self.add_root_non_leaf_node()
        self.add_private_shaper(n)
        self.add_tc_node(n)
        self.add_queue_leaf_node(n)
        self.dut.send_expect('port tm hierarchy commit 1 no', 'testpmd> ')
        self.dut.send_expect('start', 'testpmd> ')
        self.perf_test(n)

    def test_dcb_4tc_queue_map_i40e(self):
        self.verify(self.kdriver in ["i40e"], "NIC Unsupported: " + str(self.nic))
        self.host_testpmd.start_testpmd("1S/5C/1T", " --nb-cores=4 --txq=4 --rxq=4 --rss-ip ", eal_param=self.eal_param)
        self.queue_map_test(4)

    def test_dcb_8tc_queue_map_i40e(self):
        self.verify(self.kdriver in ["i40e"], "NIC Unsupported: " + str(self.nic))
        self.host_testpmd.start_testpmd("1S/9C/1T", " --nb-cores=8 --txq=8 --rxq=8 --rss-ip ", eal_param=self.eal_param)
        self.queue_map_test(8)

    def test_perf_shaping_for_port_i40e(self):
        self.verify(self.kdriver in ["i40e"], "NIC Unsupported: " + str(self.nic))
        eal_param = ' --master-lcore=1'
        self.host_testpmd.start_testpmd("1S/5C/1T", " --nb-cores=4 --txq=4 --rxq=4 --rss-ip ", eal_param=self.eal_param)
        self.dut.send_expect('port stop 1', 'testpmd> ')
        self.dut.send_expect('add port tm node shaper profile 1 0 0 0 25000000 0 0', 'testpmd> ')
        self.dut.send_expect('add port tm nonleaf node 1 1000000 -1 0 1 0 0 1 0 0', 'testpmd> ')
        self.dut.send_expect('port tm hierarchy commit 1 no', 'testpmd> ')
        self.dut.send_expect('port start 1', 'testpmd> ')
        self.dut.send_expect('start', 'testpmd> ')
        self.perf_test(4)

    def test_perf_shaping_1port_4tc_i40e(self):
        self.verify(self.kdriver in ["i40e"], "NIC Unsupported: " + str(self.nic))
        self.host_testpmd.start_testpmd("1S/5C/1T", " --nb-cores=4 --txq=4 --rxq=4 --rss-ip ", eal_param=self.eal_param)
        self.shaping_tc_test_i40e(4)

    def test_perf_shaping_1port_8tc_i40e(self):
        self.verify(self.kdriver in ["i40e"], "NIC Unsupported: " + str(self.nic))
        self.host_testpmd.start_testpmd("1S/9C/1T", " --nb-cores=8 --txq=8 --rxq=8 --rss-ip ", eal_param=self.eal_param)
        self.shaping_tc_test_i40e(8)

    def test_dcb_4tc_queue_map_ixgbe(self):
        self.verify(self.kdriver in ["ixgbe"], "NIC Unsupported: " + str(self.nic))
        self.host_testpmd.start_testpmd("1S/5C/1T", " --nb-cores=4 --txq=4 --rxq=4 --disable-rss ", eal_param=self.eal_param)
        self.queue_map_test(4)

    def test_dcb_8tc_queue_map_ixgbe(self):
        self.verify(self.kdriver in ["ixgbe"], "NIC Unsupported: " + str(self.nic))
        self.host_testpmd.start_testpmd("1S/9C/1T", " --nb-cores=8 --txq=8 --rxq=8 --disable-rss ", eal_param=self.eal_param)
        self.queue_map_test(8)

    def test_perf_shaping_1port_4tc_ixgbe(self):
        self.verify(self.kdriver in ["ixgbe"], "NIC Unsupported: " + str(self.nic))
        self.host_testpmd.start_testpmd("1S/5C/1T", " --nb-cores=4 --txq=4 --rxq=4 --disable-rss ", eal_param=self.eal_param)
        self.shaping_tc_test_ixgbe(4)

    def test_perf_shaping_1port_8tc_ixgbe(self):
        self.verify(self.kdriver in ["ixgbe"], "NIC Unsupported: " + str(self.nic))
        self.host_testpmd.start_testpmd("1S/9C/1T", " --nb-cores=8 --txq=8 --rxq=8 --disable-rss ", eal_param=self.eal_param)
        self.shaping_tc_test_ixgbe(8)

    def shaping_tc_test_ixgbe(self, n):
        self.set_dcb(n)
        self.add_root_non_leaf_node()
        self.add_tc_node_ixgbe(n)
        self.add_private_shaper_ixgbe(n)
        self.add_queue_leaf_node_ixgbe(n)
        self.dut.send_expect('port tm hierarchy commit 1 no', 'testpmd> ')
        self.dut.send_expect('start', 'testpmd> ')
        self.perf_test(n)

    def perf_test(self, n):

        dmac = self.dut.get_mac_address(self.dut_ports[0])
        pkts = []
        for i in range(n):
            pkt = 'Ether(dst="%s", src="00:02:00:00:00:01")/Dot1Q(prio=%s)/IP()/("x"*26)' % (dmac, i)
            pkts.append(pkt)
        for i in range(n):
            flow = pkts[i]
            pcap = os.sep.join([self.output_path, "test.pcap"])
            self.tester.scapy_append('wrpcap("%s", [%s])' % (pcap, flow))
            self.tester.scapy_execute()

            tgenInput = []
            pcap = os.sep.join([self.output_path, "test.pcap"])
            tgenInput.append((self.tester.get_local_port(self.dut_ports[0]), self.tester.get_local_port(self.dut_ports[1]), pcap))

            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, None, self.tester.pktgen)
            traffic_opt = {'delay': 10}
            bps, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)
            bps_rate = abs(float(self.bps) - bps)/self.bps
            print "bps_rate", bps_rate
            self.verify(round(self.bps_rate[1] >= bps_rate, 3) >= self.bps_rate[0], 'rx bps is not match 200M')

    def add_queue_leaf_node(self, n):
        for i in range(n):
            self.dut.send_expect('add port tm leaf node 1 %s %s 0 1 2 -1 0 0xffffffff 0 0' % (i, 900000 + i), 'testpmd> ')

    def add_queue_leaf_node_ixgbe(self, n):
        for i in range(n):
            self.dut.send_expect('add port tm leaf node 1 %s %s 0 1 2 0 0 0xffffffff 0 0' % (i, 900000 + i), 'testpmd> ')

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect('quit', '# ')

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
