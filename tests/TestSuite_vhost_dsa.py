# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import json
import os
import re
from copy import deepcopy

import framework.rst as rst
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE, UPDATE_EXPECTED, load_global_setting
from framework.test_case import TestCase

from .virtio_common import dsa_common as DC

SPLIT_RING_PATH = {
    "inorder_mergeable": "mrg_rxbuf=1,in_order=1",
    "mergeable": "mrg_rxbuf=1,in_order=0",
    "inorder_non_mergeable": "mrg_rxbuf=0,in_order=1",
    "non_mergeable": "mrg_rxbuf=0,in_order=0",
    "vectorized": "mrg_rxbuf=0,in_order=0,vectorized=1",
}

PACKED_RING_PATH = {
    "inorder_mergeable": "mrg_rxbuf=1,in_order=1,packed_vq=1",
    "mergeable": "mrg_rxbuf=1,in_order=0,packed_vq=1",
    "inorder_non_mergeable": "mrg_rxbuf=0,in_order=1,packed_vq=1",
    "non_mergeable": "mrg_rxbuf=0,in_order=0,packed_vq=1",
    "vectorized": "mrg_rxbuf=0,in_order=0,vectorized=1,packed_vq=1",
    "vectorized_path_not_power_of_2": "mrg_rxbuf=0,in_order=0,vectorized=1,packed_vq=1,queue_size=1025",
}


class TestVhostDsa(TestCase):
    def set_up_all(self):
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.number_of_ports = 1
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user_pmd = PmdOutput(self.dut, self.virtio_user)
        self.virtio_mac = "00:01:02:03:04:05"
        self.headers_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"] + HEADER_SIZE["tcp"]
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_core_list = self.cores_list[0:9]
        self.virtio_core_list = self.cores_list[10:15]
        self.out_path = "/tmp/%s" % self.suite_name
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        self.pktgen_helper = PacketGeneratorHelper()
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.testpmd_name = self.dut.apps_name["test-pmd"].split("/")[-1]
        self.save_result_flag = True
        self.json_obj = {}
        self.DC = DC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        self.table_header = ["Frame", "Mode/RXD-TXD", "Mpps", "% linerate"]
        self.result_table_create(self.table_header)
        self.test_parameters = self.get_suite_cfg()["test_parameters"]
        self.test_duration = self.get_suite_cfg()["test_duration"]
        self.throughput = {}
        self.gap = self.get_suite_cfg()["accepted_tolerance"]
        self.test_result = {}
        self.nb_desc = self.test_parameters.get(list(self.test_parameters.keys())[0])[0]
        self.dut.send_expect("killall -I %s" % self.testpmd_name, "#", 20)
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.mode_list = []
        self.DC.reset_all_work_queue()
        self.DC.bind_all_dsa_to_kernel()

    def get_vhost_port_num(self):
        out = self.vhost_user.send_expect("show port summary all", "testpmd> ", 60)
        port_num = re.search("Number of available ports:\s*(\d*)", out)
        return int(port_num.group(1))

    def check_each_queue_of_port_packets(self, queues):
        """
        check each queue of each port has receive packets
        """
        self.logger.info(self.vhost_user_pmd.execute_cmd("show port stats all"))
        out = self.vhost_user_pmd.execute_cmd("stop")
        self.logger.info(out)
        port_num = self.get_vhost_port_num()
        for port in range(port_num):
            for queue in range(queues):
                if queues == 1:
                    reg = "Forward statistics for port %d" % port
                else:
                    reg = "Port= %d/Queue= %d" % (port, queue)
                index = out.find(reg)
                rx = re.search("RX-packets:\s*(\d*)", out[index:])
                tx = re.search("TX-packets:\s*(\d*)", out[index:])
                rx_packets = int(rx.group(1))
                tx_packets = int(tx.group(1))
                self.verify(
                    rx_packets > 0 and tx_packets > 0,
                    "The port %d/queue %d rx-packets or tx-packets is 0 about "
                    % (port, queue)
                    + "rx-packets: %d, tx-packets: %d" % (rx_packets, tx_packets),
                )
        self.vhost_user_pmd.execute_cmd("start")

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def start_vhost_testpmd(
        self,
        cores="Default",
        param="",
        eal_param="",
        ports="",
        port_options="",
        iova_mode="va",
    ):
        eal_param += " --iova=" + iova_mode
        if port_options != "":
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                param=param,
                eal_param=eal_param,
                ports=ports,
                port_options=port_options,
                prefix="vhost",
            )
        else:
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                param=param,
                eal_param=eal_param,
                ports=ports,
                prefix="vhost",
            )
        if self.nic == "I40E_40G-QSFP_A":
            self.vhost_user_pmd.execute_cmd("port config all rss ipv4-tcp")
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

    def start_virtio_testpmd(self, cores="Default", param="", eal_param=""):
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        self.virtio_user_pmd.start_testpmd(
            cores=cores, param=param, eal_param=eal_param, no_pci=True, prefix="virtio"
        )
        # self.virtio_user_pmd.execute_cmd("set fwd csum")
        self.virtio_user_pmd.execute_cmd("set fwd mac")
        self.virtio_user_pmd.execute_cmd("start")

    def test_perf_pvp_split_ring_vhost_async_operation_test_with_each_tx_rx_queue_using_1_dpdk_driver(
        self,
    ):
        """
        Test Case 1: PVP split ring vhost async operation test with each tx/rx queue using one DSA dpdk driver channel
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "rxq0@%s-q2;"
            "rxq1@%s-q3"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024"

        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.use_dsa_list:
            ports.append(i)
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024"
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=2'"
                % (self.virtio_mac, path)
            )
            if key == "non_mergeable":
                new_virtio_param = "--enable-hw-vlan-strip  " + virtio_param
            else:
                new_virtio_param = virtio_param

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=new_virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            dmas = (
                "txq0@%s-q0;"
                "txq1@%s-q1;"
                "rxq0@%s-q0;"
                "rxq1@%s-q1"
                % (
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[1],
                    self.use_dsa_list[1],
                )
            )
            vhost_param = "--nb-cores=2 --txq=2 --rxq=2 --txd=1024 --rxd=1024"
            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=2,dmas=[%s]'" % dmas
            )
            port_options = {
                self.use_dsa_list[0]: "max_queues=2",
                self.use_dsa_list[1]: "max_queues=2",
            }
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=ports,
                port_options=port_options,
                iova_mode="pa",
            )
            for key, path in SPLIT_RING_PATH.items():
                if key == "inorder_mergeable":
                    virtio_eal_param = (
                        "--vdev 'net_virtio_user0,mac=%s,path=./vhost-net0,%s,queues=2'"
                        % (self.virtio_mac, path)
                    )

                    mode = key + "_PA"
                    self.mode_list.append(mode)
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=2)

                    mode += "_RestartVhost"
                    self.vhost_user_pmd.execute_cmd("start")
                    self.mode_list.append(mode)
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=2)
                    self.virtio_user_pmd.quit()

        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_ring_vhost_async_operation_test_with_dpdk_driver_being_shared_among_multi_tx_rx_queue(
        self,
    ):
        """
        Test Case 2: PVP split ring vhost async operations test with one DSA dpdk driver channel being shared among multiple tx/rx queues
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "txq6@%s-q1;"
            "txq7@%s-q1;"
            "rxq0@%s-q0;"
            "rxq1@%s-q0;"
            "rxq2@%s-q0;"
            "rxq3@%s-q0;"
            "rxq4@%s-q1;"
            "rxq5@%s-q1;"
            "rxq6@%s-q1;"
            "rxq7@%s-q1"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.use_dsa_list:
            ports.append(i)
        port_options = {self.use_dsa_list[0]: "max_queues=2"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8'"
                % (self.virtio_mac, path)
            )
            if key == "non_mergeable":
                new_virtio_param = "--enable-hw-vlan-strip  " + virtio_param
            else:
                new_virtio_param = virtio_param

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=new_virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            dmas = (
                "txq0@%s-q0;"
                "txq1@%s-q1;"
                "txq2@%s-q2;"
                "txq3@%s-q3;"
                "txq4@%s-q4;"
                "txq5@%s-q5;"
                "txq6@%s-q6;"
                "txq7@%s-q7;"
                "rxq0@%s-q0;"
                "rxq1@%s-q1;"
                "rxq2@%s-q2;"
                "rxq3@%s-q3;"
                "rxq4@%s-q4;"
                "rxq5@%s-q5;"
                "rxq6@%s-q6;"
                "rxq7@%s-q7"
                % (
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                )
            )
            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[%s]'" % dmas
            )
            vhost_param = "--nb-cores=6 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
            port_options = {self.use_dsa_list[0]: "max_queues=8"}
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=ports,
                port_options=port_options,
                iova_mode="pa",
            )
            for key, path in SPLIT_RING_PATH.items():
                if key == "mergeable":
                    virtio_eal_param = (
                        "--vdev 'net_virtio_user0,mac=%s,path=./vhost-net0,%s,queues=8'"
                        % (self.virtio_mac, path)
                    )

                    mode = key + "_PA"
                    self.mode_list.append(mode)
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

                    mode += "_RestartVhost"
                    self.vhost_user_pmd.execute_cmd("start")
                    self.mode_list.append(mode)
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)
                    self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            dmas = (
                "txq0@%s-q0;"
                "txq1@%s-q0;"
                "txq2@%s-q0;"
                "txq3@%s-q0;"
                "txq4@%s-q0;"
                "txq5@%s-q0;"
                "txq6@%s-q0;"
                "txq7@%s-q0;"
                "rxq0@%s-q0;"
                "rxq1@%s-q0;"
                "rxq2@%s-q0;"
                "rxq3@%s-q0;"
                "rxq4@%s-q0;"
                "rxq5@%s-q0;"
                "rxq6@%s-q0;"
                "rxq7@%s-q0"
                % (
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                )
            )
            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[%s]'" % dmas
            )
            vhost_param = "--nb-cores=6 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
            port_options = {self.use_dsa_list[0]: "max_queues=1"}
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=ports,
                port_options=port_options,
                iova_mode="pa",
            )
            for key, path in SPLIT_RING_PATH.items():
                if key == "inorder_non_mergeable":
                    virtio_eal_param = (
                        "--vdev 'net_virtio_user0,mac=%s,path=./vhost-net0,%s,queues=8'"
                        % (self.virtio_mac, path)
                    )

                    mode = key + "_PA"
                    self.mode_list.append(mode)
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

                    mode += "_RestartVhost"
                    self.vhost_user_pmd.execute_cmd("start")
                    self.mode_list.append(mode)
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)
                    self.virtio_user_pmd.quit()

        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_ring_dynamic_queues_vhost_async_operation_with_dpdk_driver(
        self,
    ):
        """
        Test Case 3: PVP split ring dynamic queues vhost async operation with dsa dpdk driver channels
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "txq2@%s-q2;"
            "txq3@%s-q2"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.use_dsa_list:
            ports.append(i)
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8,server=1'"
                % (self.virtio_mac, path)
            )
            if key == "inorder_mergeable":
                mode = key + "_VA_4_queue"
                self.mode_list.append(mode)
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=2)

        self.vhost_user_pmd.quit()
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,'"
        vhost_param = "--nb-cores=2 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=[self.dut.ports_info[0]["pci"]],
            port_options="",
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_1_queue_wo_dsa"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=1)

        self.vhost_user_pmd.quit()
        dmas = (
            "rxq0@%s-q0;"
            "rxq1@%s-q1;"
            "rxq2@%s-q1;"
            "rxq3@%s-q0"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024"
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_4_queue_diff"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=4)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q2;"
            "rxq2@%s-q0;"
            "rxq3@%s-q1;"
            "rxq4@%s-q2;"
            "rxq5@%s-q2;"
            "rxq6@%s-q2;"
            "rxq7@%s-q2"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        port_options = {
            self.use_dsa_list[0]: "max_queues=4",
            self.use_dsa_list[1]: "max_queues=4",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_8_queue_diff"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.virtio_user_pmd.quit()
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        for key, path in SPLIT_RING_PATH.items():
            if key == "non_mergeable":
                virtio_eal_param = (
                    "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8,server=1'"
                    % (self.virtio_mac, path)
                )
                mode = key + "_VA_8_queue_diff"
                self.mode_list.append(mode)
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "rxq1@%s-q1;"
            "rxq2@%s-q1;"
            "rxq3@%s-q1"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        port_options = {self.use_dsa_list[0]: "max_queues=2"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="pa",
        )
        mode = "non_mergeable" + "_PA_4_queue_diff"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_ring_vhost_async_operation_test_with_each_tx_rx_queue_using_1_dpdk_driver(
        self,
    ):
        """
        Test Case 4: PVP packed ring vhost async operation test with each tx/rx queue using one DSA dpdk driver channel
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "rxq0@%s-q2;"
            "rxq1@%s-q2"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.use_dsa_list:
            ports.append(i)
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=2'"
                % (self.virtio_mac, path)
            )
            if "vectorized" in key:
                virtio_eal_param = "--force-max-simd-bitwidth=512  " + virtio_eal_param
            if key == "vectorized_path_not_power_of_2":
                virtio_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1025 --rxd=1025"
            else:
                virtio_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024"

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            dmas = (
                "txq0@%s-q0;"
                "txq1@%s-q1;"
                "rxq0@%s-q0;"
                "rxq1@%s-q1"
                % (
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[1],
                    self.use_dsa_list[1],
                )
            )
            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=2,dmas=[%s]'" % dmas
            )
            vhost_param = "--nb-cores=2 --txq=2 --rxq=2 --txd=1024 --rxd=1024"
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=ports,
                port_options=port_options,
                iova_mode="pa",
            )
            virtio_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024"
            for key, path in PACKED_RING_PATH.items():
                if key == "inorder_mergeable":
                    virtio_eal_param = (
                        "--vdev 'net_virtio_user0,mac=%s,path=./vhost-net0,%s,queues=2'"
                        % (self.virtio_mac, path)
                    )

                    mode = key + "_PA"
                    self.mode_list.append(mode)
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=2)

                    mode += "_RestartVhost"
                    self.vhost_user_pmd.execute_cmd("start")
                    self.mode_list.append(mode)
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=2)
                    self.virtio_user_pmd.quit()

        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_ring_vhost_async_operation_test_with_1_dpdk_driver_being_shared_among_multi_tx_rx_queue(
        self,
    ):
        """
        Test Case 5: PVP packed ring vhost async operation test with one DSA dpdk driver channel being shared among multiple tx/rx queues
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "txq6@%s-q1;"
            "txq7@%s-q1;"
            "rxq0@%s-q0;"
            "rxq1@%s-q0;"
            "rxq2@%s-q0;"
            "rxq3@%s-q0;"
            "rxq4@%s-q1;"
            "rxq5@%s-q1;"
            "rxq6@%s-q1;"
            "rxq7@%s-q1"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.use_dsa_list:
            ports.append(i)
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8'"
                % (self.virtio_mac, path)
            )
            if "vectorized" in key:
                virtio_eal_param = "--force-max-simd-bitwidth=512  " + virtio_eal_param
            if key == "vectorized_path_not_power_of_2":
                virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1025 --rxd=1025"
            else:
                virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            dmas = (
                "txq0@%s-q0;"
                "txq1@%s-q0;"
                "txq2@%s-q0;"
                "txq3@%s-q0;"
                "txq4@%s-q0;"
                "txq5@%s-q0;"
                "txq6@%s-q0;"
                "txq7@%s-q0;"
                "rxq0@%s-q0;"
                "rxq1@%s-q0;"
                "rxq2@%s-q0;"
                "rxq3@%s-q0;"
                "rxq4@%s-q0;"
                "rxq5@%s-q0;"
                "rxq6@%s-q0;"
                "rxq7@%s-q0"
                % (
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                    self.use_dsa_list[0],
                )
            )
            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[%s]'" % dmas
            )
            vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=ports,
                port_options=port_options,
                iova_mode="pa",
            )
            virtio_param = "--nb-cores=2 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
            for key, path in PACKED_RING_PATH.items():
                if key == "inorder_non_mergeable":
                    virtio_eal_param = (
                        "--vdev 'net_virtio_user0,mac=%s,path=./vhost-net0,%s,queues=8'"
                        % (self.virtio_mac, path)
                    )

                    mode = key + "_PA"
                    self.mode_list.append(mode)
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

                    mode += "_RestartVhost"
                    self.vhost_user_pmd.execute_cmd("start")
                    self.mode_list.append(mode)
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)
                    self.virtio_user_pmd.quit()

        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_ring_dynamic_queues_vhost_async_operation_with_dpdk_driver(
        self,
    ):
        """
        Test Case 6: PVP packed ring dynamic queues vhost async operation with dsa dpdk driver channels
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q1"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.use_dsa_list:
            ports.append(i)
        port_options = {
            self.use_dsa_list[0]: "max_queues=4",
            self.use_dsa_list[1]: "max_queues=4",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8,server=1'"
                % (self.virtio_mac, path)
            )
            if key == "inorder_mergeable":
                mode = key + "_VA_4_queue"
                self.mode_list.append(mode)
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=2)

        self.vhost_user_pmd.quit()
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,'"
        vhost_param = "--nb-cores=2 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=[self.dut.ports_info[0]["pci"]],
            port_options="",
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_1_queue_wo_dsa"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=1)

        self.vhost_user_pmd.quit()
        dmas = (
            "rxq0@%s-q0;"
            "rxq1@%s-q1;"
            "rxq2@%s-q1"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_4_queue_diff"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=4)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q2;"
            "rxq2@%s-q0;"
            "rxq3@%s-q1;"
            "rxq4@%s-q2;"
            "rxq5@%s-q2;"
            "rxq6@%s-q2;"
            "rxq7@%s-q2"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=2 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_8_queue_diff"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.virtio_user_pmd.quit()
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        for key, path in PACKED_RING_PATH.items():
            if key == "non_mergeable":
                virtio_eal_param = (
                    "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8,server=1'"
                    % (self.virtio_mac, path)
                )
                mode = key + "_VA_8_queue_diff"
                self.mode_list.append(mode)
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "rxq1@%s-q1;"
            "rxq2@%s-q1;"
            "rxq3@%s-q1"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="pa",
        )
        mode = "non_mergeable" + "_PA_4_queue_diff"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_ring_vhost_async_operation_test_with_each_tx_rx_queue_using_1_kernel_driver(
        self,
    ):
        """
        Test Case 7: PVP split ring vhost async operation test with each tx/rx queue using one DSA kernel driver channel
        """
        self.DC.create_work_queue(work_queue_number=4, dsa_index=0)
        dmas = "txq0@wq0.0;" "txq1@wq0.1;" "rxq0@wq0.2;" "rxq1@wq0.3"
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        virtio_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024"
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=2'"
                % (self.virtio_mac, path)
            )
            if key == "non_mergeable":
                new_virtio_param = "--enable-hw-vlan-strip  " + virtio_param
            else:
                new_virtio_param = virtio_param

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=new_virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)
            self.virtio_user_pmd.quit()

        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_ring_vhost_async_operation_test_with_1_kernel_driver_being_shared_among_multi_tx_rx_queue(
        self,
    ):
        """
        Test Case 8: PVP split ring all path multi-queues vhost async operation test with one DSA kernel driver channel being shared among multiple tx/rx queues
        """
        self.DC.create_work_queue(work_queue_number=4, dsa_index=0)
        dmas = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.1;"
            "txq6@wq0.1;"
            "txq7@wq0.1;"
            "rxq0@wq0.0;"
            "rxq1@wq0.0;"
            "rxq2@wq0.0;"
            "rxq3@wq0.0;"
            "rxq4@wq0.1;"
            "rxq5@wq0.1;"
            "rxq6@wq0.1;"
            "rxq7@wq0.1"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8'"
                % (self.virtio_mac, path)
            )
            if key == "non_mergeable":
                new_virtio_param = "--enable-hw-vlan-strip  " + virtio_param
            else:
                new_virtio_param = virtio_param

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=new_virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            dmas = (
                "txq0@wq0.0;"
                "txq1@wq0.0;"
                "txq2@wq0.1;"
                "txq3@wq0.1;"
                "txq4@wq0.2;"
                "txq5@wq0.2;"
                "txq6@wq0.3;"
                "txq7@wq0.3;"
                "rxq0@wq0.0;"
                "rxq1@wq0.0;"
                "rxq2@wq0.1;"
                "rxq3@wq0.1;"
                "rxq4@wq0.2;"
                "rxq5@wq0.2;"
                "rxq6@wq0.3;"
                "rxq7@wq0.3"
            )
            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[%s]'" % dmas
            )
            vhost_param = "--nb-cores=6 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
            ports = [self.dut.ports_info[0]["pci"]]
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=ports,
                port_options="",
                iova_mode="pa",
            )
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_ring_dynamic_queue_vhost_async_operation_with_dsa_kernel_driver(
        self,
    ):
        """
        Test Case 9: PVP split ring dynamic queues vhost async operation with dsa kernel driver channels
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.DC.create_work_queue(work_queue_number=8, dsa_index=1)
        dmas = "txq0@wq0.0;" "txq1@wq0.1;" "txq2@wq0.2;" "txq3@wq0.2"
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8,server=1'"
                % (self.virtio_mac, path)
            )
            if key == "inorder_mergeable":
                mode = key + "_VA_4_queue"
                self.mode_list.append(mode)
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=2)

        self.vhost_user_pmd.quit()
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,'"
        vhost_param = "--nb-cores=2 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=[self.dut.ports_info[0]["pci"]],
            port_options="",
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_1_queue_wo_dsa"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=1)

        self.vhost_user_pmd.quit()
        dmas = "rxq0@wq0.0;" "rxq1@wq0.1;" "rxq2@wq0.1;" "rxq3@wq0.0"
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_4_queue_diff"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=4)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.2;"
            "rxq2@wq1.0;"
            "rxq3@wq1.1;"
            "rxq4@wq1.2;"
            "rxq5@wq1.2;"
            "rxq6@wq1.2;"
            "rxq7@wq1.2"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_8_queue_diff"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@wq0.0;"
            "txq1@wq0.1;"
            "txq2@wq0.2;"
            "txq3@wq0.3;"
            "txq4@wq0.4;"
            "txq5@wq0.5;"
            "rxq2@wq1.2;"
            "rxq3@wq1.3;"
            "rxq4@wq1.4;"
            "rxq5@wq1.5;"
            "rxq6@wq1.6;"
            "rxq7@wq1.7"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_8_queue_diff_1"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.virtio_user_pmd.quit()
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        for key, path in SPLIT_RING_PATH.items():
            if key == "non_mergeable":
                virtio_eal_param = (
                    "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8,server=1'"
                    % (self.virtio_mac, path)
                )
                mode = key + "_VA_8_queue_diff"
                self.mode_list.append(mode)
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_ring_vhost_async_operation_test_with_each_tx_rx_queue_using_1_dsa_kernel_driver(
        self,
    ):
        """
        Test Case 10: PVP packed ring all path multi-queues vhost async operation test with each tx/rx queue using one DSA kernel driver channel

        """
        self.DC.create_work_queue(work_queue_number=2, dsa_index=0)
        self.DC.create_work_queue(work_queue_number=2, dsa_index=1)
        dmas = "txq0@wq0.0;" "txq1@wq0.1;" "rxq0@wq1.0;" "rxq1@wq1.1"
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=2'"
                % (self.virtio_mac, path)
            )
            if "vectorized" in key:
                virtio_eal_param = "--force-max-simd-bitwidth=512  " + virtio_eal_param
            if key == "vectorized_path_not_power_of_2":
                virtio_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1025 --rxd=1025"
            else:
                virtio_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024"

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)
            self.virtio_user_pmd.quit()

        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_ring_vhost_async_operation_test_with_1_kernel_driver_being_shared_among_multi_tx_rx_queue(
        self,
    ):
        """
        Test Case 11: PVP packed ring all path multi-queues vhost async operation test with one DSA kernel driver channel being shared among multiple tx/rx queues
        """
        self.DC.create_work_queue(work_queue_number=2, dsa_index=0)
        dmas = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.1;"
            "txq6@wq0.1;"
            "txq7@wq0.1;"
            "rxq0@wq0.0;"
            "rxq1@wq0.0;"
            "rxq2@wq0.0;"
            "rxq3@wq0.0;"
            "rxq4@wq0.1;"
            "rxq5@wq0.1;"
            "rxq6@wq0.1;"
            "rxq7@wq0.1"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8'"
                % (self.virtio_mac, path)
            )
            if "vectorized" in key:
                virtio_eal_param = "--force-max-simd-bitwidth=512  " + virtio_eal_param
            if key == "vectorized_path_not_power_of_2":
                virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1025 --rxd=1025"
            else:
                virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=2)
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            dmas = (
                "txq0@wq0.0;"
                "txq1@wq0.0;"
                "txq2@wq0.0;"
                "txq3@wq0.0;"
                "txq4@wq0.1;"
                "txq5@wq0.1;"
                "txq6@wq0.1;"
                "txq7@wq0.1;"
                "rxq0@wq0.0;"
                "rxq1@wq0.0;"
                "rxq2@wq0.0;"
                "rxq3@wq0.0;"
                "rxq4@wq0.1;"
                "rxq5@wq0.1;"
                "rxq6@wq0.1;"
                "rxq7@wq0.1"
            )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=6 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="pa",
        )
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_ring_dynamic_queues_vhost_async_operation_with_dsa_kernel_driver(
        self,
    ):
        """
        Test Case 12: PVP packed ring dynamic queues vhost async operation with dsa kernel driver channels
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.DC.create_work_queue(work_queue_number=8, dsa_index=1)
        dmas = "txq0@wq0.0;" "txq1@wq0.1;" "txq2@wq0.2;" "txq3@wq0.2"
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8,server=1'"
                % (self.virtio_mac, path)
            )
            if key == "inorder_mergeable":
                mode = key + "_VA_4_queue"
                self.mode_list.append(mode)
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=2)

        self.vhost_user_pmd.quit()
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,'"
        vhost_param = "--nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=[self.dut.ports_info[0]["pci"]],
            port_options="",
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_1_queue_wo_dsa"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=1)

        self.vhost_user_pmd.quit()
        dmas = "rxq0@wq0.0;" "rxq1@wq0.1;" "rxq2@wq0.1;" "rxq3@wq0.0"
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_4_queue_diff"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=4)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.2;"
            "rxq2@wq1.0;"
            "rxq3@wq1.1;"
            "rxq4@wq1.2;"
            "rxq5@wq1.2;"
            "rxq6@wq1.2;"
            "rxq7@wq1.2"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=2 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_8_queue_diff"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@wq0.0;"
            "txq1@wq0.1;"
            "txq2@wq0.2;"
            "txq3@wq0.3;"
            "txq4@wq0.4;"
            "txq5@wq0.5;"
            "rxq2@wq1.2;"
            "rxq3@wq1.3;"
            "rxq4@wq1.4;"
            "rxq5@wq1.5;"
            "rxq6@wq1.6;"
            "rxq7@wq1.7"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_8_queue_diff_1"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.virtio_user_pmd.quit()
        virtio_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net0,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queues=8,server=1,queue_size=1025"
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1025 --rxd=1025"
        mode = "vectorized_path_not_power_of_2" + "_VA_8_queue_diff"
        self.start_virtio_testpmd(
            cores=self.virtio_core_list,
            param=virtio_param,
            eal_param=virtio_eal_param,
        )
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_and_packed_ring_dynamic_queues_vhost_async_operation_with_dsa_dpdk_and_kernel_driver(
        self,
    ):
        """
        Test Case 13: PVP split and packed ring dynamic queues vhost async operation with dsa dpdk and kernel driver channels
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.DC.create_work_queue(work_queue_number=8, dsa_index=1)
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=2,
            driver_name="vfio-pci",
            dsa_index_list=[2, 3],
            socket=self.ports_socket,
        )
        dmas = "txq0@wq0.0;" "txq1@wq0.0"
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options="",
            iova_mode="va",
        )
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8,server=1'"
                % (self.virtio_mac, path)
            )
            if key == "inorder_mergeable":
                mode = key + "_VA_kernel_driver"
                self.mode_list.append(mode)
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q1;"
            "txq3@%s-q1;"
            "rxq0@%s-q0;"
            "rxq1@%s-q0;"
            "rxq2@%s-q1;"
            "rxq3@%s-q2"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.use_dsa_list:
            ports.append(i)
        port_options = {
            self.use_dsa_list[0]: "max_queues=2",
            self.use_dsa_list[1]: "max_queues=4",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_dpdk_driver"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@wq0.0;"
            "txq1@wq0.1;"
            "txq2@wq0.2;"
            "txq3@wq0.3;"
            "txq4@wq0.4;"
            "txq5@wq0.5;"
            "txq6@wq0.6;"
            "rxq2@%s-q0;"
            "rxq3@%s-q1;"
            "rxq4@%s-q0;"
            "rxq5@%s-q1;"
            "rxq6@%s-q2;"
            "rxq7@%s-q3"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.use_dsa_list:
            ports.append(i)
        port_options = {
            self.use_dsa_list[0]: "max_queues=2",
            self.use_dsa_list[1]: "max_queues=4",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_kernel_dpdk_driver"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.virtio_user_pmd.quit()
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac=%s,path=vhost-net0,%s,queues=8,server=1'"
                % (self.virtio_mac, path)
            )
            if key == "inorder_mergeable":
                mode = key + "_VA_kernel_dpdk_driver_packed"
                self.mode_list.append(mode)
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@wq0.0;"
            "txq1@wq0.1;"
            "txq2@wq0.2;"
            "txq3@wq0.3;"
            "txq4@wq0.4;"
            "txq5@wq0.5;"
            "txq6@wq0.6;"
            "rxq2@%s-q0;"
            "rxq3@%s-q1;"
            "rxq4@%s-q0;"
            "rxq5@%s-q1;"
            "rxq6@%s-q2;"
            "rxq7@%s-q3"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.use_dsa_list:
            ports.append(i)
        port_options = {
            self.use_dsa_list[0]: "max_queues=2",
            self.use_dsa_list[1]: "max_queues=4",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=ports,
            port_options=port_options,
            iova_mode="va",
        )
        mode = "inorder_mergeable" + "_VA_kernel_dpdk_driver_packed_diff"
        self.mode_list.append(mode)
        self.send_imix_packets(mode=mode)
        self.check_each_queue_of_port_packets(queues=8)

        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def send_imix_packets(self, mode):
        """
        Send imix packet with packet generator and verify
        """
        frame_sizes = [64, 128, 256, 512, 1024, 1518]
        tgenInput = []
        for frame_size in frame_sizes:
            payload_size = frame_size - self.headers_size
            port = self.tester.get_local_port(self.dut_ports[0])
            fields_config = {
                "ip": {
                    "src": {"action": "random"},
                },
            }
            pkt = Packet()
            pkt.assign_layers(["ether", "ipv4", "tcp", "raw"])
            pkt.config_layers(
                [
                    ("ether", {"dst": "%s" % self.virtio_mac}),
                    ("ipv4", {"src": "1.1.1.1"}),
                    ("raw", {"payload": ["01"] * int("%d" % payload_size)}),
                ]
            )
            pkt.save_pcapfile(
                self.tester,
                "%s/%s_%s.pcap" % (self.out_path, self.suite_name, frame_size),
            )
            tgenInput.append(
                (
                    port,
                    port,
                    "%s/%s_%s.pcap" % (self.out_path, self.suite_name, frame_size),
                )
            )

        self.tester.pktgen.clear_streams()
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgenInput, 100, fields_config, self.tester.pktgen
        )
        trans_options = {"delay": 5, "duration": self.test_duration}
        bps, pps = self.tester.pktgen.measure_throughput(
            stream_ids=streams, options=trans_options
        )
        Mpps = pps / 1000000.0
        Mbps = bps / 1000000.0
        self.verify(
            Mbps > 0,
            f"{self.running_case} can not receive packets of frame size {frame_sizes}",
        )
        bps_linerate = self.wirespeed(self.nic, 64, 1) * 8 * (64 + 20)
        throughput = Mbps * 100 / float(bps_linerate)
        self.throughput[mode] = {
            "imix": {
                self.nb_desc: [Mbps, Mpps],
            }
        }
        results_row = ["imix"]
        results_row.append(mode)
        results_row.append(Mpps)
        results_row.append(throughput)
        self.result_table_add(results_row)

    def handle_expected(self, mode_list):
        """
        Update expected numbers to configurate file: conf/$suite_name.cfg
        """
        if load_global_setting(UPDATE_EXPECTED) == "yes":
            for mode in mode_list:
                for frame_size in self.test_parameters.keys():
                    for nb_desc in self.test_parameters[frame_size]:
                        if frame_size == "imix":
                            self.expected_throughput[mode][frame_size][nb_desc] = round(
                                self.throughput[mode][frame_size][nb_desc][1], 3
                            )
                        else:
                            self.expected_throughput[mode][frame_size][nb_desc] = round(
                                self.throughput[mode][frame_size][nb_desc], 3
                            )

    def handle_results(self, mode_list):
        """
        results handled process:
        """
        header = self.table_header
        header.append("nb_desc")
        header.append("Expected Throughput")
        header.append("Throughput Difference")
        for mode in mode_list:
            self.test_result[mode] = dict()
            for frame_size in self.test_parameters.keys():
                ret_datas = {}
                if frame_size == "imix":
                    bps_linerate = self.wirespeed(self.nic, 64, 1) * 8 * (64 + 20)
                    ret_datas = {}
                    for nb_desc in self.test_parameters[frame_size]:
                        ret_data = {}
                        ret_data[header[0]] = frame_size
                        ret_data[header[1]] = mode
                        ret_data[header[2]] = "{:.3f} Mpps".format(
                            self.throughput[mode][frame_size][nb_desc][1]
                        )
                        ret_data[header[3]] = "{:.3f}%".format(
                            self.throughput[mode][frame_size][nb_desc][0]
                            * 100
                            / bps_linerate
                        )
                        ret_data[header[4]] = nb_desc
                        ret_data[header[5]] = "{:.3f} Mpps".format(
                            self.expected_throughput[mode][frame_size][nb_desc]
                        )
                        ret_data[header[6]] = "{:.3f} Mpps".format(
                            self.throughput[mode][frame_size][nb_desc][1]
                            - self.expected_throughput[mode][frame_size][nb_desc]
                        )
                        ret_datas[nb_desc] = deepcopy(ret_data)
                else:
                    wirespeed = self.wirespeed(
                        self.nic, frame_size, self.number_of_ports
                    )
                    for nb_desc in self.test_parameters[frame_size]:
                        ret_data = {}
                        ret_data[header[0]] = frame_size
                        ret_data[header[1]] = mode
                        ret_data[header[2]] = "{:.3f} Mpps".format(
                            self.throughput[mode][frame_size][nb_desc]
                        )
                        ret_data[header[3]] = "{:.3f}%".format(
                            self.throughput[mode][frame_size][nb_desc] * 100 / wirespeed
                        )
                        ret_data[header[4]] = nb_desc
                        ret_data[header[5]] = "{:.3f} Mpps".format(
                            self.expected_throughput[mode][frame_size][nb_desc]
                        )
                        ret_data[header[6]] = "{:.3f} Mpps".format(
                            self.throughput[mode][frame_size][nb_desc]
                            - self.expected_throughput[mode][frame_size][nb_desc]
                        )
                        ret_datas[nb_desc] = deepcopy(ret_data)
                self.test_result[mode][frame_size] = deepcopy(ret_datas)
        self.result_table_create(header)
        for mode in mode_list:
            for frame_size in self.test_parameters.keys():
                for nb_desc in self.test_parameters[frame_size]:
                    table_row = list()
                    for i in range(len(header)):
                        table_row.append(
                            self.test_result[mode][frame_size][nb_desc][header[i]]
                        )
                    self.result_table_add(table_row)
        self.result_table_print()
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
                    row_dict0["performance"] = list()
                    row_dict0["parameters"] = list()
                    row_dict0["parameters"] = list()
                    result_throughput = float(row_in["Mpps"].split()[0])
                    expected_throughput = float(
                        row_in["Expected Throughput"].split()[0]
                    )
                    # delta value and accepted tolerance in percentage
                    delta = result_throughput - expected_throughput
                    gap = expected_throughput * -self.gap * 0.01
                    delta = float(delta)
                    gap = float(gap)
                    self.logger.info("Accept tolerance are (Mpps) %f" % gap)
                    self.logger.info("Throughput Difference are (Mpps) %f" % delta)
                    if result_throughput > expected_throughput + gap:
                        row_dict0["status"] = "PASS"
                    else:
                        row_dict0["status"] = "FAIL"
                    row_dict1 = dict(
                        name="Throughput",
                        value=result_throughput,
                        unit="Mpps",
                        delta=delta,
                    )
                    row_dict2 = dict(
                        name="Txd/Rxd", value=row_in["Mode/RXD-TXD"], unit="descriptor"
                    )
                    row_dict3 = dict(
                        name="frame_size", value=row_in["Frame"], unit="bytes"
                    )
                    row_dict0["performance"].append(row_dict1)
                    row_dict0["parameters"].append(row_dict2)
                    row_dict0["parameters"].append(row_dict3)
                    self.json_obj[case_name].append(row_dict0)
                    status_result.append(row_dict0["status"])
        with open(
            os.path.join(
                rst.path2Result, "{0:s}_{1}.json".format(self.nic, self.suite_name)
            ),
            "w",
        ) as fp:
            json.dump(self.json_obj, fp)
        self.verify("FAIL" not in status_result, "Exceeded Gap")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -I %s" % self.testpmd_name, "#", 20)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)
        self.dut.kill_all()
