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
import re
import time
from test_case import TestCase
from time import sleep
from settings import HEADER_SIZE
from pmd_output import PmdOutput
from copy import deepcopy
from prettytable import PrettyTable

class TestNicSingleCorePerf(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        PMD prerequisites.
        """

        self.frame_sizes = [64]
        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip'] + HEADER_SIZE['tcp']
        self.ixgbe_descriptors = [128, 512, 2048]
        self.i40e_descriptors = [512, 2048]

        # traffic duraion in second
        self.trafficDuration = 60

        #load the expected throughput for required nic
        self.expected_throughput_nnt = self.parse_string(self.get_suite_cfg()["throughput_nnt"])
        self.expected_throughput_fvl25g = self.parse_string(self.get_suite_cfg()["throughput_fvl25g"])

        # The acdepted gap between expected throughput and actual throughput, 1 Mpps
        self.gap = 1

        # header to print test result table
        self.table_header = ['Frame Size', 'TXD/RXD', 'Throughput', 'Rate', 'Expected Throughput']

        # Update config file and rebuild to get best perf on FVL
        if self.nic in ["fortville_25g"]:
            self.dut.send_expect("sed -i -e 's/CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=n/CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=y/' ./config/common_base", "#", 20)
            self.dut.build_install_dpdk(self.target)

        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports()

        self.socket = self.dut.get_numa_id(self.dut_ports[0])

        self.pmdout = PmdOutput(self.dut)

        self.test_result = {}

        # determine if to save test result as a separated file
        self.save_result_flag =  True

    def set_up(self):
        """
        Run before each test case.
        """
        if self.nic == "niantic":
            self.descriptors = self.ixgbe_descriptors
        elif self.nic in ["fortville_25g"]:
            self.descriptors = self.i40e_descriptors
        else:
            raise Exception("Not required NIC")

    def test_nic_single_core_perf(self):
        """
        Run nic single core performance 
        """
        self.verify(len(self.dut_ports) == 2 or len(self.dut_ports) == 4, "Require 2 or 4 ports to test")
        self.verify(self.nic in ['niantic','fortville_25g'], "Not required NIC ")
        if len(self.dut_ports) == 2:
            self.perf_test(2)   
        elif len(self.dut_ports) == 4:
            self.perf_test(4)

    def perf_test(self, port_num):
        """
        Single core Performance Benchmarking test
        """
        # traffic option
        options = {
             'rate' : '100%',
             #'ip': {'action': 'inc', 'mask' : '255.255.255.0', 'step': '0.0.0.1'}
            }

        header = self.table_header
        if port_num == 2:
            pci0 = self.dut.ports_info[0]['pci']
            pci1 = self.dut.ports_info[1]['pci']
            eal = "-w %s -w %s" % (pci0, pci1)
        elif port_num == 4:
            pci0 = self.dut.ports_info[0]['pci']
            pci1 = self.dut.ports_info[1]['pci']
            pci2 = self.dut.ports_info[2]['pci']
            pci3 = self.dut.ports_info[3]['pci']
            eal = "-w %s -w %s -w %s -w %s" % (pci0, pci1, pci2, pci3)

        # run testpmd with 2 cores
        core_config = "1S/2C/1T"
        core_list = self.dut.get_core_list(core_config, socket=self.socket)
        port_mask = utils.create_mask(self.dut_ports)

        for frame_size in self.frame_sizes:
            ret_datas = {}
            for descriptor in self.descriptors:
                self.logger.info("Executing Test Using cores: %s" % core_list)
                self.pmdout.start_testpmd(core_config, "--portmask=%s --txd=%d --rxd=%d" % (port_mask, descriptor, descriptor),eal, socket=self.socket)
                self.dut.send_expect("start", "testpmd> ", 15)

                self.logger.info("Running with frame size %d " % frame_size)

                # create pcap file
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                        'wrpcap("test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % payload_size)
                self.tester.scapy_execute()

                # send the traffic
                streams = self.prepare_stream(port_num, options)      
                _, packets_received = self.tester.pktgen.measure_throughput(stream_ids=streams, delay=self.trafficDuration)

                throughput = packets_received / 1000000.0

                self.dut.send_expect("stop", "testpmd> ")
                self.dut.send_expect("quit", "# ", 30)

                self.logger.info("Throughput result for Descriptor :%s is :%s Mpps" % (descriptor, throughput))

                wirespeed = self.wirespeed(self.nic, frame_size, port_num)

                # one entry for test result record
                ret_data = {}
                ret_data[header[0]] = frame_size
                ret_data[header[1]] = descriptor
                ret_data[header[2]] = str(float("%.3f" % throughput)) + " Mpps"
                ret_data[header[3]] = str(float("%.3f" % (throughput * 100 / wirespeed))) + "%"
                if self.nic == "niantic":
                    ret_data[header[4]] = self.expected_throughput_nnt[str(frame_size)][str(descriptor)] + " Mpps"
                elif self.nic == "fortville_25g":
                    ret_data[header[4]] = self.expected_throughput_fvl25g[str(frame_size)][str(descriptor)] + " Mpps"
                ret_datas[descriptor] = deepcopy(ret_data)
                self.test_result[frame_size] = deepcopy(ret_datas)
        
        for frame_size in self.frame_sizes:
            for descriptor in self.descriptors:
                self.verify(self.test_result[frame_size][descriptor][header[2]] > 0, "No traffic detected")

        # Print results
        self.result_table_create(header)
        for frame_size in self.frame_sizes:
            for descriptor in self.descriptors:
                table_row = [self.test_result[frame_size][descriptor][header[0]]]
                table_row.append(self.test_result[frame_size][descriptor][header[1]])
                table_row.append(self.test_result[frame_size][descriptor][header[2]])
                table_row.append(self.test_result[frame_size][descriptor][header[3]])
                table_row.append(self.test_result[frame_size][descriptor][header[4]])
                self.result_table_add(table_row)

        self.result_table_print()

        # save test results as a file
        if self.save_result_flag:
            self.save_result(self.test_result)

        # check if the gap between expected throughput and actual throughput exceed accepted gap 
        for frame_size in self.frame_sizes:
            for descriptor in self.descriptors:
                self.verify(float(self.test_result[frame_size][descriptor][header[4]].split()[0]) -
                    float(self.test_result[frame_size][descriptor][header[2]].split()[0]) < self.gap, "Exceeded Gap")

    def prepare_stream(self, port_num, options):
        '''
        create streams for ports, one port one stream
        '''
        if port_num == 2:
            txport0 = self.tester.get_local_port(self.dut.get_ports()[0])
            txport1 = self.tester.get_local_port(self.dut.get_ports()[1])
            stream_id0 = self.tester.pktgen.add_stream(txport0, txport1, r'/root/test.pcap')
            stream_id1 = self.tester.pktgen.add_stream(txport1, txport0, r'/root/test.pcap')
            self.tester.pktgen.config_stream(stream_id0, options)
            self.tester.pktgen.config_stream(stream_id1, options)
            return [stream_id0, stream_id1]
        elif port_num == 4:
            txport0 = self.tester.get_local_port(self.dut.get_ports()[0])
            txport1 = self.tester.get_local_port(self.dut.get_ports()[1])
            txport2 = self.tester.get_local_port(self.dut.get_ports()[2])
            txport3 = self.tester.get_local_port(self.dut.get_ports()[3])
            stream_id0 = self.tester.pktgen.add_stream(txport0, txport1, r'/root/test.pcap')
            stream_id1 = self.tester.pktgen.add_stream(txport1, txport0, r'/root/test.pcap')
            stream_id2 = self.tester.pktgen.add_stream(txport2, txport3, r'/root/test.pcap')
            stream_id3 = self.tester.pktgen.add_stream(txport3, txport2, r'/root/test.pcap')
            self.tester.pktgen.config_stream(stream_id0, options)
            self.tester.pktgen.config_stream(stream_id1, options)
            self.tester.pktgen.config_stream(stream_id2, options)
            self.tester.pktgen.config_stream(stream_id3, options)
            return [stream_id0, stream_id1, stream_id2, stream_id3]

    def save_result(self, data):
        '''
        Saves the test results as a separated file named with self.nic+_single_core_perf.txt
        in output folder if self.save_result_flag is True
        '''
        header = self.table_header
        table = PrettyTable(header)
        for frame_size in self.frame_sizes:
            for descriptor in self.descriptors:
                table_row = [self.test_result[frame_size][descriptor][header[0]]]
                table_row.append(self.test_result[frame_size][descriptor][header[1]])
                table_row.append(self.test_result[frame_size][descriptor][header[2]])
                table_row.append(self.test_result[frame_size][descriptor][header[3]])
                table_row.append(self.test_result[frame_size][descriptor][header[4]])
                table.add_row(table_row)
        file_to_save = open("output/%s_single_core_perf.txt" % self.nic, 'w')
        file_to_save.write(str(table))
        file_to_save.close()

    def parse_string(self, string):
        '''
        Parse a string in the formate of a dictionary and convert it into a real dictionary. 
        '''
        element_pattern = re.compile(".\d+:.*?}")
        string_elements = element_pattern.findall(string)
        ret = {}
        for element in string_elements:
            ex_pattern = re.compile("(\d+): *{(.*)}")
            ex_ret = ex_pattern.search(element)
            ret[ex_ret.groups()[0]] = ex_ret.groups()[1]
            inner_datas = ex_ret.groups()[1].split(",")
            ret_inner = {}
            for data in inner_datas:
                match_inner = data.split(":")
                ret_inner[match_inner[0].strip()] = match_inner[1].strip()
            ret[ex_ret.groups()[0]] = deepcopy(ret_inner)
        return ret

    def tear_down(self):
        """
        Run after each test case.
        """
        if self.nic in ["fortville_25g"]:
            self.dut.send_expect("sed -i -e 's/CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=y/CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=n/' ./config/common_base", "#", 20)    

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
