# BSD LICENSE
#
# Copyright(c) 2010-2017 Intel Corporation. All rights reserved.
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
import os
import re

import framework.utils as utils
from framework.pktgen import PacketGeneratorHelper
from framework.test_case import TestCase


class TestEFD(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """

        self.build_server_node_efd()

        self.dut_ports = self.dut.get_ports()
        self.node_app = self.dut.apps_name["node"]
        self.server_app = self.dut.apps_name["server"]
        self.app_test_path = self.dut.apps_name["test"]
        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

    def build_server_node_efd(self):
        apps = ["node", "server"]
        for app in apps:
            out = self.dut.build_dpdk_apps("./examples/server_node_efd/%s" % app)
            self.verify("Error" not in out, "Compilation %s error" % app)
            self.verify("No such" not in out, "Compilation %s error" % app)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_efd_unit(self):
        """
        Run EFD unit test
        """
        eal_para = self.dut.create_eal_parameters(cores=[0, 1, 2, 3])
        self.dut.send_expect("./%s %s" % (self.app_test_path, eal_para), "RTE>>", 60)
        out = self.dut.send_expect("efd_autotest", "RTE>>", 120)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_efd_unit_perf(self):
        """
        Run EFD unit perf test
        """
        eal_para = self.dut.create_eal_parameters(cores=[0, 1, 2, 3])
        self.dut.send_expect("./%s %s" % (self.app_test_path, eal_para), "RTE>>", 60)
        out = self.dut.send_expect("efd_perf_autotest", "RTE>>", 120)
        self.logger.info(out)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_perf_efd_nodenum(self):
        """
        Run EFD perf evaluation for number of nodes
        """
        self.verify(len(self.dut_ports) >= 2, "Not enough ports")
        node_nums = [1, 2, 3, 4, 5, 6, 7, 8]

        flow_num = 1024 * 1024 * 2

        table_header = ["Value Bits", "Nodes", "Flow Entries", "Throughput(mpps)"]

        self.result_table_create(table_header)
        # perf of different nodes
        for node_num in node_nums:
            pps = self._efd_perf_evaluate(node_num, flow_num)

            self.result_table_add([8, node_num, "2M", pps])

        self.result_table_print()

    def test_perf_efd_flownums(self):
        """
        Run EFD perf evaluation for millions of flows
        """
        self.logger.warning(
            "Millions of flow required huge memory, please allocate 16G hugepage"
        )
        self.dut.setup_memory_linux(hugepages=8192)
        self.verify(len(self.dut_ports) >= 2, "Not enough ports")
        flow_nums = [
            1024 * 1024,
            1024 * 1024 * 2,
            1024 * 1024 * 4,
            1024 * 1024 * 8,
            1024 * 1024 * 16,
            1024 * 1024 * 32,
        ]

        table_header = ["Value Bits", "Nodes", "Million Flows", "Throughput(mpps)"]

        self.result_table_create(table_header)

        # perf of different flow numbers
        for flow_num in flow_nums:
            pps = self._efd_perf_evaluate(2, flow_num)

            self.result_table_add([8, 2, flow_num / (1024 * 1024), pps])

        self.result_table_print()

    def test_perf_efd_valuesize(self):
        """
        Run EFD perf evaluation for different value size
        """
        self.verify(len(self.dut_ports) >= 2, "Not enough ports")
        val_bitnums = [8, 16, 24, 32]
        flow_num = 1024 * 1024 * 2

        table_header = ["Value Bits", "Nodes", "Flow Entries", "Throughput(mpps)"]

        self.result_table_create(table_header)
        # perf of different value bit lengths
        for val_bitnum in val_bitnums:
            # change value length and rebuild dpdk
            self.dut.send_expect(
                "sed -i -e 's/#define RTE_EFD_VALUE_NUM_BITS .*$/#define RTE_EFD_VALUE_NUM_BITS (%d)/' lib/librte_efd/rte_efd.h"
                % val_bitnum,
                "#",
            )
            self.dut.build_install_dpdk(self.target)
            self.build_server_node_efd()

            pps = self._efd_perf_evaluate(2, flow_num)
            self.result_table_add([val_bitnum, 2, "2M", pps])

        self.result_table_print()
        self.dut.send_expect(
            "sed -i -e 's/#define RTE_EFD_VALUE_NUM_BITS .*$/#define RTE_EFD_VALUE_NUM_BITS (8)/' lib/librte_efd/rte_efd.h",
            "#",
        )
        self.dut.build_install_dpdk(self.target)
        self.build_server_node_efd()

    def _efd_perf_evaluate(self, node_num, flow_num):
        # extended flow number into etgen module

        # output port is calculated from overall ports number
        server_cmd_fmt = "%s %s -- -p 0x3 -n %d -f %s"
        node_cmd_fmt = "%s %s --proc-type=secondary -- -n %d"
        socket = self.dut.get_numa_id(self.dut_ports[0])

        pcap = os.sep.join([self.output_path, "efd.pcap"])
        self.tester.scapy_append(
            'wrpcap("%s", [Ether()/IP(src="0.0.0.0", dst="0.0.0.0")/("X"*26)])' % pcap
        )
        self.tester.scapy_execute()

        tgen_input = []
        rx_port = self.tester.get_local_port(self.dut_ports[0])
        tx_port = self.tester.get_local_port(self.dut_ports[1])

        pcap = os.sep.join([self.output_path, "efd.pcap"])
        tgen_input.append((tx_port, rx_port, pcap))
        tgen_input.append((rx_port, tx_port, pcap))

        cores = self.dut.get_core_list("1S/%dC/1T" % (node_num + 2), socket)

        self.verify(len(cores), "Can't find enough cores")

        eal_para = self.dut.create_eal_parameters(cores=cores[0:2], ports=[0, 1])
        server_cmd = server_cmd_fmt % (
            self.server_app,
            eal_para,
            node_num,
            hex(flow_num),
        )
        # create table may need few minutes
        self.dut.send_expect(server_cmd, "Finished Process Init", timeout=240)

        node_sessions = []
        for node in range(node_num):

            eal_para = self.dut.create_eal_parameters(cores=[cores[2 + node]])
            node_cmd = node_cmd_fmt % (self.node_app, eal_para, node)
            node_session = self.dut.new_session(suite="node%d" % node)
            node_sessions.append(node_session)
            node_session.send_expect(node_cmd, "Finished Process Init", timeout=30)

        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # run packet generator
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgen_input, 100, None, self.tester.pktgen
        )
        _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)

        for node_session in node_sessions:
            node_session.send_expect("^C", "#")
            self.dut.close_session(node_session)

        self.dut.send_expect("^C", "#")

        pps /= 1000000.0
        return pps

    def set_fields(self):
        """set ip protocol field behavior"""
        fields_config = {
            "ip": {
                # self.flow_num not used by this suite
                # 'dst': {'range': self.flow_num, 'action': 'inc'}
                "dst": {"range": 64, "action": "inc"}
            },
        }
        return fields_config

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
