# BSD LICENSE
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
Performance-Thread test script.
"""
import os
import string
import utils
from test_case import TestCase
from settings import HEADER_SIZE
from pktgen import PacketGeneratorHelper


class TestPerformanceThread(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        global valports
        valports = [_ for _ in self.dut_ports if self.tester.get_local_port(_) != -1]

        # Verify that enough ports are available
        self.verify(len(valports) >= 2, "Insufficent Ports")

        self.port_mask = utils.create_mask(valports)
        self.socket = self.dut.get_numa_id(self.dut_ports[0])

        self.frame_sizes = self.get_suite_cfg()["frame_size"]
        self.nb_cores = self.get_suite_cfg()["cores"]
        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip'] + HEADER_SIZE['tcp']

        # compile performance_thread app
        out = self.dut.build_dpdk_apps("./examples/performance-thread/l3fwd-thread")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

        # results table header
        self.test_results = {'header': [], 'data': []}

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

    def flows(self):
        """
        Return a list of packets that implements the flows described.
        """
        return [
            'IP(src="1.2.3.4",dst="192.18.1.0")',
            'IP(src="1.2.3.4",dst="192.18.1.1")',
            'IP(src="1.2.3.4",dst="192.18.0.0")',
            'IP(src="1.2.3.4",dst="192.18.0.1")',
            'IP(src="1.2.3.4",dst="192.18.3.0")',
            'IP(src="1.2.3.4",dst="192.18.3.1")',
            'IP(src="1.2.3.4",dst="192.18.2.0")',
            'IP(src="1.2.3.4",dst="192.18.2.1")']

    def create_cores(self, cores):

        core_config = "1S/{}C/1T".format(cores)
        core_list = self.dut.get_core_list(core_config, socket=self.socket)
        core_mask = utils.create_mask(core_list)
        return core_list, core_mask

    def config_rx_tx(self, cores, core_list):

        # config --tx and --tx params for performace thread app
        if cores == 2:
            rx = "({},{},{},{})".format(valports[0], 0, core_list[0], 0) + "," + "({},{},{},{})".format(valports[1], 0,
                                                                                                        core_list[0], 0)
            tx = "({},{})".format(core_list[1], 0)
        elif cores == 4:
            rx = "({},{},{},{})".format(valports[0], 0, core_list[0], 0) + "," + "({},{},{},{})".format(valports[1], 0,
                                                                                                        core_list[1], 1)
            tx = "({},{})".format(core_list[2], 0) + "," + "({},{})".format(core_list[3], 1)
        elif cores == 8:
            rx = "({},{},{},{})".format(valports[0], 0, core_list[0], 0) + "," + \
                 "({},{},{},{})".format(valports[0], 1, core_list[1], 1) + "," + \
                 "({},{},{},{})".format(valports[1], 0, core_list[2], 2) + "," + \
                 "({},{},{},{})".format(valports[1], 1, core_list[3], 3)
            tx = "({},{})".format(core_list[4], 0) + "," + "({},{})".format(core_list[5], 1) + "," + \
                 "({},{})".format(core_list[6], 2) + "," + "({},{})".format(core_list[7], 3)
        elif cores == 16:
            rx = "({},{},{},{})".format(valports[0], 0, core_list[0], 0) + "," + \
                 "({},{},{},{})".format(valports[0], 1, core_list[1], 1) + "," + \
                 "({},{},{},{})".format(valports[0], 2, core_list[2], 2) + "," + \
                 "({},{},{},{})".format(valports[0], 3, core_list[3], 3) + "," + \
                 "({},{},{},{})".format(valports[1], 0, core_list[4], 4) + "," + \
                 "({},{},{},{})".format(valports[1], 1, core_list[5], 5) + "," + \
                 "({},{},{},{})".format(valports[1], 2, core_list[6], 6) + "," + \
                 "({},{},{},{})".format(valports[1], 3, core_list[7], 7)
            tx = "({},{})".format(core_list[8], 0) + "," + "({},{})".format(core_list[9], 1) + "," + \
                 "({},{})".format(core_list[10], 2) + "," + "({},{})".format(core_list[11], 3) + "," + \
                 "({},{})".format(core_list[12], 4) + "," + "({},{})".format(core_list[13], 5) + "," + \
                 "({},{})".format(core_list[14], 6) + "," + "({},{})".format(core_list[15], 7)

        lcore_config = "(%s-%s)@%s" % (core_list[0], core_list[-1], core_list[0])
        return lcore_config, rx, tx

    def create_pacap_file(self, frame_size):
        """
        Prepare traffic flow
        """
        dmac = [self.dut.get_mac_address(self.dut_ports[i]) for i in valports]
        smac = ["02:00:00:00:00:0%d" % i for i in valports]
        payload_size = frame_size - HEADER_SIZE['ip'] - HEADER_SIZE['eth']
        pcaps = {}
        for _port in valports:
            index = valports[_port]
            cnt = 0
            for layer in self.flows()[_port * 2:(_port + 1) * 2]:
                flow = ['Ether(dst="%s", src="%s")/%s/("X"*%d)' % (dmac[index], smac[index], layer, payload_size)]
                pcap = os.sep.join([self.output_path, "dst{0}_{1}.pcap".format(index, cnt)])
                self.tester.scapy_append('wrpcap("%s", [%s])' % (pcap, ','.join(flow)))
                self.tester.scapy_execute()
                if index not in pcaps:
                    pcaps[index] = []
                pcaps[index].append(pcap)
                cnt += 1
        return pcaps

    def prepare_stream(self, pcaps):
        """
        create streams for ports,one port one stream
        """
        tgen_input = []
        for rxPort in valports:
            if rxPort % len(valports) == 0 or len(valports) % rxPort == 2:
                txIntf = self.tester.get_local_port(valports[rxPort + 1])
                port_id = valports[rxPort + 1]
            else:
                txIntf = self.tester.get_local_port(valports[rxPort - 1])
                port_id = valports[rxPort - 1]
            rxIntf = self.tester.get_local_port(valports[rxPort])
            for pcap in pcaps[port_id]:
                tgen_input.append((txIntf, rxIntf, pcap))
        return tgen_input

    def perf_test(self, params):

        # create result table
        header_row = ["Frame size", "S/C/T", "Throughput(Mpps)", "Line Rate(%)"]
        self.test_results["header"] = header_row
        self.result_table_create(header_row)
        self.test_results["data"] = []
        eal_param = ""
        for i in valports:
            eal_param += " -a %s" % self.dut.ports_info[i]['pci']

        for cores in self.nb_cores:
            core_list, core_mask = self.create_cores(cores)
            lcore_config, rx, tx = self.config_rx_tx(cores, core_list)
            app_name = self.dut.apps_name['l3fwd-thread']
            if self.running_case is "test_perf_n_lcore_per_pcore":
                cmdline = "{} -n 4 {} --lcores='{}' {} --rx='{}' --tx='{}'".format(app_name, eal_param, lcore_config, params, rx, tx)
            else:
                cmdline = "{} -c {} {} {} --rx='{}' --tx='{}'".format(app_name, core_mask, eal_param, params, rx, tx)
            self.dut.send_expect(cmdline, "L3FWD:", 120)

            for frame_size in self.frame_sizes:
                pcaps = self.create_pacap_file(frame_size)
                # send the traffic and Measure test
                tgenInput = self.prepare_stream(pcaps)

                vm_config = self.set_fields()
                # clear streams before add new streams
                self.tester.pktgen.clear_streams()
                # run packet generator
                streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, vm_config, self.tester.pktgen)
                # set traffic option
                traffic_opt = {'delay': 15}
                _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)
                self.verify(pps > 0, "No traffic detected")
                pps /= 1000000.0
                linerate = self.wirespeed(self.nic, frame_size, len(valports))
                percentage = pps * 100 / linerate
                data_row = [frame_size, "1S/{}C/1T".format(cores), str(pps), str(percentage)]
                self.result_table_add(data_row)
                self.test_results["data"].append(data_row)
            # stop application
            self.dut.send_expect("^C", "# ", 15)
        self.result_table_print()

    def test_perf_one_lcore_per_pcore(self):
        params = "-n 4 -- -P -p {} --enable-jumbo --max-pkt-len=2500 --no-lthread" .format(self.port_mask)
        self.perf_test(params)

    def test_perf_n_lthreads_per_pcore(self):
        params = "-n 4 -- -P -p {} --enable-jumbo --max-pkt-len=2500" .format(self.port_mask)
        self.perf_test(params)

    def test_perf_n_lcore_per_pcore(self):
        params = "-- -P -p {} --enable-jumbo --max-pkt-len 2500 --no-lthread" .format(self.port_mask)
        self.perf_test(params)

    def set_fields(self):
        """
        set ip protocol field behavior
        """
        fields_config = {'ip':  {'src': {'action': 'random'}, }, }
        return fields_config

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
