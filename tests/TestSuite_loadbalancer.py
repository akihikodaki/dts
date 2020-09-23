# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
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

Test Load Balancer.

"""

import dts
from packet import Packet
from test_case import TestCase
import utils
import time


class TestLoadbalancer(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.

        Load Balancer prerequisites.
        """
        # Verify that enough ports are available
        global dutPorts
        # Based on h/w type, choose how many ports to use
        dutPorts = self.dut.get_ports(self.nic)

        # Verify that enough ports are available
        self.verify(len(dutPorts) >= 4, "Insufficient ports for testing")

        cores = self.dut.get_core_list("all")
        self.verify(len(cores) >= 5, "Insufficient cores for testing")
        self.cores = self.dut.get_core_list("1S/5C/1T")
        self.coremask = utils.create_mask(self.cores)

        global rx_port0, rx_port1, rx_port2, rx_port3, trafficFlow
        rx_port0 = self.tester.get_local_port(dutPorts[0])
        rx_port1 = self.tester.get_local_port(dutPorts[1])
        rx_port2 = self.tester.get_local_port(dutPorts[2])
        rx_port3 = self.tester.get_local_port(dutPorts[3])

        """
        Designation the traffic flow is the same as LPM rules, send and receive packet verification:
            0: 1.0.0.0/24 => 0;
            1: 1.0.1.0/24 => 1;
            2: 1.0.2.0/24 => 2;
            3: 1.0.3.0/24 => 3;
        """
        trafficFlow = {
            "Flow1": [rx_port0, "1.0.0.1"],
            "Flow2": [rx_port1, "1.0.1.1"],
            "Flow3": [rx_port2, "1.0.2.1"],
            "Flow4": [rx_port3, "1.0.3.1"],
        }

        out = self.dut.build_dpdk_apps("examples/load_balancer")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_load_balancer(self):
        """
        --rx: Set the receive port, queue and main core;
        --tx: Set the send port and main core;
        --w: specify 4 workers lcores,
        --lpm: IPv4 routing table,
        --bsz: The number of packet is 10 for transceivers,
        --pos-lb: Position of the 1-byte header field within the input packet that is used to
        determine the worker ID for each packet
        """

        cmd = './examples/load_balancer/build/load_balancer -l {0}-{1} -n 4 -- --rx "(0,0,{2}),(1,0,{2}),(2,0,{2}),(3,0,{2})" '\
              '--tx "(0,{2}),(1,{2}),(2,{2}),(3,{2})" --w "{3},{4},{5},{6}" '\
              '--lpm "1.0.0.0/24=>0;1.0.1.0/24=>1;1.0.2.0/24=>2;1.0.3.0/24=>3;" '\
              '--bsz "(10, 10), (10, 10), (10, 10)" --pos-lb 29'.format(self.cores[0], self.cores[4], self.cores[0], self.cores[1], self.cores[2], self.cores[3], self.cores[4])

        self.dut.send_expect(cmd, 'main loop.')

        # Verify the traffic flow according to Ipv4 route table
        for flow in list(trafficFlow.keys()):
            rx_port = trafficFlow[flow][0]

            for i in range(len(dutPorts)):
                dstport = self.tester.get_local_port(dutPorts[i])
                pkt_count = 10
                inst = self.tester.tcpdump_sniff_packets(intf=self.tester.get_interface(rx_port), count=pkt_count)

                pkt = Packet(pkt_type='UDP', pkt_len=64)
                dst_mac = self.dut.get_mac_address(dutPorts[i])
                pkt.config_layer('ether', {'dst': '%s' % dst_mac})
                pkt.config_layer('ipv4', {'src': "0.0.0.1", 'dst': '%s' % (trafficFlow[flow][1])})
                pkt.send_pkt(self.tester, tx_port=self.tester.get_interface(dstport), count=10)
                # Wait for the sniffer to finish.
                time.sleep(5)

                pkts = self.tester.load_tcpdump_sniff_packets(inst)
                len_pkts = len(pkts)

                self.verify(len_pkts == pkt_count, "Packet number is wrong")
                for i in range(len_pkts):
                    result = str(pkts[i].show)
                    self.verify("Ether" in result, "No packet received")
                    self.verify("src=0.0.0.1" + " dst=" + trafficFlow[flow][1] in result, "Wrong IP address")
                    self.verify("dst=%s" % dst_mac in result, "No packet received or packet missed")

        self.dut.send_expect("^C", "#")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
