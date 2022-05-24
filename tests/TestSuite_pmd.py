# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

"""
DPDK Test suite.
Test userland 10Gb PMD
"""

import os
import re
import time
from datetime import datetime
from time import sleep

import framework.utils as utils
import nics.perf_report as perf_report
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import FOLDERS, HEADER_SIZE
from framework.test_case import TestCase
from nics.system_info import SystemInfo


class TestPmd(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.

        PMD prerequisites.
        """

        self.frame_sizes = [64, 72, 128, 256, 512, 1024, 1280, 1518]

        self.rxfreet_values = [0, 8, 16, 32, 64, 128]

        self.test_cycles = [{"cores": "1S/2C/1T", "Mpps": {}, "pct": {}}]

        self.table_header = ["Frame Size"]
        for test_cycle in self.test_cycles:
            self.table_header.append("%s Mpps" % test_cycle["cores"])
            self.table_header.append("% linerate")

        self.perf_results = {"header": [], "data": []}

        self.blocklist = ""

        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports()
        if self.dut.get_os_type() == "linux":
            # Get dut system information
            port_num = self.dut_ports[0]
            pci_device_id = self.dut.ports_info[port_num]["pci"]
            ori_driver = self.dut.ports_info[port_num]["port"].get_nic_driver()
            self.dut.ports_info[port_num]["port"].bind_driver()

            sut = SystemInfo(self.dut, pci_device_id)
            if self.nic not in ["cavium_a063", "cavium_a064"]:
                self.system_info = sut.get_system_info()
            self.nic_info = sut.get_nic_info()

            self.dut.ports_info[port_num]["port"].bind_driver(ori_driver)
        ######

        self.headers_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"] + HEADER_SIZE["tcp"]

        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])

        self.pmdout = PmdOutput(self.dut)

        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_perf_single_core_performance(self):
        """
        Run single core performance
        """
        self.perf_results["header"] = []
        self.perf_results["data"] = []

        if len(self.dut_ports) >= 4:
            self.pmd_performance_4ports()
        else:
            self.verify(
                len(self.dut_ports) >= 2,
                "Insufficient ports for 2 ports performance test",
            )
            self.pmd_performance_2ports()

        # To replace False to True for if condition to send the result by email.
        if False:
            # it need place dpdk source git repo under dep directory.
            repo_dir = FOLDERS["Depends"] + r"/dpdk"
            git_info = perf_report.get_dpdk_git_info(repo_dir)
            self.verify(git_info is not None, "get dpdk git repo error")

            tpl_path = FOLDERS["NicDriver"] + r"/perf_report.jinja"
            file_tpl = os.path.abspath(tpl_path)
            html_msg = perf_report.generate_html_report(
                file_tpl,
                perf_data=self.perf_results["data"],
                git_info=git_info,
                nic_info=self.nic_info,
                system_info=self.system_info,
            )
            self.verify(html_msg is not None, "generate html report error")

            subject = "Single core performance test with %d ports %s -- %s" % (
                len(self.dut_ports),
                self.nic,
                datetime.now().strftime("%Y-%m-%d %H:%M"),
            )
            sender = "xxxxxx@intel.com"
            mailto = ["xxxxxx@intel.com"]
            smtp_server = "smtp.intel.com"
            perf_report.send_html_report(sender, mailto, subject, html_msg, smtp_server)

    def pmd_performance_4ports(self):
        """
        PMD Performance Benchmarking with 4 ports.
        """
        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))
        # prepare traffic generator input
        tgen_input = []
        pcap = os.sep.join([self.output_path, "test.pcap"])
        tgen_input.append(
            (
                self.tester.get_local_port(self.dut_ports[0]),
                self.tester.get_local_port(self.dut_ports[1]),
                pcap,
            )
        )
        tgen_input.append(
            (
                self.tester.get_local_port(self.dut_ports[2]),
                self.tester.get_local_port(self.dut_ports[3]),
                pcap,
            )
        )
        tgen_input.append(
            (
                self.tester.get_local_port(self.dut_ports[1]),
                self.tester.get_local_port(self.dut_ports[0]),
                pcap,
            )
        )
        tgen_input.append(
            (
                self.tester.get_local_port(self.dut_ports[3]),
                self.tester.get_local_port(self.dut_ports[2]),
                pcap,
            )
        )

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle["cores"]

            core_list = self.dut.get_core_list(core_config, socket=self.ports_socket)

            if len(core_list) > 4:
                queues = len(core_list) / 4
            else:
                queues = 1

            core_mask = utils.create_mask(core_list)
            port_mask = utils.create_mask(self.dut.get_ports())

            self.pmdout.start_testpmd(
                core_config,
                " --rxq=%d --txq=%d --portmask=%s --rss-ip --txrst=32 --txfreet=32 --txd=128 --tx-offloads=0"
                % (queues, queues, port_mask),
                socket=self.ports_socket,
            )
            command_line = self.pmdout.get_pmd_cmd()

            info = "Executing PMD using %s\n" % test_cycle["cores"]
            self.rst_report(info, annex=True)
            self.logger.info(info)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            # self.dut.send_expect("set fwd mac", "testpmd> ", 100)
            self.dut.send_expect("start", "testpmd> ", 100)
            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 4)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("%s", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])'
                    % (pcap, payload_size)
                )
                self.tester.scapy_execute()

                vm_config = self.set_fields()
                # clear streams before add new streams
                self.tester.pktgen.clear_streams()
                # run packet generator
                streams = self.pktgen_helper.prepare_stream_from_tginput(
                    tgen_input, 100, vm_config, self.tester.pktgen
                )
                traffic_opt = {
                    "duration": 60,
                }
                _, pps = self.tester.pktgen.measure_throughput(
                    stream_ids=streams, options=traffic_opt
                )

                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle["Mpps"][frame_size] = float("%.3f" % pps)
                test_cycle["pct"][frame_size] = float("%.3f" % pct)

            self.dut.send_expect("stop", "testpmd> ")
            self.dut.send_expect("quit", "# ", 30)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(
                    self.test_cycles[n]["Mpps"][frame_size] is not 0,
                    "No traffic detected",
                )

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results["header"] = self.table_header

        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle["Mpps"][frame_size])
                table_row.append(test_cycle["pct"][frame_size])

            self.result_table_add(table_row)
            self.perf_results["data"].append(table_row)

        self.result_table_print()

    def pmd_performance_2ports(self):
        """
        PMD Performance Benchmarking with 2 ports.
        """

        all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))

        # prepare traffic generator input
        tgen_input = []
        pcap = os.sep.join([self.output_path, "test.pcap"])
        tgen_input.append(
            (
                self.tester.get_local_port(self.dut_ports[0]),
                self.tester.get_local_port(self.dut_ports[1]),
                pcap,
            )
        )
        tgen_input.append(
            (
                self.tester.get_local_port(self.dut_ports[1]),
                self.tester.get_local_port(self.dut_ports[0]),
                pcap,
            )
        )

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle["cores"]

            core_list = self.dut.get_core_list(core_config, socket=self.ports_socket)

            if len(core_list) > 2:
                queues = len(core_list) / 2
            else:
                queues = 1

            core_mask = utils.create_mask(core_list)
            port_mask = utils.create_mask([self.dut_ports[0], self.dut_ports[1]])

            # self.pmdout.start_testpmd("all", "--coremask=%s --rxq=%d --txq=%d --portmask=%s" % (core_mask, queues, queues, port_mask))
            self.pmdout.start_testpmd(
                core_config,
                " --rxq=%d --txq=%d --portmask=%s --rss-ip --txrst=32 --txfreet=32 --txd=128"
                % (queues, queues, port_mask),
                socket=self.ports_socket,
            )
            command_line = self.pmdout.get_pmd_cmd()

            info = "Executing PMD using %s\n" % test_cycle["cores"]
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            self.dut.send_expect("start", "testpmd> ", 100)

            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, 2)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                self.tester.scapy_append(
                    'wrpcap("%s", [Ether(src="52:00:00:00:00:00")/IP(src="1.2.3.4",dst="1.1.1.1")/TCP()/("X"*%d)])'
                    % (pcap, payload_size)
                )
                self.tester.scapy_execute()

                # run traffic generator

                vm_config = self.set_fields()
                # clear streams before add new streams
                self.tester.pktgen.clear_streams()
                # run packet generator
                streams = self.pktgen_helper.prepare_stream_from_tginput(
                    tgen_input, 100, vm_config, self.tester.pktgen
                )
                traffic_opt = {
                    "duration": 60,
                }
                _, pps = self.tester.pktgen.measure_throughput(
                    stream_ids=streams, options=traffic_opt
                )

                pps /= 1000000.0
                pct = pps * 100 / wirespeed
                test_cycle["Mpps"][frame_size] = float("%.3f" % pps)
                test_cycle["pct"][frame_size] = float("%.3f" % pct)

            self.dut.send_expect("stop", "testpmd> ")
            self.dut.send_expect("quit", "# ", 30)
            sleep(5)

        for n in range(len(self.test_cycles)):
            for frame_size in self.frame_sizes:
                self.verify(
                    self.test_cycles[n]["Mpps"][frame_size] > 0, "No traffic detected"
                )

        # Print results
        self.result_table_create(self.table_header)
        self.perf_results["header"] = self.table_header
        for frame_size in self.frame_sizes:
            table_row = [frame_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle["Mpps"][frame_size])
                table_row.append(test_cycle["pct"][frame_size])

            self.result_table_add(table_row)
            self.perf_results["data"].append(table_row)

        self.result_table_print()

    def test_checksum_checking(self):
        """
        Packet forwarding checking test
        """

        self.dut.kill_all()

        port_mask = utils.create_mask([self.dut_ports[0], self.dut_ports[1]])

        for rxfreet_value in self.rxfreet_values:

            self.pmdout.start_testpmd(
                "1S/2C/1T",
                "--portmask=%s --enable-rx-cksum --disable-rss --rxd=1024 --txd=1024 --rxfreet=%d"
                % (port_mask, rxfreet_value),
                socket=self.ports_socket,
            )
            self.dut.send_expect("set fwd csum", "testpmd> ")
            self.dut.send_expect("start", "testpmd> ")

            self.send_packet(self.frame_sizes[0], checksum_test=True)

            l4csum_error = self.stop_and_get_l4csum_errors()

            # Check the l4 checksum errors reported for Rx port
            self.verify(
                4 == int(l4csum_error[1]),
                "Wrong l4 checksum error count using rxfreet=%d (expected 4, reported %s)"
                % (rxfreet_value, l4csum_error[1]),
            )

            self.dut.send_expect("quit", "# ", 30)
            sleep(5)

    def test_packet_checking(self):
        """
        Packet forwarding checking test
        """

        self.dut.kill_all()

        port_mask = utils.create_mask([self.dut_ports[0], self.dut_ports[1]])

        self.pmdout.start_testpmd(
            "1S/2C/1T", "--portmask=%s" % port_mask, socket=self.ports_socket
        )
        self.dut.send_expect("start", "testpmd> ")
        for size in self.frame_sizes:
            self.send_packet(size)

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)
        sleep(5)

    def test_packet_checking_scalar_mode(self):
        """
        Packet forwarding checking test
        """

        self.dut.kill_all()

        port_mask = utils.create_mask([self.dut_ports[0], self.dut_ports[1]])

        eal_opts = ""
        for port in self.dut_ports:
            eal_opts += "-a %s,scalar_enable=1 " % (
                self.dut.get_port_pci(self.dut_ports[port])
            )

        self.pmdout.start_testpmd(
            "1S/2C/1T",
            "--portmask=%s" % port_mask,
            eal_param=eal_opts,
            socket=self.ports_socket,
        )
        self.dut.send_expect("start", "testpmd> ")
        for size in self.frame_sizes:
            self.send_packet(size, scalar_test=True)

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)
        sleep(5)

    def stop_and_get_l4csum_errors(self):
        """
        Stop forwarding and get Bad-l4csum number from stop statistic
        """

        out = self.dut.send_expect("stop", "testpmd> ")
        result_scanner = r"Bad-l4csum: ([0-9]+) \s*"
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.findall(out)

        return m

    def get_stats(self, portid):
        """
        Get packets number from port statistic
        """

        stats = self.pmdout.get_pmd_stats(portid)
        return stats

    def send_packet(self, frame_size, checksum_test=False, scalar_test=False):
        """
        Send 1 packet to portid
        """

        port0_stats = self.get_stats(self.dut_ports[0])
        gp0tx_pkts, gp0tx_bytes = [port0_stats["TX-packets"], port0_stats["TX-bytes"]]
        port1_stats = self.get_stats(self.dut_ports[1])
        gp1rx_pkts, gp1rx_err, gp1rx_bytes = [
            port1_stats["RX-packets"],
            port1_stats["RX-errors"],
            port1_stats["RX-bytes"],
        ]

        interface = self.tester.get_interface(
            self.tester.get_local_port(self.dut_ports[1])
        )
        mac = self.dut.get_mac_address(self.dut_ports[1])

        load_size = frame_size - HEADER_SIZE["eth"]
        padding = (
            frame_size - HEADER_SIZE["eth"] - HEADER_SIZE["ip"] - HEADER_SIZE["udp"]
        )

        checksum = ""
        if checksum_test:
            checksum = "chksum=0x1"

        if scalar_test:
            pkt_count = 1
        else:
            pkt_count = 4
        self.tester.scapy_foreground()
        self.tester.scapy_append('nutmac="%s"' % mac)
        self.tester.scapy_append(
            'sendp([Ether(dst=nutmac, src="52:00:00:00:00:00")/IP(len=%s)/UDP(%s)/Raw(load="\x50"*%s)], iface="%s", count=%s)'
            % (load_size, checksum, padding, interface, pkt_count)
        )

        out = self.tester.scapy_execute()
        time.sleep(0.5)

        port0_stats = self.get_stats(self.dut_ports[0])
        p0tx_pkts, p0tx_bytes = [port0_stats["TX-packets"], port0_stats["TX-bytes"]]
        port1_stats = self.get_stats(self.dut_ports[1])
        p1rx_pkts, p1rx_err, p1rx_bytes = [
            port1_stats["RX-packets"],
            port1_stats["RX-errors"],
            port1_stats["RX-bytes"],
        ]

        p0tx_pkts -= gp0tx_pkts
        p0tx_bytes -= gp0tx_bytes
        p1rx_pkts -= gp1rx_pkts
        p1rx_bytes -= gp1rx_bytes
        p1rx_err -= gp1rx_err

        time.sleep(5)

        self.verify(
            self.pmdout.check_tx_bytes(p0tx_pkts, p1rx_pkts),
            "packet pass assert error, %d RX packets, %d TX packets"
            % (p1rx_pkts, p0tx_pkts),
        )

        self.verify(
            p1rx_bytes == (frame_size - 4) * pkt_count,
            "packet pass assert error, expected %d RX bytes, actual %d"
            % ((frame_size - 4) * pkt_count, p1rx_bytes),
        )

        self.verify(
            self.pmdout.check_tx_bytes(p0tx_bytes, (frame_size - 4) * pkt_count),
            "packet pass assert error, expected %d TX bytes, actual %d"
            % ((frame_size - 4) * pkt_count, p0tx_bytes),
        )

        return out

    def set_fields(self):
        """set ip protocol field behavior"""
        fields_config = {
            "ip": {
                "src": {"action": "random"},
            },
        }
        return fields_config

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
