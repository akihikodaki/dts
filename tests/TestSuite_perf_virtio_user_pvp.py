# BSD LICENSE
#
# Copyright(c) 2019-2020 Intel Corporation. All rights reserved.
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
import rst
import os
import re
import time
from test_case import TestCase
from packet import Packet
from settings import UPDATE_EXPECTED, load_global_setting
from copy import deepcopy


class TestVirtioSingleCorePerf(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        # Clean the execution environment
        self.dut.send_expect("rm -rf ./vhost.out", "#")
        self.frame_sizes = [64, 1518]
        # Based on h/w type, choose how many ports to use
        self.number_of_ports = 1
        self.dut_ports = self.dut.get_ports()
        self.nb_ports = len(self.dut_ports)
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        # determine if to save test result as a separated file
        self.save_result_flag = True
        socket_num = len(set([int(core['socket']) for core in self.dut.cores]))
        self.socket_mem = ','.join(['1024']*socket_num)
        self.json_obj = dict()

    def set_up(self):
        """
        Run before each test case.
        It's more convenient to load suite configuration here than
        set_up_all in debug mode.
        """

        self.dut.send_expect('rm vhost-net*', '# ')
        # test parameters include: frames size, descriptor numbers
        self.test_parameters = self.get_suite_cfg()['test_parameters']

        # traffic duraion in second
        self.test_duration = self.get_suite_cfg()['test_duration']

        # initilize throughput attribution
        # {'$framesize':{"$nb_desc": 'throughput'}
        self.throughput = {}

        # Accepted tolerance in Mpps
        self.gap = self.get_suite_cfg()['accepted_tolerance']

        # header to print test result table
        self.table_header = ['Frame Size', 'TXD/RXD', 'Throughput', 'Rate',
                             'Expected Throughput', 'Throughput Difference']
        self.test_result = {}

    def test_perf_pvp_packed_ring_mergeable_path(self):
        """
        pvp test with packed ring mergeable path .
        """
        self.test_target = "packed_1q1c"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        self.perf_pvp_test(packed=True)
        self.handle_expected()
        self.handle_results()

    def test_perf_virtio_single_core_performance_of_packed_ring_mergeable_path(self):
        """
        virtio single core performance test with packed ring Mergeable Path.
        """
        self.test_target = "packed_virtio_single_core"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        self.perf_virtio_single_core_test(packed=True)
        self.handle_expected()
        self.handle_results()

    def test_perf_vhost_single_core_performance_of_pakced_ring_mergeable_path(self):
        """
        vhost single core performance test with packed ring Mergeable Path.
        """
        self.test_target = "packed_vhost_single_core"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        self.perf_vhost_single_core_test(packed=True)
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_split_ring_mergeble_path(self):
        """
        Benchmark performance for Vhost PVP Mergeable Path.
        """
        self.test_target = "split_1q1c"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        self.perf_pvp_test(packed=False)
        self.handle_expected()
        self.handle_results()

    def test_perf_virtio_single_core_performance_of_split_ring_mergeable_path(self):
        """
        virtio single core performance test with split ring Mergeable Path.
        """
        self.test_target = "split_virtio_single_core"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        self.perf_virtio_single_core_test(packed=False)
        self.handle_expected()
        self.handle_results()

    def test_perf_vhost_single_core_performance_of_split_ring_mergeable_path(self):
        """
        : vhost single core performance test with split ring Mergeable Path.
        """
        self.test_target = "split_vhost_single_core"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        self.perf_vhost_single_core_test(packed=False)
        self.handle_expected()
        self.handle_results()

    def perf_pvp_test(self, packed):
        core_config = "1S/4C/1T"
        core_list = self.dut.get_core_list(core_config, socket=self.socket)
        self.verify(len(core_list) >= 4, 'There no enough cores to run this case')
        self.logger.info("Executing Test Using cores: %s" % core_list)
        self.core_list_user = core_list[0:2]
        self.core_list_host = core_list[2:4]
        nb_desc = self.test_parameters[64][0]
        self.start_testpmd_as_vhost('mac', nb_desc, False)
        self.start_testpmd_as_virtio('mac', nb_desc, True, packed)
        self.send_and_verify_throughput(nb_desc)

    def perf_virtio_single_core_test(self, packed):
        """
        Vhost/virtio single core PVP test
        """
        core_config = "1S/5C/1T"
        core_list = self.dut.get_core_list(core_config, socket=self.socket)
        self.verify(len(core_list) >= 5, 'There no enough cores to run this case')
        self.logger.info("Executing Test Using cores: %s" % core_list)
        self.core_list_user = core_list[0:2]
        self.core_list_host = core_list[2:5]
        nb_desc = self.test_parameters[64][0]
        self.start_testpmd_as_vhost('io', nb_desc, False)
        self.start_testpmd_as_virtio('mac', nb_desc, True, packed)
        self.send_and_verify_throughput(nb_desc)
        
    def perf_vhost_single_core_test(self, packed):
        """
        Vhost/virtio vhost single core PVP test
        """
        core_config = "1S/5C/1T"
        core_list = self.dut.get_core_list(core_config, socket=self.socket)
        self.verify(len(core_list) >= 5, 'There no enough cores to run this case')
        self.logger.info("Executing Test Using cores: %s" % core_list)
        self.core_list_user = core_list[0:3]
        self.core_list_host = core_list[3:5]
        nb_desc = self.test_parameters[64][0]
        self.start_testpmd_as_vhost('mac', nb_desc, True)
        self.start_testpmd_as_virtio('io', nb_desc, False, packed)
        self.send_and_verify_throughput(nb_desc)

    def prepare_stream(self, frame_size):
        '''
        create streams for ports, one port two streams, and configure them.
        '''
        self.tester.pktgen.clear_streams()
        stream_ids = []
        rx_port = self.tester.get_local_port(
            self.dut_ports[0])
        tx_port = self.tester.get_local_port(
            self.dut_ports[0])
        for port in range(2):
            destination_mac = self.dut.get_mac_address(
                self.dut_ports[(port) % self.number_of_ports])
            pkt = Packet(pkt_type='IP_RAW', pkt_len=frame_size)
            pkt.config_layer('ether', {'dst': '%s' % '52:00:00:00:00:00'})
            pkt.config_layer('ipv4', {'dst': '1.1.%d.1' % port, 'src': '1.1.1.2'})
            pkt.save_pcapfile(self.tester, "%s/single_core_%d.pcap" % (self.tester.tmp_file, port))
            stream_id = self.tester.pktgen.add_stream(tx_port, rx_port,
                            "%s/single_core_%d.pcap" % (self.tester.tmp_file, port))
            stream_option = {
                'pcap': "%s/single_core_%d.pcap" % (self.tester.tmp_file, port),
                'stream_config': {'rate': 100}
            }
            self.tester.pktgen.config_stream(stream_id, stream_option)
            stream_ids.append(stream_id)
        return stream_ids

    def handle_expected(self):
        """
        Update expected numbers to configurate file: conf/$suite_name.cfg
        """
        if load_global_setting(UPDATE_EXPECTED) == "yes":
            for frame_size in self.test_parameters.keys():
                for nb_desc in self.test_parameters[frame_size]:
                    self.expected_throughput[frame_size][nb_desc] = round(self.throughput[frame_size][nb_desc], 3)

    def start_testpmd_as_vhost(self, fwd_mode, nb_desc, no_pci=False):
        if no_pci:
            eal_params = self.dut.create_eal_parameters(cores=self.core_list_host,
                            no_pci=True, prefix='vhost')
        else:
            eal_params = self.dut.create_eal_parameters(cores=self.core_list_host,
                            ports=[0], prefix='vhost')
        command_line_client = self.target + "/app/testpmd %s " + \
                        "--socket-mem 1024,1024 "  \
                        "--vdev 'net_vhost0,iface=vhost-net,queues=1' " + \
                        "-- -i --nb-cores=%d  --txd=%d --rxd=%d"
        command_line_client = command_line_client % (eal_params, len(self.core_list_host)-1,
                                nb_desc, nb_desc)
        self.dut.send_expect(command_line_client, "testpmd> ", 120)
        self.dut.send_expect("set fwd %s" % fwd_mode, "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)

    def start_testpmd_as_virtio(self, fwd_mode, nb_desc, no_pci=True, packed_ring=False):
        # launch virtio
        if no_pci:
            eal_params = self.dut.create_eal_parameters(cores=self.core_list_user,
                    no_pci=True, prefix='virtio')
        else:
            eal_params = self.dut.create_eal_parameters(cores=self.core_list_user,
                    ports=[0], prefix='virtio')
                
        command_line_server = self.target + "/app/testpmd %s " + \
                        "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=%d,mrg_rxbuf=1,in_order=0  " + \
                        "-- -i --nb-cores=%d --tx-offloads=0x0 --enable-hw-vlan-strip --txd=%d --rxd=%d"
        command_line_server = command_line_server % (eal_params, int(packed_ring),
                        len(self.core_list_user)-1, nb_desc, nb_desc)
        self.vhost_user = self.dut.new_session(suite="user")
        self.vhost_user.send_expect(command_line_server, "testpmd> ", 120)
        self.vhost_user.send_expect("set fwd %s" % fwd_mode, "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def send_and_verify_throughput(self, nb_desc):
        for frame_size in self.frame_sizes:
            self.throughput[frame_size] = dict()
            self.logger.info("Test running at parameters: " +
                "framesize: {}, rxd/txd: {}".format(frame_size, nb_desc))
            stream_ids = self.prepare_stream(frame_size)
            traffic_opt = {
                'method': 'throughput',
                'rate': 100,
                'duration': 20}
            _, pps = self.tester.pktgen.measure(stream_ids, traffic_opt)
            Mpps = pps / 1000000.0
            self.verify(Mpps > 0, "%s can not receive packets of frame size %d" % (self.running_case, frame_size))
            throughput = Mpps * 100 / \
                         float(self.wirespeed(self.nic, frame_size, self.number_of_ports))
            self.throughput[frame_size][nb_desc] = Mpps
            self.verify(throughput,
                "No traffic detected, please check your configuration")
            self.logger.info("Trouthput of " +
                "framesize: {}, rxd/txd: {} is :{} Mpps".format(
                    frame_size, nb_desc, Mpps))

        
    def handle_results(self):
        """
        results handled process:
        1, save to self.test_results
        2, create test results table
        3, save to json file for Open Lab
        """
        header = self.table_header
        for frame_size in self.test_parameters.keys():
            wirespeed = self.wirespeed(self.nic, frame_size, self.nb_ports)
            ret_datas = {}
            for nb_desc in self.test_parameters[frame_size]:
                ret_data = {}
                ret_data[header[0]] = frame_size
                ret_data[header[1]] = nb_desc
                ret_data[header[2]] = "{:.3f} Mpps".format(
                    self.throughput[frame_size][nb_desc])
                ret_data[header[3]] = "{:.3f}%".format(
                    self.throughput[frame_size][nb_desc] * 100 / wirespeed)
                ret_data[header[4]] = "{:.3f} Mpps".format(
                    self.expected_throughput[frame_size][nb_desc])
                ret_data[header[5]] = "{:.3f} Mpps".format(
                    self.throughput[frame_size][nb_desc] -
                        self.expected_throughput[frame_size][nb_desc])
                ret_datas[nb_desc] = deepcopy(ret_data)
            self.test_result[frame_size] = deepcopy(ret_datas)
        # Create test results table
        self.result_table_create(header)
        for frame_size in self.test_parameters.keys():
            for nb_desc in self.test_parameters[frame_size]:
                table_row = list()
                for i in range(len(header)):
                    table_row.append(
                        self.test_result[frame_size][nb_desc][header[i]])
                self.result_table_add(table_row)
        # present test results to screen
        self.result_table_print()
        # save test results as a file
        if self.save_result_flag:
            self.save_result(self.test_result)

    def save_result(self, data):
        '''
        Saves the test results as a separated file named with
        self.nic+_perf_virtio_user_pvp.json in output folder
        if self.save_result_flag is True
        '''
        case_name = self.running_case
        self.json_obj[case_name] = list()
        status_result = []
        for frame_size in self.test_parameters.keys():
            for nb_desc in self.test_parameters[frame_size]:
                row_in = self.test_result[frame_size][nb_desc]
                row_dict0 = dict()
                row_dict0['performance'] = list()
                row_dict0['parameters'] = list()
                row_dict0['parameters'] = list()
                result_throughput = float(row_in['Throughput'].split()[0])
                expected_throughput = float(row_in['Expected Throughput'].split()[0])
                # delta value and accepted tolerance in percentage
                delta = result_throughput - expected_throughput
                gap = expected_throughput * -self.gap * 0.01
                delta = float(delta)
                gap = float(gap)
                self.logger.info("Accept tolerance are (Mpps) %f" % gap)
                self.logger.info("Throughput Difference are (Mpps) %f" % delta)
                if result_throughput > expected_throughput + gap:
                    row_dict0['status'] = 'PASS'
                else:
                    row_dict0['status'] = 'FAIL'
                self.verify(row_dict0['status'] == 'PASS', 'The throughput is not in correct range')
                row_dict1 = dict(name="Throughput", value=result_throughput, unit="Mpps", delta=delta)
                row_dict2 = dict(name="Txd/Rxd", value=row_in["TXD/RXD"], unit="descriptor")
                row_dict3 = dict(name="frame_size", value=row_in["Frame Size"], unit="bytes")
                row_dict0['performance'].append(row_dict1)
                row_dict0['parameters'].append(row_dict2)
                row_dict0['parameters'].append(row_dict3)
                self.json_obj[case_name].append(row_dict0)
                status_result.append(row_dict0['status'])
        with open(os.path.join(rst.path2Result,
                               '{0:s}_{1}.json'.format(
                                   self.nic, self.suite_name)), 'w') as fp:
            json.dump(self.json_obj, fp)
        self.verify("Fail" not in status_result, "Exceeded Gap")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)
        self.vhost_user.send_expect("stop", "testpmd> ")
        self.vhost_user.send_expect("quit", "# ", 30)
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
