# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

"""
DPDK Test suite.
Benchmark Vhost loopback for 7 RX/TX PATHs.
Includes Mergeable, Normal, Vector_RX,Inorder_mergeable,
Inorder_no_mergeable, VIRTIO1.1_mergeable, VIRTIO1.1_normal Path.
"""
import re
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


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
            self.core_config, socket=self.ports_socket
        )
        self.core_list_user = self.core_list[0:2]
        self.core_list_host = self.core_list[2:5]
        self.path = self.dut.apps_name["test-pmd"]
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
        self.vhost_pmd = PmdOutput(self.dut, self.vhost)
        self.virtio_user_pmd = PmdOutput(self.dut, self.virtio_user)

    def start_vhost_testpmd(self):
        """
        start testpmd on vhost
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        eal_params = "--vdev 'net_vhost0,iface=vhost-net,queues=1,client=0'"
        param = "--nb-cores=1 --txd=1024 --rxd=1024"
        self.vhost_pmd.start_testpmd(
            self.core_list_host,
            param=param,
            no_pci=True,
            ports=[],
            eal_param=eal_params,
            prefix="vhost",
            fixed_prefix=True,
        )
        self.vhost_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def start_virtio_user_testpmd(self, pmd_arg):
        """
        start testpmd of vhost user
        """
        eal_param = "--vdev 'net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,{}'".format(
            pmd_arg["version"]
        )
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        if "vectorized_path" in self.running_case:
            eal_param += " --force-max-simd-bitwidth=512"
        param = "{} --rss-ip --nb-cores=1 --txd=1024 --rxd=1024".format(pmd_arg["path"])
        self.virtio_user_pmd.start_testpmd(
            cores=self.core_list_user,
            param=param,
            eal_param=eal_param,
            no_pci=True,
            ports=[],
            prefix="virtio",
            fixed_prefix=True,
        )

        self.virtio_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)
        self.virtio_user_pmd.execute_cmd("start", "testpmd> ", 120)

    def check_port_throughput_after_port_stop(self):
        """
        check the throughput after port stop
        """
        loop = 1
        while loop <= 5:
            out = self.vhost_pmd.execute_cmd("show port stats 0", "testpmd>", 60)
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            if result == "0":
                break
            time.sleep(3)
            loop = loop + 1
        self.verify(
            result == "0", "port stop failed, it alse can recevie data after stop."
        )

    def check_port_link_status_after_port_restart(self):
        """
        check the link status after port restart
        """
        loop = 1
        while loop <= 5:
            out = self.vhost_pmd.execute_cmd("show port info all", "testpmd> ", 120)
            port_status = re.findall("Link\s*status:\s*([a-z]*)", out)
            if "down" not in port_status:
                break
            time.sleep(3)
            loop = loop + 1
        self.verify("down" not in port_status, "port can not up after restart")

    def port_restart(self, restart_times=1):
        if restart_times == 1:
            self.vhost_pmd.execute_cmd("stop", "testpmd> ", 120)
            self.vhost_pmd.execute_cmd("port stop 0", "testpmd> ", 120)
            self.check_port_throughput_after_port_stop()
            self.vhost_pmd.execute_cmd("clear port stats all", "testpmd> ", 120)
            self.vhost_pmd.execute_cmd("port start all", "testpmd> ", 120)
        else:
            for i in range(restart_times):
                self.vhost_pmd.execute_cmd("stop", "testpmd> ", 120)
                self.vhost_pmd.execute_cmd("port stop 0", "testpmd> ", 120)
                self.vhost_pmd.execute_cmd("clear port stats all", "testpmd> ", 120)
                self.vhost_pmd.execute_cmd("port start all", "testpmd> ", 120)
        self.check_port_link_status_after_port_restart()
        self.vhost_pmd.execute_cmd("set burst 1", "testpmd> ", 120)
        self.vhost_pmd.execute_cmd("start tx_first 1", "testpmd> ", 120)

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
        self.vhost_pmd.execute_cmd("show port stats all", "testpmd>", 60)
        for i in range(10):
            out = self.vhost_pmd.execute_cmd("show port stats all", "testpmd>", 60)
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
        self.vhost_pmd.execute_cmd("set txpkts %s" % frame_size, "testpmd>", 60)
        self.vhost_pmd.execute_cmd("start tx_first 32", "testpmd>", 60)
        Mpps = self.calculate_avg_throughput()
        self.update_table_info(case_info, frame_size, Mpps, "Before Restart")

        self.port_restart(restart_times)
        Mpps = self.calculate_avg_throughput()
        self.update_table_info(
            case_info, frame_size, Mpps, "After Restart and set burst to 1"
        )

    def close_all_testpmd(self):
        """
        close testpmd about vhost-user and virtio-user
        """
        self.vhost_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user_pmd.execute_cmd("quit", "#", 60)

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
        pmd_arg = {
            "version": "packed_vq=1,in_order=0,mrg_rxbuf=1 ",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip ",
        }
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
        pmd_arg = {
            "version": "packed_vq=1,in_order=0,mrg_rxbuf=0 ",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip ",
        }
        for frame_size in self.frame_sizes:
            self.start_vhost_testpmd()
            self.start_virtio_user_testpmd(pmd_arg)
            self.send_and_verify("packed ring non-mergeable", frame_size)
            self.close_all_testpmd()
        self.result_table_print()

    def test_lookback_test_with_packed_ring_inorder_mergeable_path(self):
        pmd_arg = {
            "version": "packed_vq=1,mrg_rxbuf=1,in_order=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
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
        pmd_arg = {
            "version": "packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1",
            "path": "--rx-offloads=0x10 --enable-hw-vlan-strip",
        }
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
        pmd_arg = {
            "version": "packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
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
        pmd_arg = {
            "version": "packed_vq=0,in_order=1,mrg_rxbuf=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip ",
        }
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
        pmd_arg = {
            "version": "packed_vq=0,in_order=1,mrg_rxbuf=0 ",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip ",
        }
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
        pmd_arg = {
            "version": "packed_vq=0,in_order=0,mrg_rxbuf=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip ",
        }
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
        pmd_arg = {
            "version": "packed_vq=0,in_order=0,mrg_rxbuf=0,vectorized=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip ",
        }
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
        pmd_arg = {
            "version": "packed_vq=0,in_order=0,mrg_rxbuf=0,vectorized=1",
            "path": "--tx-offloads=0x0 ",
        }
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
