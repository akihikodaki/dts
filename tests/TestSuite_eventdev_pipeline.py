# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
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
Test eventdev pipeline
"""

import utils
import time
import re
from test_case import TestCase
import scapy.layers.inet
from scapy.utils import rdpcap


class TestEventdevPipeline(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.works = 4
        self.packet_num = 96
        self.core_config = "1S/7C/1T"
        self.build_eventdev_app()

        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")

        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket)
        self.core_list_rx = self.core_list[0:1]
        self.core_list_tx = self.core_list[1:2]
        self.core_list_sd = self.core_list[2:3]
        self.core_list_wk = self.core_list[3:7]
        self.core_mask_rx = utils.create_mask(self.core_list_rx)
        self.core_mask_tx = utils.create_mask(self.core_list_tx)
        self.core_mask_sd = utils.create_mask(self.core_list_sd)
        self.core_mask_wk = utils.create_mask(self.core_list_wk)

        self.core_list = ",".join(self.core_list)
        pre = int(self.core_list[0]) - 1
        self.core_list = str(pre) + "," + self.core_list

        self.rx_port = self.tester.get_local_port(self.dut_ports[0])
        self.tx_port = self.rx_port
        self.rx_interface = self.tester.get_interface(self.rx_port)
        self.tx_interface = self.tester.get_interface(self.tx_port)
        self.d_mac = self.dut.get_mac_address(self.dut_ports[0])

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("killall -s INT eventdev_pipeline", "#")

    def build_eventdev_app(self):
        self.app_command = "examples/eventdev_pipeline"
        out = self.dut.build_dpdk_apps(self.app_command)
        self.verify('make: Leaving directory' in out, "Compilation failed")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def lanuch_eventdev_pipeline(self, cmd_type):
        """
        run eventdev_pipeline command
        """
        command_line = "taskset -c %s " + self.app_command + \
                       "/build/app/eventdev_pipeline " + \
                       "--vdev event_sw0 -- -r%s -t%s -e%s -w %s -s1 -n0 -c32 -W1000 %s -D"
        command_line = command_line % (
                    self.core_list, self.core_mask_rx, self.core_mask_tx,
                    self.core_mask_sd, self.core_mask_wk, cmd_type)
        self.dut.send_expect(command_line, "Port 0", 30)

        out = self.dut.get_session_output()
        self.verify("executing NIC Rx" in out, "lcore of rx not right")
        self.verify("executing NIC Tx" in out, "lcore of tx not right")
        self.verify("executing scheduler" in out, "lcore of scheduler not right")
        self.verify("executing worker" in out, "lcore of worker not right")

    def remove_dhcp_from_revpackets(self, inst):
        pkts = self.tester.load_tcpdump_sniff_packets(inst)
        i = 0
        while len(pkts) != 0 and i <= len(pkts) - 1:
            if pkts[i].pktgen.pkt.haslayer('DHCP'):
                pkts.remove(pkts[i])
                i = i - 1
            i = i + 1
        return pkts

    def send_ordered_packet(self):
        """
        send the packets with ordered of src-ip info
        worker dequeue depth of 32, so the packet number is multiple of 32 is better
        compose the pcap file, each queue has same 5 tuple and diff load info
        eg:
        if only one flow, the pcap has same 5 tuple and the load info from 000001 to 000096
        if has eight flow, the pcap has 8 couples with diff 5 tuple, and each couple load info from
        000001 to 000012
        """
        for queue in range(self.queues):
            src_ip = "11.12.13.%d" % (queue+1)
            pay_load = "000001"
            flow_info = 'flow1 = [Ether(dst="%s",src="%s")/IP(src="%s")/UDP(sport=123, dport=12)/("%s")]'
            self.tester.scapy_append(flow_info % (self.d_mac, self.s_mac, src_ip, pay_load))
            for i in range(1, self.packet_num/self.queues):
                pay_load = "0000%.2d" % (i+1)
                self.tester.scapy_append('flow_temp = [Ether(dst="%s", src="%s")/IP(src="%s")/UDP(sport=123, dport=12)/("%s")]'
                                        % (self.d_mac, self.s_mac, src_ip, pay_load))
                if i == 1:
                    self.tester.scapy_append('flow2 = flow_temp')
                else:
                    self.tester.scapy_append('flow2 = flow2 + flow_temp')
            if queue == 0:
                self.tester.scapy_append('flow = flow1 + flow2')
            else:
                self.tester.scapy_append('flow = flow + flow1 + flow2')

        self.tester.scapy_append('wrpcap("pipeline.pcap", flow)')
        self.tester.scapy_execute()
        time.sleep(5)

        filt = [{'layer': 'ether', 'config': {'src': '%s' % self.s_mac}}]
        inst = self.tester.tcpdump_sniff_packets(self.rx_interface, timeout=15, filters=filt)
        self.tester.scapy_append('pkt=rdpcap("pipeline.pcap")')
        self.tester.scapy_append('sendp(pkt, iface="%s")' % self.tx_interface)
        self.tester.scapy_execute()
        time.sleep(5)
        self.pkts = self.remove_dhcp_from_revpackets(inst)

    def check_packet_order(self):
        """
        observe the packets sended by scapy, check the packets order
        """
        self.send_ordered_packet()
        for queue in range(self.queues):
            src_ip = "11.12.13.%d" % (queue+1)
            packet_index = 0
            for i in range(len(self.pkts)):
                pay_load = "0000%.2d" % (packet_index)
                if self.pkts[i].pktgen.pkt['IP'].src == src_ip:
                    print self.pkts[i].pktgen.pkt.show
                    # get the start index load info of each queue
                    if packet_index == 0:
                        packet_index = int(self.pkts[i].pktgen.pkt['Raw'].load[-2:])
                        pay_load = "0000%.2d" % (packet_index)
                    self.verify(self.pkts[i].pktgen.pkt['Raw'].load == pay_load,
                            "The packets not ordered")
                    packet_index = packet_index + 1

    def test_keep_packet_order_with_ordered_stage(self):
        """
        keep the packets order with one ordered stage in single-flow and multi-flow
        according to the tcpdump may be capture the packets whitch not belong current
        flow, so set different src_mac of flow to identify the packets
        """
        self.lanuch_eventdev_pipeline("-o")
        self.queues = 1
        self.s_mac = "00:00:00:00:00:00"
        self.check_packet_order()
        self.s_mac = "00:00:00:00:00:01"
        self.queues = 8
        self.check_packet_order()

    def test_keep_packet_order_with_default_stage(self):
        """
        keep the packets order with atomic stage in single-flow and multi-flow
        """
        self.lanuch_eventdev_pipeline(" ")
        self.queues = 1
        self.s_mac = "00:00:00:00:00:02"
        self.check_packet_order()
        self.s_mac = "00:00:00:00:00:03"
        self.queues = 8
        self.check_packet_order()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("^c", "#", 10)
        self.dut.send_expect("killall -s INT eventdev_pipeline", "#")
        time.sleep(5)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
