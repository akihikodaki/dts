#
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
Benchmark Vhost loopback for 7 RX/TX PATHs.
Includes Mergeable, Normal, Vector_RX,Inorder_mergeable,
Inorder_no_mergeable, VIRTIO1.1_mergeable, VIRTIO1.1_normal Path.
"""
import utils
import time
import re
from test_case import TestCase


class TestLoopbackPortRestart(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.frame_sizes = [64, 1518]
        self.core_config = "1S/5C/1T"
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket)
        self.core_list_user = self.core_list[0:2]
        self.core_list_host = self.core_list[2:5]
        self.path=self.dut.apps_name['test-pmd']
        self.testpmd_name = self.path.split("/")[-1]

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.dut.send_expect("rm -rf ./vhost.out", "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        # Prepare the result table
        self.table_header = ["FrameSize(B)", "Mode", "Throughput(Mpps)", "Cycle"]
        self.result_table_create(self.table_header)

        self.vhost = self.dut.new_session(suite="vhost")
        self.virtio_user = self.dut.new_session(suite="virtio-user")

    def start_vhost_testpmd(self):
        """
        start testpmd on vhost
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        eal_param = self.dut.create_eal_parameters(cores=self.core_list_host, prefix='vhost', no_pci=True, vdevs=['net_vhost0,iface=vhost-net,queues=1,client=0'])
        command_line_client = self.path + eal_param + " -- -i --nb-cores=1 --txd=1024 --rxd=1024"
        self.vhost.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost.send_expect("set fwd mac", "testpmd> ", 120)

    @property
    def check_2M_env(self):
        out = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        return True if out == '2048' else False

    def start_virtio_user_testpmd(self, pmd_arg):
        """
        start testpmd of vhost user
        """
        eal_param = self.dut.create_eal_parameters(cores=self.core_list_user, prefix='virtio', no_pci=True, vdevs=['net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,%s' % pmd_arg["version"]])
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        command_line_user = self.path + eal_param + " -- -i %s --rss-ip --nb-cores=1 --txd=1024 --rxd=1024" % pmd_arg["path"]
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd mac", "testpmd> ", 120)
        self.virtio_user.send_expect("start", "testpmd> ", 120)

    def check_port_throughput_after_port_stop(self):
        """
        check the throughput after port stop
        """
        loop = 1
        while(loop <= 5):
            out = self.vhost.send_expect("show port stats 0", "testpmd>", 60)
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            if result == "0":
                break
            time.sleep(3)
            loop = loop + 1
        self.verify(result == "0", "port stop failed, it alse can recevie data after stop.")

    def check_port_link_status_after_port_restart(self):
        """
        check the link status after port restart
        """
        loop = 1
        while(loop <= 5):
            out = self.vhost.send_expect("show port info all", "testpmd> ", 120)
            port_status = re.findall("Link\s*status:\s*([a-z]*)", out)
            if("down" not in port_status):
                break
            time.sleep(3)
            loop = loop + 1
        self.verify("down" not in port_status, "port can not up after restart")

    def port_restart(self, restart_times=1):
        if restart_times == 1:
            self.vhost.send_expect("stop", "testpmd> ", 120)
            self.vhost.send_expect("port stop 0", "testpmd> ", 120)
            self.check_port_throughput_after_port_stop()
            self.vhost.send_expect("clear port stats all", "testpmd> ", 120)
            self.vhost.send_expect("port start all", "testpmd> ", 120)
        else:
            for i in range(restart_times):
                self.vhost.send_expect("stop", "testpmd> ", 120)
                self.vhost.send_expect("port stop 0", "testpmd> ", 120)
                self.vhost.send_expect("clear port stats all", "testpmd> ", 120)
                self.vhost.send_expect("port start all", "testpmd> ", 120)
        self.check_port_link_status_after_port_restart()
        self.vhost.send_expect("set burst 1", "testpmd> ", 120)
        self.vhost.send_expect("start tx_first 1", "testpmd> ", 120)

    def update_table_info(self, case_info, frame_size, Mpps, Cycle):
        results_row = [frame_size]
        results_row.append(case_info)
        results_row.append(Mpps)
        results_row.append(Cycle)
        self.result_table_add(results_row)

    def calculate_avg_throughput(self):
        """
        calculate the average throughput
        """
        results = 0.0
        self.vhost.send_expect("show port stats all", "testpmd>", 60)
        for i in range(10):
            out = self.vhost.send_expect("show port stats all", "testpmd>", 60)
            time.sleep(1)
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 10)
        self.verify(Mpps > 0.5, "%s can not receive packets" % self.running_case)
        return Mpps

    def send_and_verify(self, case_info, frame_size, restart_times=1):
        """
        start to send packets and calculate the average throughput
        """
        # start to send packets
        self.vhost.send_expect("set txpkts %s" % frame_size, "testpmd>", 60)
        self.vhost.send_expect("start tx_first 32", "testpmd>", 60)
        Mpps = self.calculate_avg_throughput()
        self.update_table_info(case_info, frame_size, Mpps, "Before Restart")

        self.port_restart(restart_times)
        Mpps = self.calculate_avg_throughput()
        self.update_table_info(case_info, frame_size, Mpps, "After Restart and set burst to 1")

    def close_all_testpmd(self):
        """
        close testpmd about vhost-user and virtio-user
        """
        self.vhost.send_expect("quit", "#", 60)
        self.virtio_user.send_expect("quit", "#", 60)

    def close_all_session(self):
        """
        close session of vhost-user and virtio-user
        """
        self.dut.close_session(self.vhost)
        self.dut.close_session(self.virtio_user)

    def test_loopback_test_with_packed_ring_mergeable_path(self):
        """
        performance for [frame_sizes] and restart port on virtio1.1 mergeable path
        """
        pmd_arg = {"version": "packed_vq=1,in_order=0,mrg_rxbuf=1 ",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip "}
        for frame_size in self.frame_sizes:
            self.start_vhost_testpmd()
            self.start_virtio_user_testpmd(pmd_arg)
            self.send_and_verify("packed ring mergeable", frame_size)
            self.close_all_testpmd()
        self.result_table_print()

    def test_loopback_test_with_packed_ring_nonmergeable_path(self):
        """
        performance for [frame_sizes] and restart port ob virtio1.1 normal path
        """
        pmd_arg = {"version": "packed_vq=1,in_order=0,mrg_rxbuf=0 ",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip "}
        for frame_size in self.frame_sizes:
            self.start_vhost_testpmd()
            self.start_virtio_user_testpmd(pmd_arg)
            self.send_and_verify("packed ring non-mergeable", frame_size)
            self.close_all_testpmd()
        self.result_table_print()

    def test_lookback_test_with_packed_ring_inorder_mergeable_path(self):
        pmd_arg = {"version": "packed_vq=1,mrg_rxbuf=1,in_order=1",
                   "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        for frame_size in self.frame_sizes:
            self.start_vhost_testpmd()
            self.start_virtio_user_testpmd(pmd_arg)
            self.send_and_verify("packed ring non-mergeable", frame_size)
            self.close_all_testpmd()
        self.result_table_print()

    def test_lookback_test_with_packed_ring_inorder_nonmergeable_path(self):
        """
        performance for [frame_sizes] and restart port on inorder mergeable path
        """
        pmd_arg = {"version": "packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1",
                          "path": "--rx-offloads=0x10 --enable-hw-vlan-strip"}
        for frame_size in self.frame_sizes:
            self.start_vhost_testpmd()
            self.start_virtio_user_testpmd(pmd_arg)
            self.send_and_verify("packed ring inorder non-mergeable", frame_size)
            self.close_all_testpmd()
        self.result_table_print()

    def test_lookback_test_with_packed_ring_vectorized_path(self):
        """
        performance for [frame_sizes] and restart port on inorder mergeable path
        """
        pmd_arg = {"version": "packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        for frame_size in self.frame_sizes:
            self.start_vhost_testpmd()
            self.start_virtio_user_testpmd(pmd_arg)
            self.send_and_verify("packed ring inorder non-mergeable", frame_size)
            self.close_all_testpmd()
        self.result_table_print()

    def test_lookback_test_with_split_ring_inorder_mergeable_path(self):
        """
        performance for [frame_sizes] and restart port on inorder normal path
        """
        pmd_arg = {"version": "packed_vq=0,in_order=1,mrg_rxbuf=1",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip "}
        for frame_size in self.frame_sizes:
            self.start_vhost_testpmd()
            self.start_virtio_user_testpmd(pmd_arg)
            self.send_and_verify("split ring inorder mergeable", frame_size)
            self.close_all_testpmd()
        self.result_table_print()

    def test_lookback_test_with_split_ring_inorder_nonmergeable_path(self):
        """
        performance for [frame_sizes] and restart port on virtio normal path
        """
        pmd_arg = {"version": "packed_vq=0,in_order=1,mrg_rxbuf=0 ",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip "}
        for frame_size in self.frame_sizes:
            self.start_vhost_testpmd()
            self.start_virtio_user_testpmd(pmd_arg)
            self.send_and_verify("split ring inorder non-mergeable", frame_size)
            self.close_all_testpmd()
        self.result_table_print()

    def test_lookback_test_with_split_ring_mergeable_path(self):
        """
        performance for [frame_sizes] and restart port on virtio normal path
        """
        pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=1",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip "}
        for frame_size in self.frame_sizes:
            self.start_vhost_testpmd()
            self.start_virtio_user_testpmd(pmd_arg)
            self.send_and_verify("split ring mergeable", frame_size, restart_times=100)
            self.close_all_testpmd()
        self.result_table_print()

    def test_lookback_test_with_split_ring_nonmergeable_path(self):
        """
        performance for [frame_sizes] and restart port on virtio normal path
        """
        pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=0,vectorized=1",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip "}
        for frame_size in self.frame_sizes:
            self.start_vhost_testpmd()
            self.start_virtio_user_testpmd(pmd_arg)
            self.send_and_verify("split ring non-mergeable", frame_size)
            self.close_all_testpmd()
        self.result_table_print()

    def test_loopback_test_with_split_ring_vector_rx_path(self):
        """
        performance for frame_sizes and restart port on virtio vector rx
        """
        pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=0,vectorized=1",
                          "path": "--tx-offloads=0x0 "}
        for frame_size in self.frame_sizes:
            self.start_vhost_testpmd()
            self.start_virtio_user_testpmd(pmd_arg)
            self.send_and_verify("split ring vector_rx", frame_size)
            self.close_all_testpmd()
        self.result_table_print()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.close_all_session()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
