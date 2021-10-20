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
Test vhost/virtio-user loopback multi-queues on 7 tx/rx path.
Includes Mergeable, Normal, Vector_RX, Inorder mergeable,
Inorder no-mergeable, Virtio 1.1 mergeable, Virtio 1.1 no-mergeable Path.
"""

import re
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestLoopbackMultiQueues(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.frame_sizes = [64, 1518]
        self.verify_queue = [1, 8]
        self.dut_ports = self.dut.get_ports()
        port_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(config='all', socket=port_socket)
        self.cores_num = len(self.core_list)
        self.logger.info("you can config packet_size in file %s.cfg," % self.suite_name + \
                        "in region 'suite' like packet_sizes=[64, 128, 256]")
        # get the frame_sizes from cfg file
        if 'packet_sizes' in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()['packet_sizes']
        self.path=self.dut.apps_name['test-pmd']
        self.testpmd_name = self.path.split("/")[-1]

    def set_up(self):
        """
        Run before each test case.
        """
        # Prepare the result table
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.table_header = ["Frame", "Mode", "Throughput(Mpps)", "Queue Number"]
        self.result_table_create(self.table_header)
        self.data_verify = {}

        self.vhost = self.dut.new_session(suite="vhost")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.vhost_pmd = PmdOutput(self.dut, self.vhost)
        self.virtio_user_pmd = PmdOutput(self.dut, self.virtio_user)

    def get_core_mask(self):
        """
        get the coremask about vhost and virito depend on the queue number
        """
        self.verify(self.cores_num > (2*self.nb_cores + 2),
                        "There has not enought cores to test this case %s" %
                        self.running_case)
        self.core_list_user = self.core_list[1:self.nb_cores + 2]
        self.core_list_host = self.core_list[self.nb_cores + 2:2 * self.nb_cores + 3]

    def start_vhost_testpmd(self):
        """
        start testpmd on vhost
        """
        eal_params = "--vdev 'net_vhost0,iface=vhost-net,queues={}'".format(self.queue_number)
        param = "--nb-cores={} --rxq={} --txq={} --txd=1024 --rxd=1024".format(self.nb_cores, self.queue_number, self.queue_number)
        self.vhost_pmd.start_testpmd(self.core_list_host, param=param, no_pci=True, ports=[], eal_param=eal_params, prefix='vhost', fixed_prefix=True)
        self.vhost_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)

    @property
    def check_2M_env(self):
        out = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        return True if out == '2048' else False

    def start_virtio_testpmd(self, args):
        """
        start testpmd on virtio
        """
        eal_param = "--vdev 'net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues={},{}'".format(self.queue_number, args["version"])
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        if 'vectorized_path' in self.running_case:
            eal_param += " --force-max-simd-bitwidth=512"
        param = "{} --nb-cores={} --rxq={} --txq={} --txd=1024 --rxd=1024".format(args["path"], self.nb_cores, self.queue_number, self.queue_number)
        self.virtio_user_pmd.start_testpmd(cores=self.core_list_user, param=param, eal_param=eal_param, \
                no_pci=True, ports=[], prefix="virtio", fixed_prefix=True)

        self.virtio_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)
        self.virtio_user_pmd.execute_cmd("start", "testpmd> ", 120)

    def calculate_avg_throughput(self):
        """
        calculate the average throughput
        """
        results = 0.0
        self.vhost_pmd.execute_cmd("show port stats all", "testpmd>", 60)
        for i in range(10):
            out = self.vhost_pmd.execute_cmd("show port stats all", "testpmd>", 60)
            time.sleep(1)
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 10)
        self.verify(Mpps > 5, "port can not receive packets")
        return Mpps

    def update_result_table(self, frame_size, case_info, Mpps):
        results_row = [frame_size]
        results_row.append(case_info)
        results_row.append(Mpps)
        results_row.append(self.queue_number)
        self.result_table_add(results_row)

        # recording the value of 64 packet_size
        if frame_size == 64:
            self.data_verify['queue%d-64' % self.queue_number] =  Mpps

    def check_packets_of_each_queue(self, frame_size):
        """
        check each queue has receive packets
        """
        out = self.vhost_pmd.execute_cmd("stop", "testpmd> ", 60)
        for queue_index in range(0, self.queue_number):
            queue = "Queue= %d" % queue_index
            index = out.find(queue)
            rx = re.search("RX-packets:\s*(\d*)", out[index:])
            tx = re.search("TX-packets:\s*(\d*)", out[index:])
            rx_packets = int(rx.group(1))
            tx_packets = int(tx.group(1))
            self.verify(rx_packets > 0 and tx_packets > 0,
                   "The queue %d rx-packets or tx-packets is 0 about " %
                   queue_index + \
                   "frame_size:%d, rx-packets:%d, tx-packets:%d" %
                   (frame_size, rx_packets, tx_packets))

        self.vhost_pmd.execute_cmd("clear port stats all", "testpmd> ", 60)

    def send_and_verify(self, case_info):
        """
        start to send packets and calculate avg throughput
        """
        for frame_size in self.frame_sizes:
            self.vhost_pmd.execute_cmd("set txpkts %d" % frame_size, "testpmd> ", 30)
            self.vhost_pmd.execute_cmd("start tx_first 32", "testpmd> ", 30)
            Mpps = self.calculate_avg_throughput()
            self.update_result_table(frame_size, case_info, Mpps)
            if self.queue_number > 1:
                self.check_packets_of_each_queue(frame_size)


    def verify_liner_for_multi_queue(self):
        """
        verify the Mpps of 8 queues is eight times of 1 queue
        and allow 0.1 drop for 8 queues
        """
        if self.data_verify:
            drop = self.data_verify['queue1-64']*8*(0.1)
            self.verify(self.data_verify['queue8-64'] >= self.data_verify['queue1-64']*8 - drop,
                        'The data of multiqueue is not linear for %s' % self.running_case)

    def close_all_testpmd(self):
        """
        close all testpmd of vhost and virtio
        """
        self.vhost_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user_pmd.execute_cmd("quit", "#", 60)

    def close_all_session(self):
        """
        close all session of vhost and vhost-user
        """
        self.dut.close_session(self.virtio_user)
        self.dut.close_session(self.vhost)

    def test_loopback_multi_queue_virtio11_mergeable(self):
        """
        performance for Vhost PVP virtio 1.1 Mergeable Path.
        """
        virtio_pmd_arg = {"version": "in_order=0,packed_vq=1,mrg_rxbuf=1",
                            "path": ""}
        for i in self.verify_queue:
            self.nb_cores = i
            self.queue_number = i
            self.get_core_mask()
            self.start_vhost_testpmd()
            self.start_virtio_testpmd(virtio_pmd_arg)
            self.send_and_verify("virtio_1.1 mergeable on")
            self.close_all_testpmd()

        self.result_table_print()
        self.verify_liner_for_multi_queue()

    def test_loopback_multi_queue_virtio11_normal(self):
        """
        performance for Vhost PVP virtio1.1 Normal Path.
        """
        virtio_pmd_arg = {"version": "in_order=0,packed_vq=1,mrg_rxbuf=0",
                            "path": ""}
        for i in self.verify_queue:
            self.nb_cores = i
            self.queue_number = i
            self.get_core_mask()
            self.start_vhost_testpmd()
            self.start_virtio_testpmd(virtio_pmd_arg)
            self.send_and_verify("virtio_1.1 normal")
            self.close_all_testpmd()

        self.result_table_print()
        self.verify_liner_for_multi_queue()

    def test_loopback_multi_queue_inorder_mergeable(self):
        """
        performance for Vhost PVP In_order mergeable Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=1,mrg_rxbuf=1",
                            "path": ""}
        for i in self.verify_queue:
            self.nb_cores = i
            self.queue_number = i
            self.get_core_mask()
            self.start_vhost_testpmd()
            self.start_virtio_testpmd(virtio_pmd_arg)
            self.send_and_verify("inoder mergeable on")
            self.close_all_testpmd()

        self.result_table_print()
        self.verify_liner_for_multi_queue()

    def test_loopback_multi_queue_inorder_no_mergeable(self):
        """
        performance for Vhost PVP In_order no_mergeable Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=1,mrg_rxbuf=0",
                        "path": ""}
        for i in self.verify_queue:
            self.nb_cores = i
            self.queue_number = i
            self.get_core_mask()
            self.start_vhost_testpmd()
            self.start_virtio_testpmd(virtio_pmd_arg)
            self.send_and_verify("inoder mergeable off")
            self.close_all_testpmd()

        self.result_table_print()
        self.verify_liner_for_multi_queue()

    def test_loopback_mulit_queue_mergeable(self):
        """
        performance for Vhost PVP Mergeable Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=1",
                            "path": ""}
        for i in self.verify_queue:
            self.nb_cores = i
            self.queue_number = i
            self.get_core_mask()
            self.start_vhost_testpmd()
            if self.queue_number == 8:
                virtio_pmd_arg["path"] = "--enable-hw-vlan-strip"
            self.start_virtio_testpmd(virtio_pmd_arg)
            self.send_and_verify("virito mergeable")
            self.close_all_testpmd()

        self.result_table_print()
        self.verify_liner_for_multi_queue()

    def test_loopback_multi_queue_normal(self):
        """
        performance for Vhost PVP Normal Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=0,vectorized=1",
                            "path": "--enable-hw-vlan-strip"}
        for i in self.verify_queue:
            self.nb_cores = i
            self.queue_number = i
            self.get_core_mask()
            self.start_vhost_testpmd()
            self.start_virtio_testpmd(virtio_pmd_arg)
            self.send_and_verify("virtio normal")
            self.close_all_testpmd()

        self.result_table_print()
        self.verify_liner_for_multi_queue()

    def test_loopback_multi_queue_vector_rx(self):
        """
        performance for Vhost PVP Vector_RX Path
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=0,vectorized=1",
                            "path": ""}
        for i in self.verify_queue:
            self.nb_cores = i
            self.queue_number = i
            self.get_core_mask()
            self.start_vhost_testpmd()
            self.start_virtio_testpmd(virtio_pmd_arg)
            self.send_and_verify("virito vector rx")
            self.close_all_testpmd()

        self.result_table_print()
        self.verify_liner_for_multi_queue()

    def test_loopback_with_virtio11_inorder_mergeable_path_multi_queue(self):
        """
        performance for Vhost PVP Vector_RX Path
        """
        virtio_pmd_arg = {"version": "packed_vq=1,mrg_rxbuf=1,in_order=1",
                            "path": ""}
        for i in self.verify_queue:
            self.nb_cores = i
            self.queue_number = i
            self.get_core_mask()
            self.start_vhost_testpmd()
            self.start_virtio_testpmd(virtio_pmd_arg)
            self.send_and_verify("virtio 1.1 inorder mergeable")
            self.close_all_testpmd()

        self.result_table_print()
        self.verify_liner_for_multi_queue()

    def test_loopback_with_virtio11_inorder_nonmergeable_path_multi_queue(self):
        """
        performance for Vhost PVP Vector_RX Path
        """
        virtio_pmd_arg = {"version": "packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1",
                            "path": "--rx-offloads=0x10 --enable-hw-vlan-strip "}
        for i in self.verify_queue:
            self.nb_cores = i
            self.queue_number = i
            self.get_core_mask()
            self.start_vhost_testpmd()
            self.start_virtio_testpmd(virtio_pmd_arg)
            self.send_and_verify("virtio 1.1 inorder non-mergeable")
            self.close_all_testpmd()

        self.result_table_print()
        self.verify_liner_for_multi_queue()

    def test_loopback_with_virtio11_vectorized_path_multi_queue(self):
        """
        performance for Vhost PVP Vector_RX Path
        """
        virtio_pmd_arg = {"version": "packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1",
                            "path": "--enable-hw-vlan-strip "}
        for i in self.verify_queue:
            self.nb_cores = i
            self.queue_number = i
            self.get_core_mask()
            self.start_vhost_testpmd()
            self.start_virtio_testpmd(virtio_pmd_arg)
            self.send_and_verify("virtio 1.1 inorder non-mergeable")
            self.close_all_testpmd()
        self.result_table_print()
        self.verify_liner_for_multi_queue()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.close_all_session()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
