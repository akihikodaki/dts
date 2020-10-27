# BSD LICENSE
#
# Copyright(c) <2020> Intel Corporation.
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

vm2vm split ring and packed ring with tx offload (TSO and UFO) with non-mergeable path.
vm2vm split ring and packed ring with UFO about virtio-net device capability with non-mergeable path.
vm2vm split ring and packed ring vhost-user/virtio-net check the payload of large packet is valid with
mergeable and non-mergeable dequeue zero copy.
please use qemu version greater 4.1.94 which support packed feathur to test this suite.
"""
import re
import os
import rst
import json
import time
import string
import random
from virt_common import VM
from test_case import TestCase
from pmd_output import PmdOutput
from settings import UPDATE_EXPECTED, load_global_setting
from copy import deepcopy


class TestPerfVM2VMVirtioNetPerf(TestCase):
    def set_up_all(self):
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        # get core mask
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_list = self.dut.get_core_list('all', socket=self.ports_socket)
        self.verify(len(self.cores_list) >= 4,
                    "There has not enough cores to test this suite %s" %
                    self.suite_name)
        self.vm_num = 2
        self.virtio_ip1 = "1.1.1.2"
        self.virtio_ip2 = "1.1.1.3"
        self.virtio_mac1 = "52:54:00:00:00:01"
        self.virtio_mac2 = "52:54:00:00:00:02"
        self.base_dir = self.dut.base_dir.replace('~', '/root')
        self.random_string = string.ascii_letters + string.digits
        socket_num = len(set([int(core['socket']) for core in self.dut.cores]))
        self.socket_mem = ','.join(['2048']*socket_num)
        self.vhost = self.dut.new_session(suite="vhost")
        self.pmd_vhost = PmdOutput(self.dut, self.vhost)
        self.json_obj = dict()
        self.save_result_flag = True
        self.path=self.dut.apps_name['test-pmd']
        if self.dut.build_type == 'meson':
            self.build_pmd_bond(self.dut)

    def set_up(self):
        """
        run before each test case.
        """
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vm_dut = []
        self.vm = []
        self.gap = self.get_suite_cfg()['accepted_tolerance']
        self.test_duration = self.get_suite_cfg()['test_duration']
        self.test_parameter = self.get_suite_cfg()['test_parameters']
        self.test_result = {}
        self.table_header = ['Mode', 'Type', 'TXD/RXD', 'Throughput', 'Expected Throughput',
                             'Throughput Difference']

    def build_pmd_bond(self, user_dut):
        user_dut.set_build_options({'RTE_MEMCPY_AVX512': 'y'})
        user_dut.build_install_dpdk(self.target)

    def restore_env(self, user_dut):
        user_dut.build_install_dpdk(self.target)

    def handle_expected(self):
        """
        Update expected numbers to configurate file: conf/$suite_name.cfg
        """
        if load_global_setting(UPDATE_EXPECTED) == "yes":
            self.expected_throughput[self.test_parameter] = self.throughput

    def handle_results(self):
        header = self.table_header
        ret_data = {}
        ret_data[header[0]] = 'vm2vm'
        ret_data[header[1]] = 'iperf'
        ret_data[header[2]] = self.test_parameter
        ret_data[header[3]] = self.throughput
        ret_data[header[4]] = self.expected_throughput[self.test_parameter]
        expected = re.search('(.*\d)(\s?.+)', self.expected_throughput[self.test_parameter])
        self.expected_data = float(expected.group(1))
        self.expect_unit = expected.group(2).strip()
        self.verify(self.throughput_unit == self.expect_unit, "data unit not correct, expect: %s, result: %s" % (self.expect_unit, self.throughput_unit))
        self.gap_data = round((self.throughput_data - self.expected_data), 3)
        ret_data[header[5]] = str(self.gap_data) + ' ' + self.expect_unit
        self.test_result = deepcopy(ret_data)
        self.result_table_create(header)
        self.result_table_add(list(self.test_result.values()))
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
        row_in = data
        row_dict0 = dict()
        row_dict0['performance'] = list()
        row_dict0['parameters'] = list()
        gap = self.expected_data * -float(self.gap) * 0.01

        self.logger.info("Accept tolerance are %0.3f %s" % (gap, self.expect_unit))
        self.logger.info("Throughput Difference are %0.3f %s" % (self.gap_data, self.expect_unit))
        if self.throughput_data > self.expected_data + gap:
            row_dict0['status'] = 'PASS'
        else:
            row_dict0['status'] = 'FAIL'
        row_dict1 = dict(name="Throughput", value=self.throughput_data, unit=self.throughput_unit, delta=self.gap_data)
        row_dict2 = dict(name="Txd/Rxd", value=row_in["TXD/RXD"], unit="descriptor")
        row_dict0['performance'].append(row_dict1)
        row_dict0['parameters'].append(row_dict2)
        self.json_obj[case_name].append(row_dict0)
        status_result.append(row_dict0['status'])
        with open(os.path.join(rst.path2Result,
                               '{0:s}_{1}.json'.format(
                                   self.nic, self.suite_name)), 'w') as fp:
            json.dump(self.json_obj, fp)

        self.verify("FAIL" not in status_result, "Exceeded Gap")

    def start_vhost_testpmd(self, zerocopy=False):
        """
        launch the testpmd with different parameters
        """
        if zerocopy is True:
            zerocopy_arg = ",dequeue-zero-copy=1"
        else:
            zerocopy_arg = ""
        vdev1 = "--vdev 'net_vhost0,iface=%s/vhost-net0,queues=1%s' " % (self.base_dir, zerocopy_arg)
        vdev2 = "--vdev 'net_vhost1,iface=%s/vhost-net1,queues=1%s' " % (self.base_dir, zerocopy_arg)
        eal_params = self.dut.create_eal_parameters(cores=self.cores_list, prefix='vhost', no_pci=True)
        para = " -- -i --nb-cores=2 --txd=1024 --rxd=1024"
        self.command_line = self.path + eal_params + vdev1 + vdev2 + para
        self.pmd_vhost.execute_cmd(self.command_line, timeout=30)
        self.pmd_vhost.execute_cmd('start', timeout=30)

    def start_vms(self, mode="mergeable", packed=False):
        """
        start two VM, each VM has one virtio device
        """
        setting_args = "mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        if mode == "ufo":
            setting_args += ",guest_ufo=on,host_ufo=on"
        elif mode == "mergeable":
            setting_args = "mrg_rxbuf=on"
        elif mode == "normal":
            setting_args = "mrg_rxbuf=off"
        if packed is True:
            setting_args = "%s,packed=on" % setting_args

        for i in range(self.vm_num):
            vm_dut = None
            vm_info = VM(self.dut, 'vm%d' % i, 'vhost_sample')
            vm_params = {}
            vm_params['driver'] = 'vhost-user'
            vm_params['opt_path'] = self.base_dir + '/vhost-net%d' % i
            vm_params['opt_mac'] = "52:54:00:00:00:0%d" % (i+1)
            vm_params['opt_settings'] = setting_args
            vm_info.set_vm_device(**vm_params)
            time.sleep(3)
            try:
                vm_dut = vm_info.start(set_target=False)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                self.logger.error("Failure for %s" % str(e))
                raise e
            vm_dut.restore_interfaces()

            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def config_vm_env(self):
        """
        set virtio device IP and run arp protocal
        """
        vm1_intf = self.vm_dut[0].ports_info[0]['intf']
        vm2_intf = self.vm_dut[1].ports_info[0]['intf']
        self.vm_dut[0].send_expect("ifconfig %s %s" % (vm1_intf, self.virtio_ip1), "#", 10)
        self.vm_dut[1].send_expect("ifconfig %s %s" % (vm2_intf, self.virtio_ip2), "#", 10)
        self.vm_dut[0].send_expect("arp -s %s %s" % (self.virtio_ip2, self.virtio_mac2), "#", 10)
        self.vm_dut[1].send_expect("arp -s %s %s" % (self.virtio_ip1, self.virtio_mac1), "#", 10)

    def prepare_test_env(self, zerocopy, path_mode, packed_mode=False):
        """
        start vhost testpmd and qemu, and config the vm env
        """
        self.start_vhost_testpmd(zerocopy)
        self.start_vms(mode=path_mode, packed=packed_mode)
        self.config_vm_env()

    def start_iperf(self, mode):
        """
        run perf command between to vms
        """
        # clear the port xstats before iperf
        self.vhost.send_expect("clear port xstats all", "testpmd> ", 10)

        if mode == "ufo":
            iperf_server = "iperf -s -u -i 1"
            iperf_client = "iperf -c 1.1.1.2 -i 1 -t %s -P 4 -u -b 1G -l 9000" % self.test_duration
        else:
            iperf_server = "iperf -s -i 1"
            iperf_client = "iperf -c 1.1.1.2 -i 1 -t %s" % self.test_duration
        self.vm_dut[0].send_expect("%s > iperf_server.log &" % iperf_server, "", 10)
        self.vm_dut[1].send_expect("%s > iperf_client.log &" % iperf_client, "", 60)
        time.sleep(int(self.test_duration)+3)

    def get_perf_result(self):
        """
        get the iperf test result
        """
        self.vm_dut[0].send_expect('pkill iperf', '# ')
        self.vm_dut[1].session.copy_file_from("%s/iperf_client.log" % self.dut.base_dir)
        fp = open("./iperf_client.log")
        fmsg = fp.read()
        fp.close()
        # remove the server report info from msg
        index = fmsg.find("Server Report")
        if index != -1:
            fmsg = fmsg[:index]
        iperfdata = re.compile('\s(\d+\.\d+)\s([MG]bits/sec)').findall(fmsg)
        # the last data of iperf is the ave data from 0-30 sec
        self.verify(len(iperfdata) != 0, "The iperf data between to vms is 0")
        self.throughput_unit = iperfdata[-1][1]
        self.throughput_data = round(float(iperfdata[-1][0]), 3)
        self.throughput = str(self.throughput_data) + ' ' + self.throughput_unit
        self.logger.info("The iperf data between vms is %s" % self.throughput)

        # rm the iperf log file in vm
        self.vm_dut[0].send_expect('rm iperf_server.log', '#', 10)
        self.vm_dut[1].send_expect('rm iperf_client.log', '#', 10)

    def verify_xstats_info_on_vhost(self):
        """
        check both 2VMs can receive and send big packets to each other
        """
        out_tx = self.vhost.send_expect("show port xstats 0", "testpmd> ", 20)
        out_rx = self.vhost.send_expect("show port xstats 1", "testpmd> ", 20)

        rx_info = re.search("rx_size_1523_to_max_packets:\s*(\d*)", out_rx)
        tx_info = re.search("tx_size_1523_to_max_packets:\s*(\d*)", out_tx)

        self.verify(int(rx_info.group(1)) > 0,
                    "Port 1 not receive packet greater than 1522")
        self.verify(int(tx_info.group(1)) > 0,
                    "Port 0 not forward packet greater than 1522")

    def start_iperf_and_verify_vhost_xstats_info(self, mode):
        """
        start to send packets and verify vm can received data of iperf
        and verify the vhost can received big pkts in testpmd
        """
        self.start_iperf(mode)
        self.get_perf_result()
        self.verify_xstats_info_on_vhost()

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.pmd_vhost.quit()

    def test_vm2vm_split_ring_iperf_with_tso(self):
        """
        VM2VM split ring vhost-user/virtio-net test with tcp traffic
        """
        zerocopy = False
        path_mode = "tso"
        self.test_target = "split_tso"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        self.prepare_test_env(zerocopy, path_mode)
        self.start_iperf_and_verify_vhost_xstats_info(mode="tso")
        self.handle_expected()
        self.handle_results()

    def test_vm2vm_split_ring_dequeue_zero_copy_iperf_with_tso(self):
        """
        VM2VM split ring vhost-user/virtio-net zero copy test with tcp traffic
        """
        zerocopy = True
        path_mode = "tso"
        self.test_target = "split_zero_copy_tso"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        self.prepare_test_env(zerocopy, path_mode)
        self.start_iperf_and_verify_vhost_xstats_info(mode="tso")
        self.handle_expected()
        self.handle_results()

    def test_vm2vm_packed_ring_iperf_with_tso(self):
        """
        VM2VM packed ring vhost-user/virtio-net test with tcp traffic
        """
        zerocopy = False
        path_mode = "tso"
        self.test_target = "packed_tso"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        packed_mode = True
        self.prepare_test_env(zerocopy, path_mode, packed_mode)
        self.start_iperf_and_verify_vhost_xstats_info(mode="tso")
        self.handle_expected()
        self.handle_results()

    def test_vm2vm_packed_ring_dequeue_zero_copy_iperf_with_tso(self):
        """
        VM2VM packed ring vhost-user/virtio-net zero copy test with tcp traffic
        """
        zerocopy = True
        path_mode = "tso"
        packed_mode = True
        self.test_target = "packed_zero_copy_tso"
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        self.prepare_test_env(zerocopy, path_mode, packed_mode)
        self.start_iperf_and_verify_vhost_xstats_info(mode="tso")
        self.handle_expected()
        self.handle_results()

    def tear_down(self):
        """
        run after each test case.
        """
        self.stop_all_apps()
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.

        """
        if self.dut.build_type == 'meson':
            self.restore_env(self.dut)
        if getattr(self, 'vhost', None):
            self.dut.close_session(self.vhost)
