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
import os
from test_case import TestCase
from pktgen import PacketGeneratorHelper


class TestDistributor(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.tester.extend_external_packet_generator(TestDistributor, self)

        # reduce tx queues for enable many workers
        self.dut.send_expect("sed -i -e 's/.*txRings = .*/\\tconst uint16_t rxRings = 1, txRings = 1;/' ./examples/distributor/main.c", "#")
        out = self.dut.build_dpdk_apps("./examples/distributor")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")

        self.dut_ports = self.dut.get_ports()
        self.app_distributor_path = self.dut.apps_name['distributor']
        self.app_test_path = self.dut.apps_name['test']
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

    def test_distributor_unit(self):
        """
        Run distributor unit test
        """
        eal_para = self.dut.create_eal_parameters(cores=[0, 1, 2, 3])
        self.dut.send_expect("./%s %s" % (self.app_test_path, eal_para), "RTE>>", 60)
        out = self.dut.send_expect("distributor_autotest", "RTE>>", 30)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_distributor_unit_perf(self):
        """
        Run distributor unit perf test
        """
        eal_para = self.dut.create_eal_parameters(cores=[0, 1, 2, 3])
        self.dut.send_expect("./%s %s" % (self.app_test_path, eal_para), "RTE>>", 60)
        out = self.dut.send_expect("distributor_perf_autotest", "RTE>>", 120)
        cycles_single = self.strip_cycles(out, "single")
        cycles_burst = self.strip_cycles(out, "burst")
        self.logger.info("Cycles for single mode is %d burst mode is %d"
                         % (cycles_single, cycles_burst))
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")
        self.verify(cycles_single > cycles_burst * 2,
                    "Burst performance should be much better")

    def test_perf_distributor(self):
        """
        Run distributor perf test, recorded statistic of Rx/Enqueue/Sent/Dequeue/Tx
        """
        self.verify(len(self.dut_ports) >= 1, "Not enough ports")
        workers = [1, 2, 3, 4, 8, 16, 32]
        table_header = ["Number of workers",
                        "Throughput Rate Rx received",
                        "Throughput Rate Rx core enqueued",
                        "Throughput Rate Distributor Sent",
                        "Throughput Rate Tx core dequeued",
                        "Throughput Rate Tx transmitted",
                        "Throughput Rate Pkts out",
                        "Throughput Rate Pkts out line rate"]

        # output port is calculated from overall ports number
        cmd_fmt = "%s %s -- -p 0x1"
        socket = self.dut.get_numa_id(self.dut_ports[0])

        pcap = os.sep.join([self.output_path, "distributor.pcap"])
        self.tester.scapy_append('wrpcap("%s", [Ether()/IP()/("X"*26)])' % pcap)
        self.tester.scapy_execute()
        tgen_input = []
        rx_port = self.tester.get_local_port(self.dut_ports[0])
        tx_port = self.tester.get_local_port(self.dut_ports[0])

        pcap = os.sep.join([self.output_path, "distributor.pcap"])
        tgen_input.append((tx_port, rx_port, pcap))

        self.result_table_create(table_header)
        for worker_num in workers:
            # Rx core/distributor core/Tx core/stats core
            cores = self.dut.get_core_list("1S/%dC/1T" % (worker_num + 4), socket)
            # If can't get enough core from one socket, just use all lcores
            if len(cores) < (worker_num + 4):
                cores = self._get_thread_lcore(worker_num + 4)

            eal_para = self.dut.create_eal_parameters(cores=cores, ports=[0])
            cmd = cmd_fmt % (self.app_distributor_path, eal_para)
            self.dut.send_expect(cmd, "doing packet RX", timeout=30)

            # clear streams before add new streams
            self.tester.pktgen.clear_streams()
            # run packet generator
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100,
                                    None, self.tester.pktgen)
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)

            # get aap output after sending packet
            self.app_output = self.dut.session.get_session_before(timeout=2)

            self.dut.send_expect("^C", "#")

            pps /= 1000000.0
            rx, enq, sent, deq, trans = self.strip_performance_data(self.app_output)
            rate = pps * 100 / float(self.wirespeed(self.nic, 64, 1))
            self.result_table_add([worker_num, rx, enq, sent, deq, trans, pps, float('%.3f' % rate)])

        self.result_table_print()

    def test_maximum_workers(self):
        """
        Check distributor app work fine with maximum workers
        """
        self.verify(len(self.dut_ports) >= 1, "Not enough ports")

        cmd_fmt = "%s %s -- -p 0x1"
        out = self.dut.send_expect("sed -n '/#define RTE_DISTRIB_MAX_WORKERS/p' lib/librte_distributor/distributor_private.h", "# ")
        reg_match = r"#define RTE_DISTRIB_MAX_WORKERS (.*)"
        m = re.match(reg_match, out)
        self.verify(m, "Can't find maximum worker number")

        max_workers = int(m.group(1))
        cores = self._get_thread_lcore(max_workers - 1 + 4)
        eal_para = self.dut.create_eal_parameters(cores=cores, ports=[0])
        cmd = cmd_fmt % (self.app_distributor_path, eal_para)
        self.dut.send_expect(cmd, "doing packet RX", timeout=30)

        tx_port = self.tester.get_local_port(self.dut_ports[0])
        tgen_input = [(tx_port, tx_port)]
        self.tester.check_random_pkts(tgen_input, pktnum=256, seq_check=True)

        self.dut.send_expect("^C", "#")

    def test_multiple_ports(self):
        """
        Check distributor app work fine with multiple ports
        """
        self.verify(len(self.dut_ports) >= 2, "Not enough ports")

        cmd_fmt = "%s %s -- -p 0x3"
        socket = self.dut.get_numa_id(self.dut_ports[0])
        cores = self.dut.get_core_list("1S/%dC/1T" % (2 + 4), socket)

        eal_para = self.dut.create_eal_parameters(cores=cores, ports=[0,1])
        cmd = cmd_fmt % (self.app_distributor_path, eal_para)
        self.dut.send_expect(cmd, "doing packet RX", timeout=30)

        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])
        tgen_input = [(tx_port, rx_port)]
        self.tester.check_random_pkts(tgen_input, pktnum=256, seq_check=True)

        tgen_input = [(rx_port, tx_port)]
        self.tester.check_random_pkts(tgen_input, pktnum=256, seq_check=True)

        self.dut.send_expect("^C", "#")

    def _get_thread_lcore(self, core_num):
        def strip_core(x):
            return(int(x['thread']))
        cores = list(map(strip_core, self.dut.cores[0:core_num]))
        return cores

    def hook_transmission_func(self):
        self.app_output = self.dut.session.get_session_before(timeout=2)

    def strip_performance_data(self, output=""):
        """
        Strip throughput of each stage in threads
            RX Thread:
            Port 0 Pktsin :
             - Received:
             - Returned:
             - Enqueued:
             - Dropped:
            Distributor thread:
             - In:
             - Returned:
             - Sent:
             - Dropped:
            TX thread:
             - Dequeued:
            Port 0 Pktsout:
             - Transmitted:
             - Dropped:
        """
        # skip the last one, we use the next one
        output = output[:output.rfind("RX Thread")]
        # skip the last two, we use the next one
        output = output[:output.rfind("RX Thread")]
        output = output[output.rfind("RX Thread"):]
        rec_rate = 0.0
        enq_rate = 0.0
        sent_rate = 0.0
        deq_rate = 0.0
        trans_rate = 0.0
        for line in output.splitlines():
            if "Received" in line:
                rec_rate = float(line.split()[2])
            elif "Enqueued" in line:
                enq_rate = float(line.split()[2])
            elif "Sent" in line:
                sent_rate = float(line.split()[2])
            elif "Dequeued" in line:
                deq_rate = float(line.split()[2])
            elif "Transmitted" in line:
                trans_rate = float(line.split()[2])

        return (rec_rate, enq_rate, sent_rate, deq_rate, trans_rate)

    def strip_cycles(self, out="", mode="single"):
        """
        Strip per packet cycles from output like:
            Time per burst:  12542
            Time per packet: 195
        """
        out = out[out.index("%s mode" % mode):]
        lines = out.splitlines()
        cycles = lines[2].split()[3]
        return int(cycles)

    def set_fields(self):
        ''' set ip protocol field behavior '''
        fields_config = {
        'ip':  {
            'dst': {'mask': '255.240.0.0', 'action': 'inc'}
        }, }

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
        self.dut.send_expect("sed -i -e 's/.*txRings = .*/\\tconst uint16_t rxRings = 1, txRings = rte_lcore_count() - 1;/' ./examples/distributor/main.c", "#")
        pass
