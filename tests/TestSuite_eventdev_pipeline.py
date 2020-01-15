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
from packet import Packet


class TestEventdevPipeline(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.works = 4
        self.packet_num = 96
        self.core_config = "1S/8C/1T"
        self.build_eventdev_app()

        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")

        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket)
        self.verify(len(self.core_list) >= 8, 'sever no enough cores to run this suite')
        self.core_list_rx = self.core_list[1:2]
        self.core_list_tx = self.core_list[2:3]
        self.core_list_sd = self.core_list[3:4]
        self.core_list_wk = self.core_list[4:8]
        self.core_mask_rx = utils.create_mask(self.core_list_rx)
        self.core_mask_tx = utils.create_mask(self.core_list_tx)
        self.core_mask_sd = utils.create_mask(self.core_list_sd)
        self.core_mask_wk = utils.create_mask(self.core_list_wk)

        self.taskset_core_list = ",".join(self.core_list)

        self.rx_port = self.tester.get_local_port(self.dut_ports[0])
        self.tx_port = self.rx_port
        self.rx_interface = self.tester.get_interface(self.rx_port)
        self.tx_interface = self.tester.get_interface(self.tx_port)
        self.d_mac = self.dut.get_mac_address(self.dut_ports[0])

    def set_up(self):
        """
        Run before each test case.
        """
        pass

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
        eal_params = self.dut.create_eal_parameters(cores=self.core_list,
                    ports=[self.dut.ports_info[0]['pci']])
        command_line = "taskset -c %s " + self.app_command + \
                       "/build/app/eventdev_pipeline %s " + \
                       "--vdev event_sw0 -- -r%s -t%s -e%s -w %s -s1 -n0 -c32 -W1000 %s -D"
        command_line = command_line % (
                    self.taskset_core_list, eal_params, self.core_mask_rx,
                    self.core_mask_tx, self.core_mask_sd, self.core_mask_wk, cmd_type)
        self.dut.send_expect(command_line, "Port 0", 30)

        out = self.dut.get_session_output()
        self.verify("executing NIC Rx" in out, "lcore of rx not right")
        self.verify("executing NIC Tx" in out, "lcore of tx not right")
        self.verify("executing scheduler" in out, "lcore of scheduler not right")
        self.verify("executing worker" in out, "lcore of worker not right")

    def remove_dhcp_from_revpackets(self, inst, timeout=3):
        pkts = self.tester.load_tcpdump_sniff_packets(inst, timeout)
        i = 0
        while len(pkts) != 0 and i <= len(pkts) - 1:
            if pkts[i].haslayer('DHCP'):
                pkts.pktgen.pkts.pop(i)
                i = i - 1
            i = i + 1
        return pkts

    def send_ordered_packet(self, count=1):
        """
        send the packets with ordered of src-ip info
        worker dequeue depth of 32, so the packet number is multiple of 32 is better
        compose the pcap file, each queue has same 5 tuple and diff load info
        eg:
        if only one flow, the pcap has same 5 tuple and the load info from 000001 to 000096
        if has eight flow, the pcap has 8 couples with diff 5 tuple, and each couple load info from
        000001 to 000012
        """
        pkt = Packet()
        for queue in range(self.queues):
            config_opt = [('ether', {'dst': self.d_mac, 'src': self.s_mac, 'src': self.s_mac}),
                        ('ipv4', {'src': '11.12.13.%d' % (queue+1), 'dst': '11.12.1.1'}),
                        ('udp', {'src': 123, 'dst': 12})]
            # if only one queue, create self.packet_num with same 5 tuple
            # if multi queue, create self.packet_num with diff 5 tuple,
            # each tuple have (self.packet_num//self.queues) pkts
            pkt_num = self.packet_num//self.queues
            pkt.generate_random_pkts(pktnum=pkt_num, random_type=['UDP'], ip_increase=False,
                                random_payload=False, options={'layers_config': config_opt})
            # config raw info in pkts
            for i in range(pkt_num):
                payload = "0000%.2d" % (i+1)
                pkt.pktgen.pkts[i + pkt_num*queue]['Raw'].load = payload

        filt = [{'layer': 'ether', 'config': {'src': '%s' % self.s_mac}}]
        inst = self.tester.tcpdump_sniff_packets(self.rx_interface, filters=filt)
        pkt.send_pkt(crb=self.tester, tx_port=self.tx_interface, count=count, timeout=300)
        self.pkts = self.remove_dhcp_from_revpackets(inst)

    def check_load_balance_behavior(self, case_info):
        """
        check the load-balance bahavior by the workload of every worker
        the send pkts number is 96*100, and each worker received pkts number should
        smaller than 2760 and greather than 2040
        """
        self.send_ordered_packet(count=100)
        # exit the eventdev_pipeline app
        # and get the output info
        self.dut.send_expect('^c', 'Signal')
        out = self.dut.get_session_output(timeout=3)
        work_rx = []
        for wk in self.core_list_wk:
            one_info = re.search('worker\s*%s\s*thread done.\s*RX=(\d*)\s*TX=(\d*)' % str(wk), out)
            self.verify(one_info is not None and len(one_info.groups()) == 2
                        and int(one_info.group(1)) > 0,
                        "%s can not get the worker rx and tx packets info from output" % case_info)
            work_info = {'work': int(wk), 'rx': int(one_info.group(1)), 'tx': int(one_info.group(2))}
            work_rx.append(work_info)
        # get all received pkts
        all_rx = 0
        for wk in work_rx:
            all_rx += wk['rx']
        ave_rx = all_rx//len(work_rx)
        for wk in work_rx:
            self.verify(wk['rx'] <= ave_rx + ave_rx*0.15 and wk['rx'] >= ave_rx - ave_rx*0.15,
                '%s : the work thread rx is not balance, all_rx: %d, work %d rx is %d' % (
                case_info, all_rx, wk['work'], wk['rx']))
            self.logger.info('%s : worker thread %d received %d pkts' % (case_info, wk['work'], wk['rx']))

    def check_packet_order(self, case_info):
        """
        observe the packets sended by scapy, check the packets order
        """
        self.send_ordered_packet()
        for queue in range(self.queues):
            src_ip = "11.12.13.%d" % (queue+1)
            packet_index = 0
            for i in range(len(self.pkts)):
                pay_load = "0000%.2d" % (packet_index)
                if self.pkts[i]['IP'].src == src_ip:
                    print((self.pkts[i].show))
                    # get the start index load info of each queue
                    if packet_index == 0:
                        packet_index = int(self.pkts[i]['Raw'].load[-2:])
                        pay_load = "0000%.2d" % (packet_index)
                    rev_pkt_load = self.pkts[i]['Raw'].load
                    if isinstance(self.pkts[i]['Raw'].load, bytes):
                        rev_pkt_load = str(self.pkts[i]['Raw'].load, encoding='utf-8')
                    self.verify(rev_pkt_load == pay_load,
                            "%s : The packets not ordered" % case_info)
                    packet_index = packet_index + 1

    def test_keep_packet_order_with_ordered_stage(self):
        """
        keep the packets order with one ordered stage in single-flow and multi-flow
        according to the tcpdump may be capture the packets whitch not belong current
        flow, so set different src_mac of flow to identify the packets
        """
        self.logger.info('check keep packet order about single-flow')
        self.lanuch_eventdev_pipeline("-o")
        self.queues = 1
        self.s_mac = "00:00:00:00:00:00"
        self.check_packet_order('single-flow')
        self.logger.info('check keep packet order about multi-flow')
        self.s_mac = "00:00:00:00:00:01"
        self.queues = 8
        self.check_packet_order('multi-flow')

    def test_keep_packet_order_with_default_stage(self):
        """
        keep the packets order with atomic stage in single-flow and multi-flow
        """
        self.logger.info('check keep packet order about single-flow')
        self.lanuch_eventdev_pipeline(" ")
        self.queues = 1
        self.s_mac = "00:00:00:00:00:02"
        self.check_packet_order('single-flow')
        self.logger.info('check keep packet order about multi-flow')
        self.s_mac = "00:00:00:00:00:03"
        self.queues = 8
        self.check_packet_order('multi-flow')

    def test_check_load_balance_behavior_with_default_type(self):
        """
        Check load-balance behavior with default type in single-flow and multi-flow situations
        """
        self.logger.info('check load balance about single-flow')
        self.lanuch_eventdev_pipeline(" ")
        self.queues = 1
        self.s_mac = "00:00:00:00:00:04"
        self.check_load_balance_behavior('single-flow')

        self.logger.info('check load balance about multi-flow')
        self.lanuch_eventdev_pipeline(" ")
        self.queues = 8
        self.s_mac = "00:00:00:00:00:05"
        self.check_load_balance_behavior('multi-flow')

    def test_check_load_balance_behavior_with_order_type(self):
        """
        Check load-balance behavior with order type stage in single-flow and multi-flow situations
        """
        self.logger.info('check load balance about single-flow')
        self.lanuch_eventdev_pipeline("-o")
        self.queues = 1
        self.s_mac = "00:00:00:00:00:06"
        self.check_load_balance_behavior('single-flow')

        self.logger.info('check load balance about multi-flow')
        self.lanuch_eventdev_pipeline("-o")
        self.queues = 8
        self.s_mac = "00:00:00:00:00:07"
        self.check_load_balance_behavior('multi-flow')

    def test_check_load_balance_behavior_with_parallel_type(self):
        """
        Check load-balance behavior with parallel type stage in single-flow and multi-flow situations
        """
        self.logger.info('check load balance about single-flow')
        self.lanuch_eventdev_pipeline("-p")
        self.queues = 1
        self.s_mac = "00:00:00:00:00:08"
        self.check_load_balance_behavior('single-flow')

        self.logger.info('check load balance about multi-flow')
        self.lanuch_eventdev_pipeline("-p")
        self.queues = 8
        self.s_mac = "00:00:00:00:00:09"
        self.check_load_balance_behavior('multi-flow')

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        time.sleep(5)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
