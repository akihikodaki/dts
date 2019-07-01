# BSD LICENSE
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (C) 2019 Marvell International Ltd.

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

class TestEventdevPipelinePerf(TestCase,IxiaPacketGenerator):

    def set_up_all(self):
        """
        Run at the start of each test suite.

        PMD prerequisites.
        """
        self.tester.extend_external_packet_generator(TestEventdevPipelinePerf, self)

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

    def eventdev_cmd(self, stlist, nports, wmask):

        self.Port_pci_ids = []
        command_line1 = "dpdk-eventdev_pipeline -c %s -w %s"
        for i in range(0, nports):
            self.Port_pci_ids.append(self.dut.ports_info[i]['pci'])
            ## Adding core-list and pci-ids
            command_line1 = command_line1 + " -w %s "
        ## Adding test and stage types
        command_line2 = "-- -w %s -n=0 --dump %s -m 16384" % (wmask , stlist )
        return command_line1 + command_line2

    def test_perf_eventdev_pipeline_1ports_atomic_performance(self):
        """
        Evendev_Pipeline Performance Benchmarking with 1 ports.
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
            core_mask = utils.create_mask(core_list)
            core_list.remove(core_list[0])
            worker_core_mask = utils.create_mask(core_list)

            command_line = self.eventdev_cmd("", 1, worker_core_mask)
            command_line = command_line %(core_mask, self.eventdev_device_bus_id, self.Port_pci_ids[0])
            self.dut.send_expect(command_line,"eventdev port 0", 100)

            info = "Executing Eventdev_pipeline using %s\n" % test_cycle['cores']
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

            self.dut.send_expect("^C", "# ", 5)
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

    def test_perf_eventdev_pipeline_1ports_parallel_performance(self):
        """
        Evendev_Pipeline Performance Benchmarking with 1 ports.
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
            core_mask = utils.create_mask(core_list)
            core_list.remove(core_list[0])
            worker_core_mask = utils.create_mask(core_list)

            command_line = self.eventdev_cmd("-p", 1, worker_core_mask)
            command_line = command_line %(core_mask, self.eventdev_device_bus_id, self.Port_pci_ids[0])
            self.dut.send_expect(command_line,"eventdev port 0", 100)

            info = "Executing Eventdev_pipeline using %s\n" % test_cycle['cores']
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

            self.dut.send_expect("^C", "# ", 5)
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

    def test_perf_eventdev_pipeline_1ports_order_performance(self):
        """
        Evendev_Pipeline Performance Benchmarking with 1 ports.
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
            core_mask = utils.create_mask(core_list)
            core_list.remove(core_list[0])
            worker_core_mask = utils.create_mask(core_list)

            command_line = self.eventdev_cmd("-o", 1, worker_core_mask)
            command_line = command_line %(core_mask, self.eventdev_device_bus_id, self.Port_pci_ids[0])
            self.dut.send_expect(command_line,"eventdev port 0", 100)

            info = "Executing Eventdev_pipeline using %s\n" % test_cycle['cores']
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

            self.dut.send_expect("^C", "# ", 5)
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

    def test_perf_eventdev_pipeline_2ports_atomic_performance(self):
        """
        Evendev_Pipeline Performance Benchmarking with 2 ports.
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
            core_mask = utils.create_mask(core_list)
            core_list.remove(core_list[0])
            worker_core_mask = utils.create_mask(core_list)

            command_line = self.eventdev_cmd("", 2, worker_core_mask )
            command_line = command_line %(core_mask, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1])
            self.dut.send_expect(command_line,"eventdev port 0", 100)

            info = "Executing Eventdev_pipeline using %s\n" % test_cycle['cores']
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

            self.dut.send_expect("^C", "# ", 5)
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

    def test_perf_eventdev_pipeline_2ports_parallel_performance(self):
        """
        Evendev_Pipeline parallel schedule type Performance Benchmarking with 2 ports.
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
            core_mask = utils.create_mask(core_list)
            core_list.remove(core_list[0])
            worker_core_mask = utils.create_mask(core_list)

            command_line = self.eventdev_cmd("-p", 2, worker_core_mask)
            command_line = command_line %(core_mask, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1])
            self.dut.send_expect(command_line,"eventdev port 0", 100)

            info = "Executing Eventdev_pipeline using %s\n" % test_cycle['cores']
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

            self.dut.send_expect("^C", "# ", 5)
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

    def test_perf_eventdev_pipeline_2ports_order_performance(self):
        """
        Evendev_Pipeline Order schedule type Performance Benchmarking with 2 ports.
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
            core_mask = utils.create_mask(core_list)
            core_list.remove(core_list[0])
            worker_core_mask = utils.create_mask(core_list)

            command_line = self.eventdev_cmd("-o", 2, worker_core_mask)
            command_line = command_line %(core_mask, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1])
            self.dut.send_expect(command_line,"eventdev port 0", 100)

            info = "Executing Eventdev_pipeline using %s\n" % test_cycle['cores']
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

            self.dut.send_expect("^C", "# ", 5)
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

    def test_perf_eventdev_pipeline_4ports_atomic_performance(self):
        """
        Evendev_Pipeline Performance Benchmarking with 4 ports.
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
            core_mask = utils.create_mask(core_list)
            core_list.remove(core_list[0])
            worker_core_mask = utils.create_mask(core_list)

            command_line = self.eventdev_cmd("", 4, worker_core_mask)
            command_line = command_line %(core_mask, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1], self.Port_pci_ids[2], self.Port_pci_ids[3])
            self.dut.send_expect(command_line,"eventdev port 0", 100)

            info = "Executing Eventdev_pipeline using %s\n" % test_cycle['cores']
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

            self.dut.send_expect("^C", "# ", 5)
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

    def test_perf_eventdev_pipeline_4ports_parallel_performance(self):
        """
        Evendev_Pipeline parallel schedule type Performance Benchmarking with 4 ports.
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
            core_mask = utils.create_mask(core_list)
            core_list.remove(core_list[0])
            worker_core_mask = utils.create_mask(core_list)

            command_line = self.eventdev_cmd("-p", 4, worker_core_mask)
            command_line = command_line %(core_mask, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1], self.Port_pci_ids[2], self.Port_pci_ids[3])
            self.dut.send_expect(command_line,"eventdev port 0", 100)

            info = "Executing Eventdev_pipeline using %s\n" % test_cycle['cores']
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

            self.dut.send_expect("^C", "# ", 5)
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

    def test_perf_eventdev_pipeline_4ports_order_performance(self):
        """
        Evendev_Pipeline Order schedule type Performance Benchmarking with 4 ports.
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
            core_mask = utils.create_mask(core_list)
            core_list.remove(core_list[0])
            worker_core_mask = utils.create_mask(core_list)

            command_line = self.eventdev_cmd("-o", 4, worker_core_mask)
            command_line = command_line %(core_mask, self.eventdev_device_bus_id, self.Port_pci_ids[0], self.Port_pci_ids[1], self.Port_pci_ids[2], self.Port_pci_ids[3])
            self.dut.send_expect(command_line,"eventdev port 0", 100)

            info = "Executing Eventdev_pipeline using %s\n" % test_cycle['cores']
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

            self.dut.send_expect("^C", "# ", 5)
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
        self.dut.send_expect("^C", "# ", 5)
        self.dut.unbind_eventdev_port(port_to_unbind=self.eventdev_device_bus_id)
        self.dut.kill_all()
