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
import re
import utils
from test_case import TestCase
from etgen import IxiaPacketGenerator


class TestEFD(TestCase, IxiaPacketGenerator):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.tester.extend_external_packet_generator(TestEFD, self)

        out = self.dut.build_dpdk_apps("./examples/server_node_efd")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")

        self.dut_ports = self.dut.get_ports()
        self.node_app = "./examples/server_node_efd/node/%s/node" % self.target
        self.server_app = "./examples/server_node_efd/server/%s/server" % self.target

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_efd_unit(self):
        """
        Run EFD unit test
        """
        self.dut.send_expect("./%s/app/test -n 1 -c f" % self.target, "RTE>>", 60)
        out = self.dut.send_expect("efd_autotest", "RTE>>", 120)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_efd_unit_perf(self):
        """
        Run EFD unit perf test
        """
        self.dut.send_expect("./%s/app/test -n 1 -c f" % self.target, "RTE>>", 60)
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

        table_header = ["Value Bits",
                        "Nodes",
                        "Flow Entries",
                        "Throughput(mpps)"]

        self.result_table_create(table_header)
        # perf of different nodes
        for node_num in node_nums:
            pps = self._efd_perf_evaluate(node_num, flow_num)

            self.result_table_add([8, node_num, "2M",  pps])

        self.result_table_print()

    def test_perf_efd_flownums(self):
        """
        Run EFD perf evaluation for millions of flows
        """
        self.logger.warning("Millions of flow required huge memory, please allocate 16G hugepage")
        self.dut.setup_memory_linux(hugepages=8192)
        self.verify(len(self.dut_ports) >= 2, "Not enough ports")
        flow_nums = [1024 * 1024, 1024 * 1024 * 2, 1024 * 1024 * 4,
                     1024 * 1024 * 8, 1024 * 1024 * 16, 1024 * 1024 * 32]

        table_header = ["Value Bits",
                        "Nodes",
                        "Million Flows",
                        "Throughput(mpps)"]

        self.result_table_create(table_header)

        # perf of different flow numbers
        for flow_num in flow_nums:
            pps = self._efd_perf_evaluate(2, flow_num)

            self.result_table_add([8, 2, flow_num / (1024 * 1024),  pps])

        self.result_table_print()

    def test_perf_efd_valuesize(self):
        """
        Run EFD perf evaluation for different value size
        """
        self.verify(len(self.dut_ports) >= 2, "Not enough ports")
        val_bitnums = [8, 16, 24, 32]
        flow_num = 1024 * 1024 * 2

        table_header = ["Value Bits",
                        "Nodes",
                        "Flow Entries",
                        "Throughput(mpps)"]

        self.result_table_create(table_header)
        # perf of different value bit lengths
        for val_bitnum in val_bitnums:
            # change value length and rebuild dpdk
            self.dut.send_expect("sed -i -e 's/#define RTE_EFD_VALUE_NUM_BITS .*$/#define RTE_EFD_VALUE_NUM_BITS (%d)/' lib/librte_efd/rte_efd.h" % val_bitnum, "#")
            self.dut.build_install_dpdk(self.target)
            out = self.dut.build_dpdk_apps("./examples/server_node_efd")
            self.verify("Error" not in out, "Compilation error")
            self.verify("No such" not in out, "Compilation error")

            pps = self._efd_perf_evaluate(2, flow_num)
            self.result_table_add([val_bitnum, 2, "2M",  pps])

        self.result_table_print()
        self.dut.send_expect("sed -i -e 's/#define RTE_EFD_VALUE_NUM_BITS .*$/#define RTE_EFD_VALUE_NUM_BITS (8)' lib/librte_efd/rte_efd.h", "#")
        self.dut.build_install_dpdk(self.target)
        out = self.dut.build_dpdk_apps("./examples/server_node_efd")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")

    def _efd_perf_evaluate(self, node_num, flow_num):
        # extended flow number into etgen module
        self.tester.ixia_packet_gen.flow_num = flow_num

        # output port is calculated from overall ports number
        server_cmd_fmt = "%s -c %s -n %d -w %s -w %s -- -p 0x3 -n %d -f %s"
        node_cmd_fmt = "%s -c %s -n %d --proc-type=secondary -- -n %d"
        socket = self.dut.get_numa_id(self.dut_ports[0])

        self.tester.scapy_append('wrpcap("efd.pcap", [Ether()/IP(src="0.0.0.0", dst="0.0.0.0")/("X"*26)])')
        self.tester.scapy_execute()

        tgen_input = []
        rx_port = self.tester.get_local_port(self.dut_ports[0])
        tx_port = self.tester.get_local_port(self.dut_ports[1])

        tgen_input.append((tx_port, rx_port, "efd.pcap"))
        tgen_input.append((rx_port, tx_port, "efd.pcap"))

        cores = self.dut.get_core_list("1S/%dC/1T" % (node_num + 2), socket)

        self.verify(len(cores), "Can't find enough cores")

        server_cmd = server_cmd_fmt % (self.server_app, utils.create_mask(cores[0:2]),
                                       self.dut.get_memory_channels(),
                                       self.dut.get_port_pci(self.dut_ports[0]),
                                       self.dut.get_port_pci(self.dut_ports[1]),
                                       node_num, hex(flow_num))

        # create table may need few minutes
        self.dut.send_expect(server_cmd, "Finished Process Init", timeout=240)

        node_sessions = []
        for node in range(node_num):
            node_cmd = node_cmd_fmt % (self.node_app, utils.create_mask([cores[2 + node]]),
                                       self.dut.get_memory_channels(), node)
            node_session = self.dut.new_session(suite="node%d" % node)
            node_sessions.append(node_session)
            node_session.send_expect(node_cmd, "Finished Process Init", timeout=30)

        _, pps = self.tester.traffic_generator_throughput(tgen_input, delay=10)

        for node_session in node_sessions:
            node_session.send_expect("^C", "#")
            self.dut.close_session(node_session)

        self.dut.send_expect("^C", "#")

        pps /= 1000000.0
        return pps

    def ip(self, port, frag, src, proto, tos, dst, chksum, len, options, version, flags, ihl, ttl, id):
        self.add_tcl_cmd("protocol config -name ip")
        self.add_tcl_cmd('ip config -sourceIpAddr "%s"' % src)
        self.add_tcl_cmd("ip config -sourceIpAddrMode ipIdle")
        self.add_tcl_cmd('ip config -destIpAddr "%s"' % dst)
        self.add_tcl_cmd("ip config -destIpAddrMode ipIncrHost")
        # increase number equal to flow number
        self.add_tcl_cmd("ip config -destIpAddrRepeatCount %d" % self.flow_num)
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
        self.dut.kill_all()
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
