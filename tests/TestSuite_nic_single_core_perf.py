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
import string
from test_case import TestCase
from exception import VerifyFailure
from settings import HEADER_SIZE, UPDATE_EXPECTED, load_global_setting
from pmd_output import PmdOutput
from copy import deepcopy
from numpy import mean
import rst
from pktgen import PacketGeneratorHelper


class TestNicSingleCorePerf(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        PMD prerequisites.
        """
        self.verify(self.nic in ['niantic', 'fortville_25g', 'fortville_spirit', 'ConnectX5_MT4121',
                                 'ConnectX4_LX_MT4117', 'columbiaville_100g', 'columbiaville_25g', 'columbiaville_25gx2',
                                 'brcm_57414', 'brcm_P2100G'],
                                 "Not required NIC ")
        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip']

        self.rx_desc_size = self.get_suite_cfg().get('rx_desc_size', 32)
        err_msg = "Rx desc only has 16B and 32B size, %d is not valid" % self.rx_desc_size
        self.verify(self.rx_desc_size == 16 or self.rx_desc_size == 32, err_msg)
        if self.rx_desc_size == 16:
            # Update DPDK config file and rebuild to get best perf on fortville
            if self.nic in ["fortville_25g", "fortville_spirit"]:
                self.dut.set_build_options({'RTE_LIBRTE_I40E_16BYTE_RX_DESC': 'y'})
            elif self.nic in ["columbiaville_100g", "columbiaville_25g", "columbiaville_25gx2"]:
                self.dut.set_build_options({'RTE_LIBRTE_ICE_16BYTE_RX_DESC': 'y'})
            self.dut.build_install_dpdk(self.target)

        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports()
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.pmdout = PmdOutput(self.dut)

        # determine if to save test result as a separated file
        self.save_result_flag = True

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
        It's more convenient to load suite configuration here than
        set_up_all in debug mode.
        """

        # test parameters include: frames size, descriptor numbers
        self.test_parameters = self.get_suite_cfg()['test_parameters']

        # traffic duraion in second
        self.test_duration = self.get_suite_cfg()['test_duration']
        self.throughput_stat_sample_interval = self.get_suite_cfg().get('throughput_stat_sample_interval', 5)

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

        # Accepted tolerance is ratio
        self.gap = self.get_suite_cfg().get('accepted_tolerance', 0.1)

        # header to print test result table
        self.table_header = ['Fwd_core', 'Frame Size', 'TXD/RXD', 'Real-Mpps', 'Rate',
                             'Expected-Mpps', 'Fluc Ratio', 'Status']
        self.test_result = {}

    def flows(self):
        """
        Return a list of packets that implements the flows described in l3fwd.
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

    def create_pacap_file(self, frame_size, port_num):
        """
        Prepare traffic flow
        """
        payload_size = frame_size - HEADER_SIZE['ip'] - HEADER_SIZE['eth']
        pcaps = {}
        for _port in self.dut_ports:
            if 1 == port_num:
                flow = ['Ether(src="52:00:00:00:00:00")/%s/("X"*%d)' % (self.flows()[_port], payload_size)]
                pcap = os.sep.join([self.output_path, "dst{0}.pcap".format(_port)])
                self.tester.scapy_append('wrpcap("%s", [%s])' % (pcap, ','.join(flow)))
                self.tester.scapy_execute()
                pcaps[_port] = []
                pcaps[_port].append(pcap)
            else:
                index = self.dut_ports[_port]
                cnt = 0
                for layer in self.flows()[_port * 2:(_port + 1) * 2]:
                    flow = ['Ether(src="52:00:00:00:00:00")/%s/("X"*%d)' % (layer, payload_size)]
                    pcap = os.sep.join([self.output_path, "dst{0}_{1}.pcap".format(index, cnt)])
                    self.tester.scapy_append('wrpcap("%s", [%s])' % (pcap, ','.join(flow)))
                    self.tester.scapy_execute()
                    if index not in pcaps:
                        pcaps[index] = []
                    pcaps[index].append(pcap)
                    cnt += 1
        return pcaps

    def prepare_stream(self, pcaps, port_num):
        """
        create streams for ports,one port one stream
        """
        tgen_input = []
        if 1 == port_num:
            txIntf = self.tester.get_local_port(self.dut_ports[0])
            rxIntf = txIntf
            for pcap in pcaps[0]:
                tgen_input.append((txIntf, rxIntf, pcap))
        else:
            for rxPort in range(port_num):
                if rxPort % port_num == 0 or rxPort ** 2 == port_num:
                    txIntf = self.tester.get_local_port(self.dut_ports[rxPort + 1])
                    port_id = self.dut_ports[rxPort + 1]
                else:
                    txIntf = self.tester.get_local_port(self.dut_ports[rxPort - 1])
                    port_id = self.dut_ports[rxPort - 1]
                rxIntf = self.tester.get_local_port(self.dut_ports[rxPort])
                for pcap in pcaps[port_id]:
                    tgen_input.append((txIntf, rxIntf, pcap))
        return tgen_input

    def test_perf_nic_single_core(self):
        """
        Run nic single core performance
        """
        self.nb_ports = len(self.dut_ports)
        self.verify(self.nb_ports >= 1, "At least 1 port is required to test")
        self.perf_test(self.nb_ports)
        self.handle_expected()
        self.handle_results()

    def handle_expected(self):
        """
        Update expected numbers to configurate file: conf/$suite_name.cfg
        """
        if load_global_setting(UPDATE_EXPECTED) == "yes":
            for fwd_config in list(self.test_parameters.keys()):
                for frame_size in list(self.test_parameters[fwd_config].keys()):
                    for nb_desc in self.test_parameters[fwd_config][frame_size]:
                        self.expected_throughput[fwd_config][frame_size][nb_desc] = \
                            round(self.throughput[fwd_config][frame_size][nb_desc], 3)

    def perf_test(self, port_num):
        """
        Single core Performance Benchmarking test
        """
        # ports allowlist
        eal_para = ""
        for i in range(port_num):
            eal_para += " -w " + self.dut.ports_info[i]['pci']

        port_mask = utils.create_mask(self.dut_ports)

        for fwd_config in list(self.test_parameters.keys()):
            # parameters for application/testpmd
            param = " --portmask=%s" % (port_mask)
            # the fwd_config just the config for fwd core
            # to start testpmd should add 1C to it
            core_config = '1S/%s' % fwd_config
            thread_num = int(fwd_config[fwd_config.find('/')+1: fwd_config.find('T')])
            core_list = self.dut.get_core_list(core_config, socket=self.socket)
            self.verify(len(core_list) >= thread_num, "the Hyper-threading not open, please open it to test")

            # need add one more core for start testpmd
            core_list = [core_list[0]] + [str(int(i) + 1) for i in core_list]

            self.logger.info("Executing Test Using cores: %s of config %s" % (core_list, fwd_config))

            nb_cores = thread_num

            # fortville has to use 2 queues at least to get the best performance
            if self.nic in ["fortville_25g", "fortville_spirit"] or thread_num == 2:
                param += " --rxq=2 --txq=2"
            # columbiaville use one queue per port for best performance.
            elif self.nic in ["columbiaville_100g", "columbiaville_25g", "columbiaville_25gx2"]:
                param += " --rxq=1 --txq=1"
                # workaround for that testpmd can't forward packets in io forward mode
                param += " --port-topology=loop"
            # improves performance and reduces fluctuations
            elif self.nic in ['ConnectX5_MT4121', 'ConnectX4_LX_MT4117']:
                param += " --burst=64 --mbcache=512"

            self.throughput[fwd_config] = dict()
            for frame_size in list(self.test_parameters[fwd_config].keys()):
                self.throughput[fwd_config][frame_size] = dict()
                pcaps = self.create_pacap_file(frame_size, port_num)
                tgenInput = self.prepare_stream(pcaps, port_num)
                for nb_desc in self.test_parameters[fwd_config][frame_size]:
                    self.logger.info("Test running at parameters: " +
                        "framesize: {}, rxd/txd: {}".format(frame_size, nb_desc))
                    parameter = param + " --txd=%d --rxd=%d --nb-cores=%d" % (nb_desc, nb_desc, nb_cores)
                    self.pmdout.start_testpmd(
                        core_list, parameter, eal_para, socket=self.socket)
                    self.dut.send_expect("start", "testpmd> ", 15)

                    vm_config = self.set_fields()
                    # clear streams before add new streams
                    self.tester.pktgen.clear_streams()

                    # run packet generator
                    streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, vm_config, self.tester.pktgen)
                    # set traffic option
                    traffic_opt = {
                        'method': 'throughput',
                        'rate': 100,
                        'duration': self.test_duration,
                        'interval': self.throughput_stat_sample_interval,
                        }
                    stats = self.tester.pktgen.measure(stream_ids=streams, traffic_opt=traffic_opt)

                    #####################################################
                    # Remove max and min if count >=5, then get average
                    #####################################################
                    if isinstance(stats, list):
                        total_pps_rxs = []
                        c = len(stats)
                        for i in range(c):
                            stats_pps = stats[i][1]
                            if isinstance(stats_pps, tuple):
                                total_pps_rxs.append(stats_pps[1])
                            else:
                                total_pps_rxs.append(stats_pps)
                        if c >= 5:
                            total_pps_rxs.remove(max(total_pps_rxs))
                            total_pps_rxs.remove(min(total_pps_rxs))
                        total_pps_rx = mean(total_pps_rxs)
                    else:
                        total_pps_rx = stats

                    self.verify(total_pps_rx > 0, "No traffic detected, please check your configuration")
                    total_mpps_rx = total_pps_rx / 1000000.0
                    self.throughput[fwd_config][frame_size][nb_desc] = total_mpps_rx

                    self.dut.send_expect("stop", "testpmd> ")
                    self.dut.send_expect("quit", "# ", 30)

                    self.logger.info("Trouthput of " +
                        "framesize: {}, rxd/txd: {} is :{} Mpps".format(
                            frame_size, nb_desc, total_mpps_rx))

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
        for fwd_config in list(self.test_parameters.keys()):
            ret_datas = {}
            for frame_size in list(self.test_parameters[fwd_config].keys()):
                wirespeed = self.wirespeed(self.nic, frame_size, self.nb_ports)
                ret_datas[frame_size] = {}
                for nb_desc in self.test_parameters[fwd_config][frame_size]:
                    ret_data = {}
                    ret_data[header[0]] = fwd_config
                    ret_data[header[1]] = frame_size
                    ret_data[header[2]] = nb_desc
                    _real = self.throughput[fwd_config][frame_size][nb_desc]
                    _exp = self.expected_throughput[fwd_config][frame_size][nb_desc]
                    ret_data[header[3]] = "{:.3f}".format(_real)
                    ret_data[header[4]] = "{:.3f}%".format(_real * 100 / wirespeed)
                    ret_data[header[5]] = "{:.3f}".format(_exp)
                    delta = (_real - _exp)/_exp
                    if _exp != 0:
                        ret_data[header[6]] = "{:.3f}".format(delta)
                        if delta > -self.gap:
                            ret_data[header[7]] = 'PASS'
                        else:
                            ret_data[header[7]] = 'FAIL'
                    else:
                        ret_data[header[6]] = "N/A"
                        ret_data[header[7]] = 'PASS'

                    ret_datas[frame_size][nb_desc] = deepcopy(ret_data)
                self.test_result[fwd_config] = deepcopy(ret_datas)

        # Create test results table
        self.result_table_create(header)
        for fwd_config in list(self.test_parameters.keys()):
            for frame_size in list(self.test_parameters[fwd_config].keys()):
                for nb_desc in self.test_parameters[fwd_config][frame_size]:
                    table_row = list()
                    for i in range(len(header)):
                        table_row.append(
                            self.test_result[fwd_config][frame_size][nb_desc][header[i]])
                    self.result_table_add(table_row)
        # present test results to screen
        self.result_table_print()

        # save test results as a file
        if self.save_result_flag:
            self.save_result(self.test_result)

    def save_result(self, data):
        '''
        Saves the test results as a separated file named with
        self.nic+_single_core_perf.json in output folder
        if self.save_result_flag is True
        '''
        json_obj = dict()
        case_name = self.running_case
        json_obj[case_name] = list()
        status_result = []
        for fwd_config in list(self.test_parameters.keys()):
            for frame_size in list(self.test_parameters[fwd_config].keys()):
                for nb_desc in self.test_parameters[fwd_config][frame_size]:
                    row_in = self.test_result[fwd_config][frame_size][nb_desc]
                    row_dict0 = dict()
                    row_dict0['performance'] = list()
                    row_dict0['parameters'] = list()
                    row_dict0['status'] = row_in['Status']
                    row_dict1 = dict(name="Throughput", value=row_in['Real-Mpps'], unit="Mpps",
                                     delta=row_in['Fluc Ratio'], expected=row_in['Expected-Mpps'])
                    row_dict2 = dict(name="Txd/Rxd", value=row_in["TXD/RXD"], unit="descriptor")
                    row_dict3 = dict(name="frame_size", value=row_in["Frame Size"], unit="bytes")
                    row_dict4 = dict(name="Fwd_core", value=row_in["Fwd_core"])
                    row_dict0['performance'].append(row_dict1)
                    row_dict0['parameters'].append(row_dict2)
                    row_dict0['parameters'].append(row_dict3)
                    row_dict0['parameters'].append(row_dict4)
                    json_obj[case_name].append(row_dict0)
                    status_result.append(row_dict0['status'])

        json_file = os.path.join(rst.path2Result, '{0:s}_single_core_perf.json'.format(self.nic))
        with open(json_file, 'w') as fp:
            json.dump(json_obj, fp, indent=4, separators=(',', ': '), sort_keys=True)

        self.verify("FAIL" not in status_result, "Excessive gap between test results and expectations")

    def set_fields(self):
        """
        set ip protocol field behavior
        """
        fields_config = {'ip': {'src': {'action': 'random'}, }, }
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
        # resume setting
        if self.rx_desc_size == 16:
            if self.nic in ["fortville_25g", "fortville_spirit"]:
                self.dut.set_build_options({'RTE_LIBRTE_I40E_16BYTE_RX_DESC': 'n'})
            elif self.nic in ["columbiaville_100g", "columbiaville_25g", "columbiaville_25gx2"]:
                self.dut.set_build_options({'RTE_LIBRTE_ICE_16BYTE_RX_DESC': 'n'})
            self.dut.build_install_dpdk(self.target)
        self.dut.kill_all()
