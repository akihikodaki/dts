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
Test userland 10Gb/25Gb/40Gb/100Gb
"""

import utils
import re
import time
import os

from test_case import TestCase
from time import sleep
from settings import HEADER_SIZE
from pmd_output import PmdOutput
from etgen import IxiaPacketGenerator

from settings import FOLDERS
from system_info import SystemInfo
import perf_report
from datetime import datetime

class TestEventdevPerf(TestCase,IxiaPacketGenerator):

    def set_up_all(self):
        """
        Run at the start of each test suite.

        PMD prerequisites.
        """
        self.tester.extend_external_packet_generator(TestEventdevPerf, self)

        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]

        self.rxfreet_values = [0, 8, 16, 32, 64, 128]

        self.test_cycles = [
                        {'cores': '1S/2C/1T', 'Mpps': {}, 'pct': {}},
                        {'cores': '1S/3C/1T', 'Mpps': {}, 'pct': {}},
                        {'cores': '1S/5C/1T', 'Mpps': {}, 'pct': {}},
                        {'cores': '1S/9C/1T', 'Mpps': {}, 'pct': {}},
                        {'cores': '1S/17C/1T', 'Mpps': {}, 'pct': {}},
                        ]
        self.get_cores_from_last = True
        self.table_header = ['Frame Size']
        for test_cycle in self.test_cycles:
            m = re.search(r"(\d+S/)(\d+)(C/\d+T)",test_cycle['cores'])
            cores = m.group(1) + str(int(m.group(2))-1) + m.group(3)
            self.table_header.append("%s Mpps" % cores)
            self.table_header.append("% linerate")

        self.perf_results = {'header': [], 'data': []}

        self.blacklist = ""

        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports()
        if self.dut.get_os_type() == 'linux':
            # Get dut system information
            port_num = self.dut_ports[0]
            pci_device_id = self.dut.ports_info[port_num]['pci']
            ori_driver = self.dut.ports_info[port_num]['port'].get_nic_driver()
            self.dut.ports_info[port_num]['port'].bind_driver()

            self.dut.ports_info[port_num]['port'].bind_driver(ori_driver)

        if self.nic == "cavium_a063":
            self.eventdev_device_bus_id = "0002:0e:00.0"
            self.eventdev_device_id = "a0f9"

        #### Bind evendev device ####
            self.dut.bind_eventdev_port(port_to_bind=self.eventdev_device_bus_id)

        #### Configuring evendev SS0 & SSOw limits ####
            self.dut.set_eventdev_port_limits(self.eventdev_device_id, self.eventdev_device_bus_id)

        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE[
            'ip'] + HEADER_SIZE['tcp']

        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])

        self.pmdout = PmdOutput(self.dut)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def eventdev_cmd(self, test_type, stlist, nports, worker_cores):

        self.Port_pci_ids = []
        command_line1 = "dpdk-test-eventdev -l %s -w %s"
        for i in range(0, nports):
            self.Port_pci_ids.append(self.dut.ports_info[i]['pci'])
            ## Adding core-list and pci-ids
            command_line1 = command_line1 + " -w %s "
        ## Adding test and stage types
        command_line2 = "-- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=%s --stlist=%s --wlcores=%s" %(test_type, stlist, worker_cores)
        return command_line1 + command_line2

    def test_perf_eventdev_1ports_atq_atomic_performance(self):
        """
        Evendev Performance Benchmarking with 1 ports with test_type=pipeline_atq and schedule_type=atomic.
        """

        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for 1 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_atq", "A", 1, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 1)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_1ports_atq_parallel_performance(self):
        """
        Evendev Performance Benchmarking with 1 ports with test_type=pipeline_atq and schedule_type=parallel.
        """
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for 1 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_atq", "P", 1, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 1)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_1ports_atq_order_performance(self):
        """
        Evendev Performance Benchmarking with 1 ports with test_type=pipeline_atq and schedule_type=order.
        """

        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for 1 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_atq", "O", 1, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 1)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_1ports_queue_atomic_performance(self):
        """
        Evendev Performance Benchmarking with 1 ports with test_type=pipeline_queue and schedule_type=atomic.
        """

        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for 1 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_queue", "A", 1, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 1)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_1ports_queue_parallel_performance(self):
        """
        Evendev Performance Benchmarking with 1 ports with test_type=pipeline_queue and schedule_type=parallel.
        """

        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for 1 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_queue", "P", 1, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 1)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_1ports_queue_order_performance(self):
        """
        Evendev Performance Benchmarking with 1 ports with test_type=pipeline_queue and schedule_type=order.
        """

        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for 1 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_queue", "O", 1, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 1)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_2ports_atq_atomic_performance(self):
        """
        Evendev Performance Benchmarking with 2 ports with test_type=pipeline_atq and schedule_type=atomic.
        """

        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for 2 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_atq", "A", 2, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 2)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_2ports_atq_parallel_performance(self):
        """
        Evendev Performance Benchmarking with 2 ports with test_type=pipeline_atq and schedule_type=parallel.
        """

        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for 2 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_atq", "P", 2, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 2)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_2ports_atq_order_performance(self):
        """
        Evendev Performance Benchmarking with 2 ports with test_type=pipeline_atq and schedule_type=order.
        """

        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for 2 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_atq", "O", 2, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 2)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_2ports_queue_atomic_performance(self):
        """
        Evendev Performance Benchmarking with 2 ports with test_type=pipeline_queue and schedule_type=atomic.
        """

        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for 2 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_queue", "A", 2, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 2)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_2ports_queue_parallel_performance(self):
        """
        Evendev Performance Benchmarking with 2 ports with test_type=pipeline_queue and schedule_type=parallel.
        """

        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for 2 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_queue", "P", 2, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 2)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_2ports_queue_order_performance(self):
        """
        Evendev Performance Benchmarking with 2 ports with test_type=pipeline_queue and schedule_type=order.
        """

        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for 2 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_queue", "O", 2, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 2)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()


    def test_perf_eventdev_4ports_atq_atomic_performance(self):
        """
        Evendev Performance Benchmarking with 4 ports with test_type=pipeline_atq and schedule_type=atomic.
        """

        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for 4 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[2]),
                           self.tester.get_local_port(self.dut_ports[3]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[3]),
                           self.tester.get_local_port(self.dut_ports[2]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_atq", "A", 4, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1], self.Port_pci_ids[2], self.Port_pci_ids[3])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 4)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")
        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_4ports_atq_parallel_performance(self):
        """
        Evendev Performance Benchmarking with 4 ports with test_type=pipeline_atq and schedule_type=parallel.
        """

        self.verify(len(self.dut_ports) >= 4, "Insufficient ports for 4 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[2]),
                           self.tester.get_local_port(self.dut_ports[3]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[3]),
                           self.tester.get_local_port(self.dut_ports[2]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_atq", "P", 4, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1], self.Port_pci_ids[2], self.Port_pci_ids[3])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 4)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_4ports_atq_order_performance(self):
        """
        Evendev Performance Benchmarking with 4 ports with test_type=pipeline_atq and schedule_type=order.
        """

        self.verify(len(self.dut_ports) >= 4, "Insufficient ports for 4 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[2]),
                           self.tester.get_local_port(self.dut_ports[3]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[3]),
                           self.tester.get_local_port(self.dut_ports[2]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_atq", "O", 4, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1], self.Port_pci_ids[2], self.Port_pci_ids[3])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 4)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_4ports_queue_atomic_performance(self):
        """
        Evendev Performance Benchmarking with 4 ports with test_type=pipeline_queue and schedule_type=atomic.
        """

        self.verify(len(self.dut_ports) >= 4, "Insufficient ports for 4 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[2]),
                           self.tester.get_local_port(self.dut_ports[3]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[3]),
                           self.tester.get_local_port(self.dut_ports[2]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_queue", "A", 4, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1], self.Port_pci_ids[2], self.Port_pci_ids[3])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 4)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_4ports_queue_parallel_performance(self):
        """
        Evendev Performance Benchmarking with 4 ports with test_type=pipeline_queue and schedule_type=parallel.
        """

        self.verify(len(self.dut_ports) >= 4, "Insufficient ports for 4 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[2]),
                           self.tester.get_local_port(self.dut_ports[3]),
                          "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[3]),
                          self.tester.get_local_port(self.dut_ports[2]),
                           "event_test.pcap"))
        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_queue", "P", 4, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1], self.Port_pci_ids[2], self.Port_pci_ids[3])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 4)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def test_perf_eventdev_4ports_queue_order_performance(self):
        """
        Evendev Performance Benchmarking with 4 ports with test_type=pipeline_queue and schedule_type=order.
        """

        self.verify(len(self.dut_ports) >= 4, "Insufficient ports for 4 ports performance test")
        self.perf_results['header'] = []
        self.perf_results['data'] = []

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        tgen_input.append((self.tester.get_local_port(self.dut_ports[0]),
                           self.tester.get_local_port(self.dut_ports[1]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[2]),
                           self.tester.get_local_port(self.dut_ports[3]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[1]),
                           self.tester.get_local_port(self.dut_ports[0]),
                           "event_test.pcap"))
        tgen_input.append((self.tester.get_local_port(self.dut_ports[3]),
                           self.tester.get_local_port(self.dut_ports[2]),
                           "event_test.pcap"))

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']

            core_list = self.dut.get_core_list(core_config,
                                               socket=self.ports_socket, from_last = self.get_cores_from_last)
            cores_list = "%s-%s" % (core_list[0],core_list[-1])

            if len(core_list) > 2:
                worker_cores = "%s-%s" %(core_list[1],core_list[-1])
            else:
                worker_cores = core_list[-1]

            command_line = self.eventdev_cmd( "pipeline_queue", "O", 4, worker_cores)
            command_line = command_line %(cores_list, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1], self.Port_pci_ids[2], self.Port_pci_ids[3])
            self.dut.send_expect(command_line,"Configured", 100)

            info = "Executing Eventdev using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 4)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("event_test.pcap", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])' % (payload_size))
                self.tester.scapy_execute()

                # run traffic generator
                _, pps = self.tester.traffic_generator_throughput(tgen_input, rate_percent=100, delay=60)
                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle['Mpps'][frame_size] = float('%.3f' % pps)
                test_cycle['pct'][frame_size] = float('%.3f' % pct)

            self.dut.send_expect("^C", "# ", 50)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            frame_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results['header'] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][frame_size])
                table_row.append(test_cycle['pct'][frame_size])

            self.result_table_add(table_row)
            self.perf_results['data'].append(table_row)

        self.result_table_print()

    def ip(self, port, frag, src, proto, tos, dst, chksum, len, options, version, flags, ihl, ttl, id):
        self.add_tcl_cmd("protocol config -name ip")
        self.add_tcl_cmd('ip config -sourceIpAddr "%s"' % src)
        self.add_tcl_cmd("ip config -sourceIpAddrMode ipIncrHost")
        self.add_tcl_cmd("ip config -sourceIpAddrRepeatCount 100")
        self.add_tcl_cmd('ip config -destIpAddr "%s"' % dst)
        self.add_tcl_cmd("ip config -destIpAddrMode ipIdle")
        self.add_tcl_cmd("ip config -ttl %d" % ttl)
        self.add_tcl_cmd("ip config -totalLength %d" % len)
        self.add_tcl_cmd("ip config -fragment %d" % frag)
        self.add_tcl_cmd("ip config -ipProtocol ipV4ProtocolReserved255")
        self.add_tcl_cmd("ip config -identifier %d" % id)
        self.add_tcl_cmd("stream config -framesize %d" % (len + 18))
        self.add_tcl_cmd("ip set %d %d %d" % (self.chasId, port['card'], port['port']))


    def tear_down(self):
        """
        Run after each test case.
        """

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("^C", "# ", 50)
        self.dut.unbind_eventdev_port(port_to_unbind=self.eventdev_device_bus_id)
        self.dut.kill_all()
