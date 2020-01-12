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
Test Layer-2 Forwarding support
"""
import os
import time
import utils
from test_case import TestCase
from settings import HEADER_SIZE
from pktgen import PacketGeneratorHelper


class TestL2fwd(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.

        L2fwd prerequisites.
        """
        self.frame_sizes = [64, 65, 128, 256, 512, 1024, 1280, 1518]

        self.test_queues = [{'queues': 1, 'Mpps': {}, 'pct': {}},
                            {'queues': 2, 'Mpps': {}, 'pct': {}},
                            {'queues': 4, 'Mpps': {}, 'pct': {}},
                            {'queues': 8, 'Mpps': {}, 'pct': {}}
                            ]

        self.core_config = "1S/4C/1T"
        self.number_of_ports = 2
        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip'] + \
            HEADER_SIZE['udp']

        self.dut_ports = self.dut.get_ports_performance(force_different_nic=False)

        self.verify(len(self.dut_ports) >= self.number_of_ports,
                    "Not enough ports for " + self.nic)

        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])

        # compile
        out = self.dut.build_dpdk_apps("./examples/l2fwd")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")

        self.table_header = ['Frame']
        for queue in self.test_queues:
            self.table_header.append("%d queues Mpps" % queue['queues'])
            self.table_header.append("% linerate")

        self.result_table_create(self.table_header)

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
        pass

    def quit_l2fwd(self):
        self.dut.send_expect("fg", "l2fwd ", 5)
        self.dut.send_expect("^C", "# ", 5)

    def notest_port_testing(self):
        """
        Check port forwarding.
        """
        # the cases use the first two ports
        port_mask = utils.create_mask([self.dut_ports[0], self.dut_ports[1]])

        self.dut.send_expect("./examples/l2fwd/build/app/l2fwd -n 1 -c f -- -q 8 -p %s  &" % port_mask, "L2FWD: entering main loop", 60)

        for i in [0, 1]:
            tx_port = self.tester.get_local_port(self.dut_ports[i])
            rx_port = self.tester.get_local_port(self.dut_ports[1 - i])

            tx_interface = self.tester.get_interface(tx_port)
            rx_interface = self.tester.get_interface(rx_port)

            self.tester.scapy_background()
            self.tester.scapy_append('p = sniff(iface="%s", count=1)' % rx_interface)
            self.tester.scapy_append('number_packets=len(p)')
            self.tester.scapy_append('RESULT = str(number_packets)')

            self.tester.scapy_foreground()
            self.tester.scapy_append('sendp([Ether()/IP()/UDP()/("X"*46)], iface="%s")' % tx_interface)

            self.tester.scapy_execute()
            number_packets = self.tester.scapy_get_result()
            self.verify(number_packets == "1", "Failed to switch L2 frame")

        self.quit_l2fwd()

    def test_l2fwd_integrity(self):
        """
        Check port forwarding.
        """
        # the cases use the first two ports
        port_mask = utils.create_mask([self.dut_ports[0], self.dut_ports[1]])

        core_mask = utils.create_mask(self.dut.get_core_list(self.core_config,
                                                           socket=self.ports_socket))
        for queues in self.test_queues:

            command_line = "./examples/l2fwd/build/app/l2fwd -n %d -c %s -- -q %s -p %s &" % \
                (self.dut.get_memory_channels(), core_mask,
                 str(queues['queues']), port_mask)

            self.dut.send_expect(command_line, "L2FWD: entering main loop", 60)

            tgen_input = []
            tx_port = self.tester.get_local_port(self.dut_ports[0])
            rx_port = self.tester.get_local_port(self.dut_ports[1])
            tgen_input.append((tx_port, rx_port))

            self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
            result = self.tester.check_random_pkts(tgen_input, allow_miss=False, params = [('ether', {'dst': '%s'%(self.dst_mac)})])
            self.verify(result != False, "Packet integrity check failed")

            self.quit_l2fwd()

    def test_perf_l2fwd_performance(self):
        """
        Benchmark performance for frame_sizes.
        """
        ports = []
        for port in range(self.number_of_ports):
            ports.append(self.dut_ports[port])

        port_mask = utils.create_mask(ports)
        core_mask = utils.create_mask(self.dut.get_core_list(self.core_config,
                                                           socket=self.ports_socket))

        for frame_size in self.frame_sizes:

            payload_size = frame_size - self.headers_size

            tgen_input = []
            cnt = 1
            for port in range(self.number_of_ports):
                rx_port = self.tester.get_local_port(self.dut_ports[port % self.number_of_ports])
                tx_port = self.tester.get_local_port(self.dut_ports[(port + 1) % self.number_of_ports])
                destination_mac = self.dut.get_mac_address(self.dut_ports[(port + 1) % self.number_of_ports])
                pcap = os.sep.join([self.output_path, "l2fwd_{0}_{1}.pcap".format(port, cnt)])
                self.tester.scapy_append('wrpcap("%s", [Ether(dst="%s")/IP()/UDP()/("X"*%d)])' % (
                    pcap, destination_mac, payload_size))
                tgen_input.append((tx_port, rx_port, pcap))
                time.sleep(3)
                self.tester.scapy_execute()
                cnt += 1

            for queues in self.test_queues:

                command_line = "./examples/l2fwd/build/app/l2fwd -n %d -c %s -- -q %s -p %s &" % \
                    (self.dut.get_memory_channels(), core_mask,
                     str(queues['queues']), port_mask)

#                self.dut.send_expect(command_line, "memory mapped", 60)
                self.dut.send_expect(command_line, "L2FWD: entering main loop", 60)
                # wait 5 second after l2fwd boot up. 
                # It is aimed to make sure trex detect link up status.
                if self.tester.is_pktgen:
                    time.sleep(5)
                info = "Executing l2fwd using %s queues, frame size %d and %s setup.\n" % \
                       (queues['queues'], frame_size, self.core_config)

                self.logger.info(info)
                self.rst_report(info, annex=True)
                self.rst_report(command_line + "\n\n", frame=True, annex=True)

                # clear streams before add new streams
                self.tester.pktgen.clear_streams()
                # run packet generator
                streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100,
                                                    None, self.tester.pktgen)
                _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)

                Mpps = pps / 1000000.0
                queues['Mpps'][frame_size] = Mpps
                queues['pct'][frame_size] = Mpps * 100 / float(self.wirespeed(
                                                               self.nic,
                                                               frame_size,
                                                               self.number_of_ports))

                self.quit_l2fwd()

        # Look for transmission error in the results
        for frame_size in self.frame_sizes:
            for n in range(len(self.test_queues)):
                self.verify(self.test_queues[n]['Mpps'][frame_size] > 0,
                            "No traffic detected")

        # Prepare the results for table
        for frame_size in self.frame_sizes:
            results_row = []
            results_row.append(frame_size)
            for queue in self.test_queues:
                results_row.append(queue['Mpps'][frame_size])
                results_row.append(queue['pct'][frame_size])

            self.result_table_add(results_row)

        self.result_table_print()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("fg", "l2fwd|# ", 5)
        self.dut.send_expect("^C", "# ", 5)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
