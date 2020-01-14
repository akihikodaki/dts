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
Test vhost/virtio-user loopback multi-queues on 9 tx/rx path.
Includes split ring mergeable, non-mergeable, Vector_RX, Inorder mergeable,
Inorder non-mergeable, packed ring mergeable, non-mergeable, inorder mergeable,
inorder non-mergeable Path.
"""

import utils
import time
import re
import json
import rst
import os
from copy import deepcopy
from test_case import TestCase
from settings import UPDATE_EXPECTED, load_global_setting


class TestPerfVirtioUserLoopback(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.frame_sizes = [64, 1518]
        self.nb_ports = 1
        self.nb_cores = 1
        self.queue_number = 1
        cores_num = len(set([int(core['socket']) for core in self.dut.cores]))
        # set diff arg about mem_socket base on socket number
        self.socket_mem = ','.join(['1024']*cores_num)
        self.core_config = "1S/4C/1T"
        self.verify(len(self.core_config) >= 4,
                        "There has not enought cores to test this suite")
        self.core_list = self.dut.get_core_list(self.core_config)
        self.core_list_user = self.core_list[0:2]
        self.core_list_host = self.core_list[2:4]

        self.vhost = self.dut.new_session(suite="vhost")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.save_result_flag = True

    def set_up(self):
        """
        Run before each test case.
        It's more convenient to load suite configuration here than
        set_up_all in debug mode.
        """
        self.dut.send_expect('rm ./vhost-net*', '# ')
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
        # get the frame_sizes from cfg file
        if 'packet_sizes' in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()['packet_sizes']

    def start_vhost_testpmd(self, nb_desc):
        """
        start testpmd on vhost
        """
        eal_params = self.dut.create_eal_parameters(cores=self.core_list_host,
                        no_pci=True, prefix='vhost')
        command_line_client = self.dut.target + "/app/testpmd %s " + \
                              "--socket-mem %s --legacy-mem  --vdev " + \
                              "'net_vhost0,iface=vhost-net,queues=%d' -- -i --nb-cores=%d " + \
                              "--rxq=%d --txq=%d --txd=%d --rxd=%d"
        command_line_client = command_line_client % (
            eal_params, self.socket_mem, self.queue_number,
            self.nb_cores, self.queue_number, self.queue_number,
            nb_desc, nb_desc)
        self.vhost.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost.send_expect("set fwd mac", "testpmd> ", 120)

    def start_virtio_testpmd(self, nb_desc, args):
        """
        start testpmd on virtio
        """
        eal_params = self.dut.create_eal_parameters(cores=self.core_list_user,
                        no_pci=True, prefix='virtio')
        command_line_user = self.dut.target + "/app/testpmd %s " + \
                            " --socket-mem %s --legacy-mem " + \
                            "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=%d,%s " + \
                            "-- -i %s --rss-ip --nb-cores=%d --rxq=%d --txq=%d --txd=%d --rxd=%d"
        command_line_user = command_line_user % (
            eal_params, self.socket_mem,
            self.queue_number, args["version"], args["path"], self.nb_cores,
            self.queue_number, self.queue_number, nb_desc, nb_desc)
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd mac", "testpmd> ", 120)
        self.virtio_user.send_expect("start", "testpmd> ", 120)

    def calculate_avg_throughput(self):
        """
        calculate the average throughput
        """
        results = 0.0
        results_row = []
        for i in range(10):
            out = self.vhost.send_expect("show port stats all", "testpmd>", 60)
            time.sleep(5)
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 10)
        self.verify(Mpps > 0, "port can not receive packets")
        return Mpps

    def send_and_verify(self, nb_desc, case_info):
        """
        start to send packets and calculate avg throughput
        """
        for frame_size in self.frame_sizes:
            self.throughput[frame_size] = dict()
            self.vhost.send_expect("set txpkts %d" % frame_size, "testpmd> ", 30)
            self.vhost.send_expect("start tx_first 32", "testpmd> ", 30)
            Mpps = self.calculate_avg_throughput()
            self.verify(Mpps > 0, "%s can not receive packets of frame size %d" % (self.running_case, frame_size))
            self.throughput[frame_size][nb_desc] = Mpps
            self.logger.info("Trouthput of " +
                             "framesize: {}, rxd/txd: {} is :{} Mpps".format(
                                 frame_size, nb_desc, Mpps))
            self.vhost.send_expect("stop", "testpmd> ", 60)

    def close_all_testpmd(self):
        """
        close all testpmd of vhost and virtio
        """
        self.vhost.send_expect("quit", "#", 60)
        self.virtio_user.send_expect("quit", "#", 60)

    def close_all_session(self):
        """
        close all session of vhost and vhost-user
        """
        self.dut.close_session(self.vhost)
        self.dut.close_session(self.virtio_user)

    def handle_expected(self):
        """
        Update expected numbers to configurate file: conf/$suite_name.cfg
        """
        if load_global_setting(UPDATE_EXPECTED) == "yes":
            for frame_size in self.test_parameters.keys():
                for nb_desc in self.test_parameters[frame_size]:
                    self.expected_throughput[frame_size][nb_desc] = round(self.throughput[frame_size][nb_desc],3)

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
        self.nic+_single_core_perf.json in output folder
        if self.save_result_flag is True
        '''
        json_obj = dict()
        case_name = self.running_case
        json_obj[case_name] = list()
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
                delta=float(delta)
                gap=float(gap)
                self.logger.info("Accept tolerance of %d are (Mpps) %f" %(frame_size, gap))
                self.logger.info("Throughput Difference of %d are (Mpps) %f" %(frame_size, delta))
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
                json_obj[case_name].append(row_dict0)
                status_result.append(row_dict0['status'])
        with open(os.path.join(rst.path2Result,
                               '{0:s}_vhost_loopback_performance_virtio_user.json'.format(
                                   self.nic)), 'w') as fp:
            json.dump(json_obj, fp)
        self.verify("Fail" not in status_result, "Exceeded Gap")

    def test_perf_loopback_packed_ring_inorder_mergeable(self):
        """
        performance for Vhost PVP virtio 1.1 inorder mergeable Path.
        """
        virtio_pmd_arg = {"version": "in_order=1,packed_vq=1,mrg_rxbuf=1",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.test_target = "packed_ring_inorder_mergeable"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        nb_desc = self.test_parameters[64][0]
        self.start_vhost_testpmd(nb_desc)
        self.start_virtio_testpmd(nb_desc, virtio_pmd_arg)
        self.send_and_verify(nb_desc, "virtio_1.1 mergeable on")
        self.close_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_loopback_packed_ring_inorder_non_mergeable(self):
        """
        performance for Vhost PVP virtio1.1 inorder non-mergeable Path.
        """
        self.test_target = "packed_ring_inorder_non-mergeable"
        virtio_pmd_arg = {"version": "in_order=1,packed_vq=1,mrg_rxbuf=0",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        nb_desc = self.test_parameters[64][0]
        self.start_vhost_testpmd(nb_desc)
        self.start_virtio_testpmd(nb_desc, virtio_pmd_arg)
        self.send_and_verify(nb_desc, "virtio_1.1 normal")
        self.close_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_loopback_packed_ring_mergeable(self):
        """
        performance for Vhost PVP virtio 1.1 Mergeable Path.
        """
        virtio_pmd_arg = {"version": "in_order=0,packed_vq=1,mrg_rxbuf=1",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.test_target = "packed_ring_mergeable"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        nb_desc = self.test_parameters[64][0]
        self.start_vhost_testpmd(nb_desc)
        self.start_virtio_testpmd(nb_desc, virtio_pmd_arg)
        self.send_and_verify(nb_desc, "virtio_1.1 mergeable on")
        self.close_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_loopback_packed_ring_non_mergeable(self):
        """
        performance for Vhost PVP virtio1.1 non-mergeable Path.
        """
        self.test_target = "packed_ring_non-mergeable"
        virtio_pmd_arg = {"version": "in_order=0,packed_vq=1,mrg_rxbuf=0",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        nb_desc = self.test_parameters[64][0]
        self.start_vhost_testpmd(nb_desc)
        self.start_virtio_testpmd(nb_desc, virtio_pmd_arg)
        self.send_and_verify(nb_desc, "virtio_1.1 normal")
        self.close_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_loopback_split_ring_inorder_mergeable(self):
        """
        performance for Vhost PVP In_order Mergeable Path.
        """
        self.test_target = "split_ring_inorder_mergeable"
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=1,mrg_rxbuf=1",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        nb_desc = self.test_parameters[64][0]
        self.start_vhost_testpmd(nb_desc)
        self.start_virtio_testpmd(nb_desc, virtio_pmd_arg)
        self.send_and_verify(nb_desc, "inorder mergeable on")
        self.close_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_loopback_split_ring_inorder_non_mergeable(self):
        """
        performance for Vhost PVP Inorder Non-mergeable Path.
        """
        self.test_target = "split_ring_inorder_non-mergeable"
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=1,mrg_rxbuf=0",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        nb_desc = self.test_parameters[64][0]
        self.start_vhost_testpmd(nb_desc)
        self.start_virtio_testpmd(nb_desc, virtio_pmd_arg)
        self.send_and_verify(nb_desc, "inorder mergeable off")
        self.close_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_loopback_split_ring_mergeable(self):
        """
        performance for Vhost PVP Mergeable Path.
        """
        self.test_target = "split_ring_mergeable"
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=1",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        nb_desc = self.test_parameters[64][0]
        self.start_vhost_testpmd(nb_desc)
        self.start_virtio_testpmd(nb_desc, virtio_pmd_arg)
        self.send_and_verify(nb_desc, "virtio mergeable")
        self.close_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_loopback_split_ring_non_mergeable(self):
        """
        performance for Vhost PVP Non-mergeable Path.
        """
        self.test_target = "split_ring_non-mergeable"
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=0",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        nb_desc = self.test_parameters[64][0]
        self.start_vhost_testpmd(nb_desc)
        self.start_virtio_testpmd(nb_desc, virtio_pmd_arg)
        self.send_and_verify(nb_desc, "virtio mergeable off")
        self.close_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_loopback_split_ring_vector_rx(self):
        """
        performance for Vhost PVP Vector_RX Path
        """
        self.test_target = "split_ring_vector_rx"
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=0",
                          "path": "--tx-offloads=0x0"}
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        nb_desc = self.test_parameters[64][0]
        self.start_vhost_testpmd(nb_desc)
        self.start_virtio_testpmd(nb_desc, virtio_pmd_arg)
        self.send_and_verify(nb_desc, "virtio vector rx")
        self.close_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.close_all_session()
