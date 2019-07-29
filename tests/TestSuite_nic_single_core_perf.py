#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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
import json
import os
import re
import time
from test_case import TestCase
from time import sleep
from exception import VerifyFailure
from settings import HEADER_SIZE, UPDATE_EXPECTED, load_global_setting
from pmd_output import PmdOutput
from pktgen import TRANSMIT_CONT
from copy import deepcopy
from prettytable import PrettyTable
import rst


class TestNicSingleCorePerf(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        PMD prerequisites.
        """
        self.verify(self.nic in ['niantic', 'fortville_25g', 'fortville_spirit',
                                 'ConnectX5_MT4121', 'ConnectX4_LX_MT4117'],
                                 "Not required NIC ")

        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip']

        # Update DPDK config file and rebuild to get best perf on fortville
        if self.nic in ["fortville_25g", "fortville_spirit"]:
            self.dut.send_expect(
                "sed -i -e 's/CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=n/CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=y/' ./config/common_base", "#", 20)
            self.dut.build_install_dpdk(self.target)

        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports()
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.pmdout = PmdOutput(self.dut)

        # determine if to save test result as a separated file
        self.save_result_flag = True

    def set_up(self):
        """
        Run before each test case.
        It's more convenient to load suite configuration here than
        set_up_all in debug mode.
        """

        # test parameters include: frames size, descriptor numbers
        self.test_parameters = self.get_suite_cfg()['test_parameters']

        # traffic duraion in second
        self.test_duration = self.get_suite_cfg()['test_duration']

        # load the expected throughput for required nic
        if self.nic in ["ConnectX4_LX_MT4117"]:
            nic_speed = self.dut.ports_info[0]['port'].get_nic_speed()
            if nic_speed == "25000":
                self.expected_throughput = self.get_suite_cfg(
                )['expected_throughput'][self.nic]['25G']
            else:
                self.expected_throughput = self.get_suite_cfg(
                )['expected_throughput'][self.nic]['40G']
        else:
            self.expected_throughput = self.get_suite_cfg()[
                'expected_throughput'][self.nic]

        # initilize throughput attribution
        # {'$framesize':{"$nb_desc": 'throughput'}
        self.throughput = {}

        # Accepted tolerance in Mpps
        self.gap = self.get_suite_cfg()['accepted_tolerance']

        # header to print test result table
        self.table_header = ['Frame Size', 'TXD/RXD', 'Throughput', 'Rate',
                             'Expected Throughput', 'Throughput Difference']
        self.test_result = {}

    def test_perf_nic_single_core(self):
        """
        Run nic single core performance 
        """
        self.nb_ports = len(self.dut_ports)
        self.verify(self.nb_ports == 2 or self.nb_ports == 4,
                    "Require 2 or 4 ports to test")
        self.perf_test(self.nb_ports)
        self.handle_results()

        # check the gap between expected throughput and actual throughput
        try:
            for frame_size in self.test_parameters.keys():
                for nb_desc in self.test_parameters[frame_size]:
                    cur_gap = (self.expected_throughput[frame_size][nb_desc] -
                                self.throughput[frame_size][nb_desc])
                    self.verify(cur_gap < self.gap,
                                 "Beyond Gap, Possible regression")
        except Exception as e:
            self.logger.error(e)
            self.handle_expected()
            raise VerifyFailure(
                "Possible regression, Check your configuration please")
        else:
            self.handle_expected()

    def handle_expected(self):
        """
        Update expected numbers to configurate file: conf/$suite_name.cfg
        """
        if load_global_setting(UPDATE_EXPECTED) == "yes":
            for frame_size in self.test_parameters.keys():
                for nb_desc in self.test_parameters[frame_size]:
                    self.expected_throughput[frame_size][nb_desc] = \
                        round(self.throughput[frame_size][nb_desc],3)

    def perf_test(self, port_num):
        """
        Single core Performance Benchmarking test
        """
        # ports whitelist
        eal_para = ""
        for i in range(self.nb_ports):
            eal_para += " -w " + self.dut.ports_info[i]['pci']

        # run testpmd with 2 cores, one for interaction ,and one for forwarding
        core_config = "1S/2C/1T"
        core_list = self.dut.get_core_list(core_config, socket = self.socket)
        self.logger.info("Executing Test Using cores: %s" % core_list)
        port_mask = utils.create_mask(self.dut_ports)

        # parameters for application/testpmd
        param = " --portmask=%s" % (port_mask)
        # fortville has to use 2 queues at least to get the best performance
        if self.nic in ["fortville_25g", "fortville_spirit"]:
            param += " --rxq=2 --txq=2"

        for frame_size in self.test_parameters.keys():
            self.throughput[frame_size] = dict()
            for nb_desc in self.test_parameters[frame_size]:
                self.logger.info("Test running at parameters: " +
                    "framesize: {}, rxd/txd: {}".format(frame_size, nb_desc))
                parameter = param + " --txd=%d --rxd=%d" % (nb_desc, nb_desc)
                self.pmdout.start_testpmd(
                    core_config, parameter, eal_para, socket = self.socket)
                self.dut.send_expect("start", "testpmd> ", 15)

                # measure throughput
                stream_ids = self.prepare_stream(frame_size)
                traffic_opt = {'delay': self.test_duration}
                _, packets_received = self.tester.pktgen.measure_throughput(
                    stream_ids, traffic_opt)
                throughput = packets_received / 1000000.0
                self.throughput[frame_size][nb_desc] = throughput

                self.dut.send_expect("stop", "testpmd> ")
                self.dut.send_expect("quit", "# ", 30)

                self.verify(throughput,
                    "No traffic detected, please check your configuration")
                self.logger.info("Trouthput of " +
                    "framesize: {}, rxd/txd: {} is :{} Mpps".format(
                        frame_size, nb_desc, throughput))

        return self.throughput

    def handle_results(self):
        """
        results handled process:
        1, save to self.test_results
        2, create test results table
        3, save to json file for Open Lab
        """

        # save test results to self.test_result
        header = self.table_header
        for frame_size in self.test_parameters.keys():
            wirespeed = self.wirespeed(self.nic, frame_size, self.nb_ports)
            ret_datas = {}
            for nb_desc in self.test_parameters[frame_size]:
                ret_data = {}
                ret_data[header[0]] = frame_size
                ret_data[header[1]] = nb_desc
                ret_data[header[2]] = "{:.3f} Mpps".format(
                    self.throughput[frame_size][nb_desc])
                ret_data[header[3]] = "{:.3f}%".format(
                    self.throughput[frame_size][nb_desc] * 100 / wirespeed)
                ret_data[header[4]] = "{:.3f} Mpps".format(
                    self.expected_throughput[frame_size][nb_desc])
                ret_data[header[5]] = "{:.3f} Mpps".format(
                    self.throughput[frame_size][nb_desc] -
                        self.expected_throughput[frame_size][nb_desc])

                ret_datas[nb_desc] = deepcopy(ret_data)
            self.test_result[frame_size] = deepcopy(ret_datas)

        # Create test results table
        self.result_table_create(header)
        for frame_size in self.test_parameters.keys():
            for nb_desc in self.test_parameters[frame_size]:
                table_row = list()
                for i in range(len(header)):
                    table_row.append(
                        self.test_result[frame_size][nb_desc][header[i]])
                self.result_table_add(table_row)
        # present test results to screen
        self.result_table_print()

        # save test results as a file
        if self.save_result_flag:
            self.save_result(self.test_result)

    def prepare_stream(self, frame_size):
        '''
        create streams for ports, one port two streams, and configure them.
        '''
        # create pcap file
        payload_size = frame_size - self.headers_size
        self.tester.scapy_append(
            'wrpcap("/tmp/test0.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/("X"*%d)])' % payload_size)
        self.tester.scapy_append(
            'wrpcap("/tmp/test1.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="2.2.3.4",dst="1.1.1.1")/("X"*%d)])' % payload_size)
        self.tester.scapy_execute()

        stream_ids = []
        for i in range(self.nb_ports):
            if i % 2 == 0:
                txport = self.tester.get_local_port(self.dut.get_ports()[i])
                rxport = self.tester.get_local_port(
                    self.dut.get_ports()[i + 1])

                # fortville requires 2 streams for 2 queues at least, and
                # this's fine for other NIC too.
                for k in range(2):
                    # txport -> rxport
                    pcap = '/tmp/test{}.pcap'.format(k)
                    options = {
                        'pcap': pcap,
                        'stream_config':{
                            'txmode' : {},
                            'transmit_mode': TRANSMIT_CONT,
                            'rate': 100,}}
                    stream_id = self.tester.pktgen.add_stream(
                        txport, rxport, '/tmp/test{}.pcap'.format(k))
                    self.tester.pktgen.config_stream(stream_id, options)
                    stream_ids.append(stream_id)
                    # rxport -> txport
                    stream_id = self.tester.pktgen.add_stream(
                        rxport, txport, '/tmp/test{}.pcap'.format(k))
                    self.tester.pktgen.config_stream(stream_id, options)
                    stream_ids.append(stream_id)

        return stream_ids

    def save_result(self, data):
        '''
        Saves the test results as a separated file named with
        self.nic+_single_core_perf.json in output folder
        if self.save_result_flag is True
        '''
        json_obj = dict()
        json_obj['nic_type'] = self.nic
        json_obj['results'] = list()
        for frame_size in self.test_parameters.keys():
            for nb_desc in self.test_parameters[frame_size]:
                row_in = self.test_result[frame_size][nb_desc]
                row_dict = dict()
                row_dict['parameters'] = dict()
                row_dict['parameters']['frame_size'] = dict(
                    value = row_in['Frame Size'], unit = 'bytes')
                row_dict['parameters']['txd/rxd'] = dict(
                    value = row_in['TXD/RXD'], unit = 'descriptors')
                delta = (float(row_in['Throughput'].split()[0]) -
                         float(row_in['Expected Throughput'].split()[0]))
                if delta >= -self.gap:
                    result = 'PASS'
                else:
                    result = 'FAIL'
                row_dict['throughput'] = dict(
                    delta = delta, unit = row_in['Throughput'].split()[1],
                    result = result)
                json_obj['results'].append(row_dict)
        with open(os.path.join(rst.path2Result,
                               '{0:s}_single_core_perf.json'.format(
                                   self.nic)), 'w') as fp:
            json.dump(json_obj, fp)

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        # resume setting
        if self.nic in ["fortville_25g", "fortville_spirit"]:
            self.dut.send_expect(
                "sed -i -e 's/CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=y/CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=n/' ./config/common_base", "#", 20)
            self.dut.build_install_dpdk(self.target)

        self.dut.kill_all()
