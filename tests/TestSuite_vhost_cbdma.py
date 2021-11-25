# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation.
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
We introduce a new vdev parameter to enable DMA acceleration for Tx
operations of queues:
 - dmas: This parameter is used to specify the assigned DMA device of
   a queue.

Here is an example:
 $ ./testpmd -c f -n 4 \
   --vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas=[txq0@80:04.0]'
"""
import json
import os
import re
import time
from copy import deepcopy

import framework.rst as rst
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE, UPDATE_EXPECTED, load_global_setting
from framework.test_case import TestCase


class TestVirTioVhostCbdma(TestCase):
    def set_up_all(self):
        # Get and verify the ports
        self.dut_ports = self.dut.get_ports()
        self.number_of_ports = 1
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.virtio_user1 = self.dut.new_session(suite="virtio-user1")
        self.pmdout_vhost_user = PmdOutput(self.dut, self.vhost_user)
        self.pmdout_virtio_user = PmdOutput(self.dut, self.virtio_user)
        self.pmdout_virtio_user1 = PmdOutput(self.dut, self.virtio_user1)
        self.frame_sizes = [64, 1518]
        self.virtio_mac = "00:01:02:03:04:05"
        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip']
        self.pci_info = self.dut.ports_info[0]['pci']
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("all", socket=self.socket)
        self.cbdma_dev_infos = []
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        # the path of pcap file
        self.out_path = '/tmp/%s' % self.suite_name
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        self.pktgen_helper = PacketGeneratorHelper()
        self.base_dir = self.dut.base_dir.replace('~', '/root')
        self.testpmd_name = self.dut.apps_name['test-pmd'].split("/")[-1]
        self.save_result_flag = True
        self.json_obj = {}

    def set_up(self):
        """
        Run before each test case.
        """
        self.table_header = ['Frame']
        self.table_header.append("Mode/RXD-TXD")
        self.used_cbdma = []
        self.table_header.append("Mpps")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)
        # test parameters include: frames size, descriptor numbers
        self.test_parameters = self.get_suite_cfg()['test_parameters']
        # traffic duraion in second
        self.test_duration = self.get_suite_cfg()['test_duration']
        # initialize throughput attribution
        # {'TestCase':{ 'Mode': {'$framesize':{"$nb_desc": 'throughput'}}}
        self.throughput = {}
        # Accepted tolerance in Mpps
        self.gap = self.get_suite_cfg()['accepted_tolerance']
        self.test_result = {}
        self.nb_desc = self.test_parameters.get(list(self.test_parameters.keys())[0])[0]
        self.dut.send_expect("killall -I %s" % self.testpmd_name, '#', 20)
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("rm -rf /tmp/s0", "#")
        self.mode_list = []

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num):
        """
        get all cbdma ports
        """
        out = self.dut.send_expect('./usertools/dpdk-devbind.py --status-dev dma', '# ', 30)
        device_info = out.split('\n')
        for device in device_info:
            pci_info = re.search('\s*(0000:\S*:\d*.\d*)', device)
            if pci_info is not None:
                dev_info = pci_info.group(1)
                # the numa id of ioat dev, only add the device which
                # on same socket with nic dev
                bus = int(dev_info[5:7], base=16)
                if bus >= 128:
                    cur_socket = 1
                else:
                    cur_socket = 0
                if self.ports_socket == cur_socket:
                    self.cbdma_dev_infos.append(pci_info.group(1))
        self.verify(len(self.cbdma_dev_infos) >= cbdma_num, 'There no enough cbdma device to run this suite')
        self.used_cbdma = self.cbdma_dev_infos[0:cbdma_num]
        self.device_str = ' '.join(self.used_cbdma)
        self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=%s %s' % (self.drivername, self.device_str), '# ', 60)

    def bind_cbdma_device_to_kernel(self):
        if self.device_str is not None:
            self.dut.send_expect('modprobe ioatdma', '# ')
            self.dut.send_expect('./usertools/dpdk-devbind.py -u %s' % self.device_str, '# ', 30)
            self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=ioatdma  %s' % self.device_str, '# ', 60)

    def check_packets_of_each_queue(self, queue_list):
        """
        check each queue has receive packets
        """
        out = self.vhost_user.send_expect("stop", "testpmd> ", 60)
        for queue_index in queue_list:
            queue = "Queue= %d" % queue_index
            index = out.find(queue)
            rx = re.search("RX-packets:\s*(\d*)", out[index:])
            tx = re.search("TX-packets:\s*(\d*)", out[index:])
            rx_packets = int(rx.group(1))
            tx_packets = int(tx.group(1))
            self.verify(rx_packets > 0 and tx_packets > 0,
                        "The queue %d rx-packets or tx-packets is 0 about " %
                        queue_index + \
                        "rx-packets:%d, tx-packets:%d" %
                        (rx_packets, tx_packets))
        self.vhost_user.send_expect("clear port stats all", "testpmd> ", 30)
        self.vhost_user.send_expect("start", "testpmd> ", 30)

    def check_port_stats_result(self, session):
        out = session.send_expect("show port stats all", "testpmd> ", 30)
        self.result_first = re.findall(r'RX-packets: (\w+)', out)
        self.result_secondary = re.findall(r'TX-packets: (\w+)', out)
        self.verify(int(self.result_first[0]) > 1 and int(self.result_secondary[0]) > 1, "forward packets no correctly")

    @property
    def check_2m_env(self):
        out = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        return True if out == '2048' else False

    def launch_testpmd_as_vhost_user(self, command, cores="Default", dev="", ports = ""):
        self.pmdout_vhost_user.start_testpmd(cores=cores, param=command, vdevs=[dev], ports=ports, prefix="vhost")
        self.vhost_user.send_expect('set fwd mac', 'testpmd> ', 120)
        self.vhost_user.send_expect('start', 'testpmd> ', 120)

    def launch_testpmd_as_virtio_user1(self, command, cores="Default", dev=""):
        eal_params = ""
        if self.check_2m_env:
            eal_params += " --single-file-segments"
        self.pmdout_virtio_user1.start_testpmd(cores, command, vdevs=[dev], no_pci=True, prefix="virtio1", eal_param=eal_params)
        self.virtio_user1.send_expect('set fwd mac', 'testpmd> ', 30)
        self.virtio_user1.send_expect('start', 'testpmd> ', 30)
        self.virtio_user1.send_expect('show port info all', 'testpmd> ', 30)

    def launch_testpmd_as_virtio_user(self, command, cores="Default", dev=""):
        eal_params = ""
        if self.check_2m_env:
            eal_params += " --single-file-segments"
        self.pmdout_virtio_user.start_testpmd(cores, command, vdevs=[dev],no_pci=True, prefix="virtio", eal_param=eal_params)
        self.virtio_user.send_expect('set fwd mac', 'testpmd> ', 120)
        self.virtio_user.send_expect('start', 'testpmd> ', 120)
        self.virtio_user.send_expect('show port info all', 'testpmd> ', 30)

    def diff_param_launch_send_and_verify(self, mode, params, dev, cores, is_quit=True, launch_virtio=True):
        if launch_virtio:
            self.launch_testpmd_as_virtio_user(params, cores, dev=dev)
        self.send_and_verify(mode)
        if is_quit:
            self.virtio_user.send_expect("quit", "# ")
            time.sleep(3)

    def test_perf_pvp_spilt_all_path_with_cbdma_vhost_enqueue_operations(self):
        """
        Test Case 1: PVP Split all path with DMA-accelerated vhost enqueue
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        txd_rxd = 1024
        eal_tx_rxd = ' --nb-cores=%d --txd=%d --rxd=%d'
        queue = 1
        used_cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(used_cbdma_num)
        vhost_vdevs = f"'net_vhost0,iface=/tmp/s0,queues=%d,dmas=[txq0@{self.device_str}]'"
        dev_path_mode_mapper = {
            "inorder_mergeable_path": 'mrg_rxbuf=1,in_order=1',
            "mergeable_path": 'mrg_rxbuf=1,in_order=0',
            "inorder_non_mergeable_path": 'mrg_rxbuf=0,in_order=1',
            "non_mergeable_path": 'mrg_rxbuf=0,in_order=0',
            "vector_rx_path": 'mrg_rxbuf=0,in_order=0',
        }
        pvp_split_all_path_virtio_params = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=%d --txd=%d --rxd=%d" % (queue, txd_rxd, txd_rxd)
        allow_pci = [self.dut.ports_info[0]['pci']]
        for index in range(used_cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[index])
        self.launch_testpmd_as_vhost_user(eal_tx_rxd % (queue, txd_rxd, txd_rxd), self.cores[0:2], dev=vhost_vdevs % (queue), ports=allow_pci)
        for key, path_mode in dev_path_mode_mapper.items():
            if key == "vector_rx_path":
                pvp_split_all_path_virtio_params = eal_tx_rxd % (queue, txd_rxd, txd_rxd)
            vdevs = f"'net_virtio_user0,mac={self.virtio_mac},path=/tmp/s0,{path_mode},queues=%d'" % queue
            self.diff_param_launch_send_and_verify(key, pvp_split_all_path_virtio_params, vdevs, self.cores[2:4], is_quit=False)
            self.mode_list.append(key)
            # step3 restart vhost port, then check throughput again
            key += "_RestartVhost"
            self.vhost_user.send_expect('show port stats all', 'testpmd> ', 10)
            self.vhost_user.send_expect('stop', 'testpmd> ', 10)
            self.vhost_user.send_expect('start', 'testpmd> ', 10)
            self.vhost_user.send_expect('show port info all', 'testpmd> ', 30)
            self.vhost_user.send_expect('show port stats all', 'testpmd> ', 10)
            self.diff_param_launch_send_and_verify(key, pvp_split_all_path_virtio_params, vdevs,
                                                   self.cores[2:4], launch_virtio=False)
            self.mode_list.append(key)
        self.vhost_user.send_expect("quit", "# ")
        self.result_table_print()
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)

    def test_perf_dynamic_queue_number_cbdma_vhost_enqueue_operations(self):
        """
        Test Case2: Split ring dynamic queue number test for DMA-accelerated vhost Tx operations
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        used_cbdma_num = 8
        queue = 8
        txd_rxd = 1024
        nb_cores = 1
        virtio_path = "/tmp/s0"
        path_mode = 'mrg_rxbuf=1,in_order=1'
        self.get_cbdma_ports_info_and_bind_to_dpdk(used_cbdma_num)
        eal_params = " --nb-cores=1 --txd=1024 --rxd=1024 --txq=%d --rxq=%d "
        dynamic_queue_number_cbdma_virtio_params = f"  --tx-offloads=0x0 --enable-hw-vlan-strip {eal_params % (queue,queue)}"
        virtio_dev = f"net_virtio_user0,mac={self.virtio_mac},path={virtio_path},{path_mode},queues={queue},server=1"
        vhost_dev = f"'net_vhost0,iface={virtio_path},queues=%d,client=1,%s'"
        # launch vhost testpmd
        allow_pci = [self.dut.ports_info[0]['pci']]
        for index in range(used_cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[index])

        # no cbdma to launch vhost
        self.launch_testpmd_as_vhost_user(eal_params % (queue,queue), self.cores[0:2], dev=vhost_dev % (queue,''), ports=[allow_pci[0]])
        mode = "no_cbdma"
        self.mode_list.append(mode)
        self.launch_testpmd_as_virtio_user(dynamic_queue_number_cbdma_virtio_params, self.cores[2:4], dev=virtio_dev)
        self.send_and_verify(mode, queue_list=range(queue))
        self.vhost_user.send_expect("quit", "#")

        # used 4 cbdma_num and 4 queue to launch vhost

        vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]};txq2@{self.used_cbdma[2]};txq3@{self.used_cbdma[3]}]"
        self.launch_testpmd_as_vhost_user(eal_params % (queue/2,queue/2), self.cores[0:2], dev=vhost_dev % (int(queue/2),vhost_dmas), ports=allow_pci[:5])
        self.send_and_verify("used_4_cbdma_num", queue_list=range(int(queue/2)))
        self.mode_list.append("used_4_cbdma_num")
        self.vhost_user.send_expect("quit", "#")

        #used 8 cbdma_num to launch vhost
        vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]};txq2@{self.used_cbdma[2]};txq3@{self.used_cbdma[3]};txq4@{self.used_cbdma[4]};txq5@{self.used_cbdma[5]};txq6@{self.used_cbdma[6]};txq7@{self.used_cbdma[7]}]"
        self.launch_testpmd_as_vhost_user(eal_params % (queue, queue), self.cores[0:2],
                                          dev=vhost_dev % (queue,vhost_dmas), ports=allow_pci)
        self.send_and_verify("used_8_cbdma_num", queue_list=range(queue))
        self.mode_list.append("used_8_cbdma_num")
        self.send_and_verify("used_8_cbdma_num_1", queue_list=range(queue))
        self.mode_list.append("used_8_cbdma_num_1")
        self.virtio_user.send_expect("stop", "testpmd> ", 60)
        time.sleep(5)
        self.virtio_user.send_expect("quit", "# ")
        self.vhost_user.send_expect("quit", "# ")
        self.result_table_print()
        # result_rows = [[], [64, 'dynamic_queue2', 7.4959375, 12.593175], [1518, 'dynamic_queue2', 1.91900225, 59.028509209999996]]
        result_rows = self.result_table_getrows()  #
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)

    def test_perf_pvp_packed_all_path_with_cbdma_vhost_enqueue_operations(self):
        """
        Test Case 3: PVP packed ring all path with DMA-accelerated vhost enqueue
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        txd_rxd = 1024
        eal_tx_rxd = ' --nb-cores=%d --txd=%d --rxd=%d'
        queue = 1
        used_cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(used_cbdma_num)
        vhost_vdevs = f"'net_vhost0,iface=/tmp/s0,queues=%d,dmas=[txq0@{self.device_str}]'"
        dev_path_mode_mapper = {
            "inorder_mergeable_path": 'mrg_rxbuf=1,in_order=1,packed_vq=1',
            "mergeable_path": 'mrg_rxbuf=1,in_order=0,packed_vq=1',
            "inorder_non_mergeable_path": 'mrg_rxbuf=0,in_order=1,packed_vq=1',
            "non_mergeable_path": 'mrg_rxbuf=0,in_order=0,packed_vq=1',
            "vector_rx_path": 'mrg_rxbuf=0,in_order=0,packed_vq=1',
        }
        pvp_split_all_path_virtio_params = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=%d --txd=%d --rxd=%d" % (queue, txd_rxd, txd_rxd)
        allow_pci = [self.dut.ports_info[0]['pci']]
        for index in range(used_cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[index])
        self.launch_testpmd_as_vhost_user(eal_tx_rxd % (queue, txd_rxd, txd_rxd), self.cores[0:2], dev=vhost_vdevs % (queue), ports=allow_pci)
        for key, path_mode in dev_path_mode_mapper.items():
            if key == "vector_rx_path":
                pvp_split_all_path_virtio_params = eal_tx_rxd % (queue, txd_rxd, txd_rxd)
            vdevs = f"'net_virtio_user0,mac={self.virtio_mac},path=/tmp/s0,{path_mode},queues=%d'" % queue
            self.diff_param_launch_send_and_verify(key, pvp_split_all_path_virtio_params, vdevs, self.cores[2:4], is_quit=False)
            self.mode_list.append(key)
            # step3 restart vhost port, then check throughput again
            key += "_RestartVhost"
            self.vhost_user.send_expect('show port stats all', 'testpmd> ', 10)
            self.vhost_user.send_expect('stop', 'testpmd> ', 10)
            self.vhost_user.send_expect('start', 'testpmd> ', 10)
            self.vhost_user.send_expect('show port info all', 'testpmd> ', 30)
            self.vhost_user.send_expect('show port stats all', 'testpmd> ', 10)
            self.diff_param_launch_send_and_verify(key, pvp_split_all_path_virtio_params, vdevs,
                                                   self.cores[2:4], launch_virtio=False)
            self.mode_list.append(key)
        self.vhost_user.send_expect("quit", "# ")
        self.result_table_print()
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)

    def test_perf_packed_dynamic_queue_number_cbdma_vhost_enqueue_operations(self):
        """
        Test Case4: Packed ring dynamic queue number test for DMA-accelerated vhost Tx operations
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()['expected_throughput'][self.test_target]
        used_cbdma_num = 8
        queue = 8
        txd_rxd = 1024
        nb_cores = 1
        virtio_path = "/tmp/s0"
        path_mode = 'mrg_rxbuf=1,in_order=1,packed_vq=1'
        self.get_cbdma_ports_info_and_bind_to_dpdk(used_cbdma_num)
        vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]}]"
        eal_params = " --nb-cores=1 --txd=1024 --rxd=1024 --txq=%d --rxq=%d "
        dynamic_queue_number_cbdma_virtio_params = f"  --tx-offloads=0x0 --enable-hw-vlan-strip {eal_params % (queue, queue)}"
        virtio_dev = f"net_virtio_user0,mac={self.virtio_mac},path={virtio_path},{path_mode},queues={queue},server=1"
        vhost_dev = f"'net_vhost0,iface={virtio_path},queues=%s,client=1,%s'"
        # launch vhost testpmd
        allow_pci = [self.dut.ports_info[0]['pci']]
        for index in range(used_cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[index])

        # no cbdma to launch vhost
        self.launch_testpmd_as_vhost_user(eal_params % (queue,queue), self.cores[0:2], dev=vhost_dev % (queue,''), ports= [allow_pci[0]])
        mode = "no_cbdma"
        self.mode_list.append(mode)
        self.launch_testpmd_as_virtio_user(dynamic_queue_number_cbdma_virtio_params, self.cores[2:4], dev=virtio_dev)
        self.send_and_verify(mode, queue_list=range(queue))
        self.vhost_user.send_expect("quit", "#")

        # used 4 cbdma_num and 4 queue to launch vhost
        vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]};txq2@{self.used_cbdma[2]};txq3@{self.used_cbdma[3]}]"
        self.launch_testpmd_as_vhost_user(eal_params % (queue/2,queue/2), self.cores[0:2],
                dev=vhost_dev % (int(queue/2),vhost_dmas), ports=allow_pci[:5])
        self.send_and_verify("used_4_cbdma_num", queue_list=range(int(queue/2)))
        self.mode_list.append("used_4_cbdma_num")
        self.vhost_user.send_expect("quit", "#")

        #used 8 cbdma_num to launch vhost
        vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]};txq2@{self.used_cbdma[2]};txq3@{self.used_cbdma[3]};txq4@{self.used_cbdma[4]};txq5@{self.used_cbdma[5]};txq6@{self.used_cbdma[6]};txq7@{self.used_cbdma[7]}]"
        self.launch_testpmd_as_vhost_user(eal_params % (queue, queue), self.cores[0:2],
                                          dev=vhost_dev % (queue,vhost_dmas), ports=allow_pci)
        self.send_and_verify("used_8_cbdma_num", queue_list=range(queue))
        self.mode_list.append("used_8_cbdma_num")
        self.send_and_verify("used_8_cbdma_num_1", queue_list=range(queue))
        self.mode_list.append("used_8_cbdma_num_1")
        self.virtio_user.send_expect("stop", "testpmd> ", 60)
        time.sleep(5)
        self.virtio_user.send_expect("quit", "# ")
        self.vhost_user.send_expect("quit", "# ")
        self.result_table_print()
        # result_rows = [[], [64, 'dynamic_queue2', 7.4959375, 12.593175], [1518, 'dynamic_queue2', 1.91900225, 59.028509209999996]]
        result_rows = self.result_table_getrows()  #
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)


    
    def test_perf_compare_pvp_split_ring_performance(self):
        """
        Test Case5: Compare PVP split ring performance between CPU copy, CBDMA copy and Sync copy
        """
        used_cbdma_num = 1
        queue = 1
        txd_rxd = 1024
        eal_tx_rxd = ' --nb-cores=%d --txd=%d --rxd=%d'
        path_mode = 'mrg_rxbuf=1,in_order=1,server=1'
        allow_pci = [self.dut.ports_info[0]['pci']]
        self.get_cbdma_ports_info_and_bind_to_dpdk(used_cbdma_num)
        for index in range(used_cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[index])
        path_mode = 'mrg_rxbuf=1,in_order=1'
        vhost_vdevs = f"'net_vhost0,iface=/tmp/s0,queues=%d,client=1,dmas=[txq0@{self.device_str}]'"
        compare_pvp_split_ring_performance = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=%d --txd=%d --rxd=%d" % (queue, txd_rxd, txd_rxd)
        dev_path_mode_mapper = {
            "sync_cbdma": '',
            "cpu": '',
        }
        for key in dev_path_mode_mapper.items():
            if key == "cpu":
                vhost_vdevs = f"'net_vhost0,iface=/tmp/s0,queues=1'"
                self.launch_testpmd_as_vhost_user(eal_tx_rxd % (queue, txd_rxd, txd_rxd), self.cores[0:2], dev=vhost_vdevs, ports=[allow_pci[0]])
                vdevs = f"'net_virtio_user0,mac={self.virtio_mac},path=/tmp/s0,{path_mode},queues=%d'" % queue
                self.launch_testpmd_as_virtio_user(compare_pvp_split_ring_performance, self.cores[2:4], dev=vdevs)
                mode = "cpu_copy_64"
                self.mode_list.append(mode)
                self.send_and_verify(mode, frame_sizes=[64], pkt_length_mode='fixed')
                perf_cpu_copy_64 = self.throughput[mode][64][self.nb_desc]
                self.virtio_user.send_expect('show port stats all', 'testpmd> ', 10)
                self.virtio_user.send_expect("quit", "# ")
                self.vhost_user.send_expect("quit", "# ")
            else:
                self.launch_testpmd_as_vhost_user(eal_tx_rxd % (queue, txd_rxd, txd_rxd), self.cores[0:2],dev=vhost_vdevs % (queue), ports=allow_pci)
                vdevs = f"'net_virtio_user0,mac={self.virtio_mac},path=/tmp/s0,{path_mode},queues=%d,server=1'" % queue
                self.launch_testpmd_as_virtio_user(compare_pvp_split_ring_performance, self.cores[2:4],dev=vdevs)
                mode = "sync_copy_64"
                self.mode_list.append(mode)
                self.send_and_verify(mode,frame_sizes=[64],pkt_length_mode='fixed')
                perf_sync_copy_64 = self.throughput[mode][64][self.nb_desc]
                mode = "cbdma_copy_1518"
                self.mode_list.append(mode)
                self.send_and_verify(mode,frame_sizes=[1518],pkt_length_mode='fixed')
                perf_cbdma_copy_1518 = self.throughput[mode][1518][self.nb_desc]
                self.virtio_user.send_expect('show port stats all', 'testpmd> ', 10)
                self.vhost_user.send_expect("quit", "# ")
                time.sleep(3)
                self.launch_testpmd_as_vhost_user(eal_tx_rxd % (queue, txd_rxd, txd_rxd), self.cores[0:2],dev=vhost_vdevs % (queue), ports=allow_pci)
                mode = "sync_copy_1518"
                self.mode_list.append(mode)
                self.send_and_verify(mode,frame_sizes=[1518],pkt_length_mode='fixed')
                perf_sync_copy_1518 = self.throughput[mode][1518][self.nb_desc]
                self.check_port_stats_result(self.virtio_user)
                self.virtio_user.send_expect("quit", "# ")
                self.vhost_user.send_expect("quit", "# ")
        self.result_table_print()
        self.verify(abs(perf_sync_copy_64 - perf_cpu_copy_64)/perf_sync_copy_64 < 0.1, "sync_copy_64 vs. cpu_copy_64 delta > 10%"  )
        self.verify(abs(perf_cbdma_copy_1518 - perf_sync_copy_1518)/perf_sync_copy_1518 > 0.05,"cbdma_copy_1518 vs sync_copy_1518 delta < 5%")

    @staticmethod
    def vhost_or_virtio_set_one_queue(session):
        session.send_expect('stop', 'testpmd> ', 120)
        session.send_expect('port stop all', 'testpmd> ', 120)
        session.send_expect('port config all rxq 1', 'testpmd> ', 120)
        session.send_expect('port config all txq 1', 'testpmd> ', 120)
        session.send_expect('port start all', 'testpmd> ', 120)
        session.send_expect('start', 'testpmd> ', 120)
        session.send_expect('show port info all', 'testpmd> ', 30)
        session.send_expect('show port stats all', 'testpmd> ', 120)
        time.sleep(5)

    @property
    def check_value(self):
        check_dict = dict.fromkeys(self.frame_sizes)
        linerate = {64: 0.085, 128: 0.12, 256: 0.20, 512: 0.35, 1024: 0.50, 1280: 0.55, 1518: 0.60}
        for size in self.frame_sizes:
            speed = self.wirespeed(self.nic, size, self.number_of_ports)
            check_dict[size] = round(speed * linerate[size], 2)
        return check_dict

    def send_imix_and_verify(self, mode, multiple_queue=True, queue_list=[]):
        """
        Send imix packet with packet generator and verify
        """
        frame_sizes = [
            64, 128, 256, 512, 1024, 1280, 1518, ]
        tgenInput = []
        for frame_size in frame_sizes:
            payload_size = frame_size - self.headers_size
            port = self.tester.get_local_port(self.dut_ports[0])
            fields_config = {'ip': {'src': {'action': 'random'}, }, }
            if not multiple_queue:
                fields_config = None
            pkt = Packet()
            pkt.assign_layers(['ether', 'ipv4', 'raw'])
            pkt.config_layers([('ether', {'dst': '%s' % self.virtio_mac}), ('ipv4', {'src': '1.1.1.1'}),
                               ('raw', {'payload': ['01'] * int('%d' % payload_size)})])
            pkt.save_pcapfile(self.tester, "%s/multiqueuerandomip_%s.pcap" % (self.out_path, frame_size))
            tgenInput.append((port, port, "%s/multiqueuerandomip_%s.pcap" % (self.out_path, frame_size)))

        self.tester.pktgen.clear_streams()
        streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, fields_config, self.tester.pktgen)
        trans_options = {'delay': 5, 'duration': self.test_duration}
        bps, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=trans_options)
        Mpps = pps / 1000000.0
        Mbps = bps / 1000000.0
        self.verify(Mbps > 0,
                    f"{self.running_case} can not receive packets of frame size {frame_sizes}")
        bps_linerate = self.wirespeed(self.nic, 64, 1) * 8 * (64 + 20)
        throughput = Mbps * 100 / float(bps_linerate)
        self.throughput[mode] = {
            'imix': {
                self.nb_desc: [Mbps, Mpps],
                }
        }
        results_row = ['imix']
        results_row.append(mode)
        results_row.append(Mpps)
        results_row.append(throughput)
        self.result_table_add(results_row)
        if queue_list:
            # check RX/TX can work normally in each queues
            self.check_packets_of_each_queue(queue_list=queue_list)

    def send_and_verify(self, mode, multiple_queue=True, queue_list=[], frame_sizes=None, pkt_length_mode='imix'):
        """
        Send packet with packet generator and verify
        """
        if pkt_length_mode == 'imix':
            self.send_imix_and_verify(mode, multiple_queue, queue_list)
            return

        self.throughput[mode] = dict()
        for frame_size in frame_sizes:
            self.throughput[mode][frame_size] = dict()
            payload_size = frame_size - self.headers_size
            tgenInput = []
            port = self.tester.get_local_port(self.dut_ports[0])
            fields_config = {'ip': {'src': {'action': 'random'},},}
            if not multiple_queue:
                fields_config = None
            pkt1 = Packet()
            pkt1.assign_layers(['ether', 'ipv4', 'raw'])
            pkt1.config_layers([('ether', {'dst': '%s' % self.virtio_mac}), ('ipv4', {'src': '1.1.1.1'}),
                                ('raw', {'payload': ['01'] * int('%d' % payload_size)})])
            pkt1.save_pcapfile(self.tester, "%s/multiqueuerandomip_%s.pcap" % (self.out_path, frame_size))
            tgenInput.append((port, port, "%s/multiqueuerandomip_%s.pcap" % (self.out_path, frame_size)))
            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, fields_config, self.tester.pktgen)
            trans_options = {'delay': 5, 'duration': 20}
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=trans_options)
            Mpps = pps / 1000000.0
            self.verify(Mpps > 0, "%s can not receive packets of frame size %d" % (self.running_case, frame_size))
            throughput = Mpps * 100 / float(self.wirespeed(self.nic, frame_size, 1))
            self.throughput[mode][frame_size][self.nb_desc] = Mpps
            results_row = [frame_size]
            results_row.append(mode)
            results_row.append(Mpps)
            results_row.append(throughput)
            self.result_table_add(results_row)
        if queue_list:
            # check RX/TX can work normally in each queues
            self.check_packets_of_each_queue(queue_list=queue_list)

    def handle_expected(self, mode_list):
        """
        Update expected numbers to configurate file: conf/$suite_name.cfg
        """
        if load_global_setting(UPDATE_EXPECTED) == "yes":
            for mode in mode_list:
                for frame_size in self.test_parameters.keys():
                    for nb_desc in self.test_parameters[frame_size]:
                        if frame_size == 'imix':
                            self.expected_throughput[mode][frame_size][nb_desc] = round(
                                self.throughput[mode][frame_size][nb_desc][1], 3)
                        else:
                            self.expected_throughput[mode][frame_size][nb_desc] = round(
                                self.throughput[mode][frame_size][nb_desc], 3)

    def handle_results(self, mode_list):
        """
        results handled process:
        1, save to self.test_results
            table_header = ['Frame', 'Mode/RXD-TXD', 'Mpps', '% linerate', 'nb_desc', 'Expected Throughput', 'Throughput Difference']
            ret_datas = {1024: {'Frame': 64, 'Mode/RXD-TXD': 'dynamic_queue2', 'Mpps': '7.537 Mpps', '% linerate': '12.662%',
                        'nb_desc': 1024, 'Expected Throughput': '7.537 Mpps', 'Throughput Difference': '-0.000 Mpps'}}
            self.test_result = {'dynamic_queue2': {64: {1024: {'Frame': 64, 'Mode/RXD-TXD': 'dynamic_queue2', 'Mpps': '7.537 Mpps',
                '% linerate': '12.662%', 'nb_desc': 1024, 'Expected Throughput': '7.537 Mpps', 'Throughput Difference': '-0.000 Mpps'}}}}
        2, create test results table
        3, save to json file for Open Lab
        """
        header = self.table_header
        header.append("nb_desc")
        header.append("Expected Throughput")
        header.append("Throughput Difference")
        for mode in mode_list:
            self.test_result[mode] = dict()
            for frame_size in self.test_parameters.keys():
                ret_datas = {}
                if frame_size == 'imix':
                    bps_linerate = self.wirespeed(self.nic, 64, 1) * 8 * (64 + 20)
                    ret_datas = {}
                    for nb_desc in self.test_parameters[frame_size]:
                        ret_data = {}
                        ret_data[header[0]] = frame_size
                        ret_data[header[1]] = mode
                        ret_data[header[2]] = "{:.3f} Mpps".format(
                            self.throughput[mode][frame_size][nb_desc][1])
                        ret_data[header[3]] = "{:.3f}%".format(
                            self.throughput[mode][frame_size][nb_desc][0] * 100 / bps_linerate)
                        ret_data[header[4]] = nb_desc
                        ret_data[header[5]] = "{:.3f} Mpps".format(
                            self.expected_throughput[mode][frame_size][nb_desc])
                        ret_data[header[6]] = "{:.3f} Mpps".format(
                            self.throughput[mode][frame_size][nb_desc][1] -
                            self.expected_throughput[mode][frame_size][nb_desc])
                        ret_datas[nb_desc] = deepcopy(ret_data)
                else:
                    wirespeed = self.wirespeed(self.nic, frame_size, self.number_of_ports)
                    for nb_desc in self.test_parameters[frame_size]:
                        ret_data = {}
                        ret_data[header[0]] = frame_size
                        ret_data[header[1]] = mode
                        ret_data[header[2]] = "{:.3f} Mpps".format(
                            self.throughput[mode][frame_size][nb_desc])
                        ret_data[header[3]] = "{:.3f}%".format(
                            self.throughput[mode][frame_size][nb_desc] * 100 / wirespeed)
                        ret_data[header[4]] = nb_desc
                        ret_data[header[5]] = "{:.3f} Mpps".format(
                            self.expected_throughput[mode][frame_size][nb_desc])
                        ret_data[header[6]] = "{:.3f} Mpps".format(
                            self.throughput[mode][frame_size][nb_desc] -
                            self.expected_throughput[mode][frame_size][nb_desc])
                        ret_datas[nb_desc] = deepcopy(ret_data)
                self.test_result[mode][frame_size] = deepcopy(ret_datas)
        # Create test results table
        self.result_table_create(header)
        for mode in mode_list:
            for frame_size in self.test_parameters.keys():
                for nb_desc in self.test_parameters[frame_size]:
                    table_row = list()
                    for i in range(len(header)):
                        table_row.append(
                            self.test_result[mode][frame_size][nb_desc][header[i]])
                    self.result_table_add(table_row)
        # present test results to screen
        self.result_table_print()
        # save test results as a file
        if self.save_result_flag:
            self.save_result(self.test_result, mode_list)

    def save_result(self, data, mode_list):
        """
        Saves the test results as a separated file named with
        self.nic+_perf_virtio_user_pvp.json in output folder
        if self.save_result_flag is True
        """
        case_name = self.running_case
        self.json_obj[case_name] = list()
        status_result = []
        for mode in mode_list:
            for frame_size in self.test_parameters.keys():
                for nb_desc in self.test_parameters[frame_size]:
                    row_in = self.test_result[mode][frame_size][nb_desc]
                    row_dict0 = dict()
                    row_dict0['performance'] = list()
                    row_dict0['parameters'] = list()
                    row_dict0['parameters'] = list()
                    result_throughput = float(row_in['Mpps'].split()[0])
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
                    row_dict1 = dict(name="Throughput", value=result_throughput, unit="Mpps", delta=delta)
                    row_dict2 = dict(name="Txd/Rxd", value=row_in["Mode/RXD-TXD"], unit="descriptor")
                    row_dict3 = dict(name="frame_size", value=row_in["Frame"], unit="bytes")
                    row_dict0['performance'].append(row_dict1)
                    row_dict0['parameters'].append(row_dict2)
                    row_dict0['parameters'].append(row_dict3)
                    self.json_obj[case_name].append(row_dict0)
                    status_result.append(row_dict0['status'])
        with open(os.path.join(rst.path2Result, '{0:s}_{1}.json'.format(self.nic, self.suite_name)), 'w') as fp:
            json.dump(self.json_obj, fp)
        self.verify("FAIL" not in status_result, "Exceeded Gap")

    def tear_down(self):
        """
        Run after each test case.
        Clear qemu and testpmd to avoid blocking the following TCs
        """
        self.dut.send_expect("killall -I %s" % self.testpmd_name, '#', 20)
        self.bind_cbdma_device_to_kernel()
        if self.running_case == 'test_check_threshold_value_with_cbdma':
            self.bind_nic_driver(self.dut_ports, self.drivername)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)
        self.dut.close_session(self.virtio_user1)
        self.dut.kill_all()
