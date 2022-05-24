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

SPLIT_RING_PATH = {
    "inorder_mergeable_path": "mrg_rxbuf=1,in_order=1",
    "mergeable_path": "mrg_rxbuf=1,in_order=0",
    "inorder_non_mergeable_path": "mrg_rxbuf=0,in_order=1",
    "non_mergeable_path": "mrg_rxbuf=0,in_order=0",
    "vectorized_path": "mrg_rxbuf=0,in_order=0,vectorized=1",
}

PACKED_RING_PATH = {
    "inorder_mergeable_path": "mrg_rxbuf=1,in_order=1,packed_vq=1",
    "mergeable_path": "mrg_rxbuf=1,in_order=0,packed_vq=1",
    "inorder_non_mergeable_path": "mrg_rxbuf=0,in_order=1,packed_vq=1",
    "non_mergeable_path": "mrg_rxbuf=0,in_order=0,packed_vq=1",
    "vectorized_path": "mrg_rxbuf=0,in_order=0,vectorized=1,packed_vq=1",
    "vectorized_path_not_power_of_2": "mrg_rxbuf=0,in_order=0,vectorized=1,packed_vq=1",
}


class TestVhostCbdma(TestCase):
    def set_up_all(self):
        self.dut_ports = self.dut.get_ports()
        self.number_of_ports = 1
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user_pmd = PmdOutput(self.dut, self.virtio_user)
        self.virtio_mac = "00:01:02:03:04:05"
        self.headers_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"]
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_core_list = self.cores_list[0:9]
        self.virtio_core_list = self.cores_list[9:11]
        self.out_path = "/tmp/%s" % self.suite_name
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        self.pktgen_helper = PacketGeneratorHelper()
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.testpmd_name = self.dut.apps_name["test-pmd"].split("/")[-1]
        self.save_result_flag = True
        self.json_obj = {}

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
        self.dut.send_expect("rm -rf /tmp/s0", "#")
        self.mode_list = []

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num, allow_diff_socket=False):
        """
        get and bind cbdma ports into DPDK driver
        """
        self.all_cbdma_list = []
        self.cbdma_list = []
        self.cbdma_str = ""
        out = self.dut.send_expect(
            "./usertools/dpdk-devbind.py --status-dev dma", "# ", 30
        )
        device_info = out.split("\n")
        for device in device_info:
            pci_info = re.search("\s*(0000:\S*:\d*.\d*)", device)
            if pci_info is not None:
                dev_info = pci_info.group(1)
                # the numa id of ioat dev, only add the device which on same socket with nic dev
                bus = int(dev_info[5:7], base=16)
                if bus >= 128:
                    cur_socket = 1
                else:
                    cur_socket = 0
                if allow_diff_socket:
                    self.all_cbdma_list.append(pci_info.group(1))
                else:
                    if self.ports_socket == cur_socket:
                        self.all_cbdma_list.append(pci_info.group(1))
        self.verify(
            len(self.all_cbdma_list) >= cbdma_num, "There no enough cbdma device"
        )
        self.cbdma_list = self.all_cbdma_list[0:cbdma_num]
        self.cbdma_str = " ".join(self.cbdma_list)
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=%s %s"
            % (self.drivername, self.cbdma_str),
            "# ",
            60,
        )

    @staticmethod
    def generate_dmas_param(queues):
        das_list = []
        for i in range(queues):
            das_list.append("txq{}".format(i))
        das_param = "[{}]".format(";".join(das_list))
        return das_param

    @staticmethod
    def generate_lcore_dma_param(cbdma_list, core_list):
        group_num = int(len(cbdma_list) / len(core_list))
        lcore_dma_list = []
        if len(cbdma_list) == 1:
            for core in core_list:
                lcore_dma_list.append("lcore{}@{}".format(core, cbdma_list[0]))
        elif len(core_list) == 1:
            for cbdma in cbdma_list:
                lcore_dma_list.append("lcore{}@{}".format(core_list[0], cbdma))
        else:
            for cbdma in cbdma_list:
                core_list_index = int(cbdma_list.index(cbdma) / group_num)
                lcore_dma_list.append(
                    "lcore{}@{}".format(core_list[core_list_index], cbdma)
                )
        lcore_dma_param = "[{}]".format(",".join(lcore_dma_list))
        return lcore_dma_param

    def bind_cbdma_device_to_kernel(self):
        self.dut.send_expect("modprobe ioatdma", "# ")
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -u %s" % self.cbdma_str, "# ", 30
        )
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=ioatdma  %s" % self.cbdma_str,
            "# ",
            60,
        )

    def get_vhost_port_num(self):
        out = self.vhost_user.send_expect("show port summary all", "testpmd> ", 60)
        port_num = re.search("Number of available ports:\s*(\d*)", out)
        return int(port_num.group(1))

    def check_each_queue_of_port_packets(self, queues=0):
        """
        check each queue of each port has receive packets
        """
        out = self.vhost_user_pmd.execute_cmd("stop")
        port_num = self.get_vhost_port_num()
        for port in range(port_num):
            for queue in range(queues):
                if queues > 0:
                    reg = "Port= %d/Queue= %d" % (port, queue)
                else:
                    reg = "Forward statistics for port {}".format(port)
                index = out.find(reg)
                rx = re.search("RX-packets:\s*(\d*)", out[index:])
                tx = re.search("TX-packets:\s*(\d*)", out[index:])
                rx_packets = int(rx.group(1))
                tx_packets = int(tx.group(1))
                self.verify(
                    rx_packets > 0 and tx_packets > 0,
                    "The port {}/queue {} rx-packets or tx-packets is 0 about ".format(
                        port, queue
                    )
                    + "rx-packets: {}, tx-packets: {}".format(rx_packets, tx_packets),
                )
        self.vhost_user_pmd.execute_cmd("start")

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def start_vhost_testpmd(
        self, cores="Default", param="", eal_param="", ports="", iova_mode="va"
    ):
        eal_param += " --iova=" + iova_mode
        self.vhost_user_pmd.start_testpmd(
            cores=cores, param=param, eal_param=eal_param, ports=ports, prefix="vhost"
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

    def start_virtio_testpmd(self, cores="Default", param="", eal_param=""):
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        self.virtio_user_pmd.start_testpmd(
            cores=cores, param=param, eal_param=eal_param, no_pci=True, prefix="virtio"
        )
        self.virtio_user_pmd.execute_cmd("set fwd mac")
        self.virtio_user_pmd.execute_cmd("start")
        self.virtio_user_pmd.execute_cmd("show port info all")

    def test_perf_pvp_split_all_path_vhost_txq_1_to_1_cbdma(self):
        """
        Test Case 1: PVP split ring all path vhost enqueue operations with 1 to 1 mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        dmas = self.generate_dmas_param(1)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            "--nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        virtio_param = "--nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=1'".format(
                    self.virtio_mac, path
                )
            )
            if key == "non_mergeable_path":
                new_virtio_param = "--enable-hw-vlan-strip  " + virtio_param
            else:
                new_virtio_param = virtio_param

            self.logger.info("Start virtio-user with {} path with {}".format(key, path))
            mode = key + "_VA"
            self.mode_list.append(mode)
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=new_virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets()

            self.logger.info("Restart vhost with {} path with {}".format(key, path))
            mode += "_RestartVhost"
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets()
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path in SPLIT_RING_PATH.items():
                virtio_eal_param = (
                    "--vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=1'".format(
                        self.virtio_mac, path
                    )
                )
                if key == "non_mergeable_path":
                    new_virtio_param = "--enable-hw-vlan-strip  " + virtio_param
                else:
                    new_virtio_param = virtio_param

                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                mode = key + "_PA"
                self.mode_list.append(mode)
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=new_virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets()

                self.logger.info("Restart vhost with {} path with {}".format(key, path))
                mode += "_RestartVhost"
                self.vhost_user_pmd.execute_cmd("start")
                self.mode_list.append(mode)
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets()
                self.virtio_user_pmd.quit()
        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_all_path_multi_queues_vhost_txq_1_to_1_cbdma(self):
        """
        Test Case 2: PVP split ring all path multi-queues vhost enqueue operations with 1 to 1 mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 8
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        dmas = self.generate_dmas_param(8)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8".format(
                    self.virtio_mac, path
                )
            )
            if key == "non_mergeable_path":
                new_virtio_param = "--enable-hw-vlan-strip  " + virtio_param
            else:
                new_virtio_param = virtio_param

            self.logger.info("Start virtio-user with {} path with {}".format(key, path))
            mode = key + "_VA"
            self.mode_list.append(mode)
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=new_virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)

            self.logger.info("Restart host with {} path with {}".format(key, path))
            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.vhost_user_pmd.execute_cmd("start")
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path in SPLIT_RING_PATH.items():
                if key == "mergeable_path":
                    virtio_eal_param = "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8".format(
                        self.virtio_mac, path
                    )

                    mode = key + "_PA"
                    self.logger.info(
                        "Start virtio-user with {} path with {}".format(key, path)
                    )
                    self.mode_list.append(mode)
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

                    mode += "_RestartVhost"
                    self.logger.info(
                        "Restart host with {} path with {}".format(key, path)
                    )
                    self.mode_list.append(mode)
                    self.vhost_user_pmd.execute_cmd("start")
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)
                    self.virtio_user_pmd.quit()

        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_all_path_multi_queues_vhost_txq_M_2_1_cbdma(self):
        """
        Test Case 3: PVP split ring all path multi-queues vhost enqueue operations with M to 1 mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        dmas = self.generate_dmas_param(8)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8".format(
                    self.virtio_mac, path
                )
            )
            if key == "non_mergeable_path":
                new_virtio_param = "--enable-hw-vlan-strip  " + virtio_param
            else:
                new_virtio_param = virtio_param

            mode = key + "_VA" + "_1_lcore"
            self.mode_list.append(mode)
            self.logger.info("Start virtio-user with {} path with {}".format(key, path))
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=new_virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.logger.info("Restart host with {} path with {}".format(key, path))
            self.vhost_user_pmd.execute_cmd("start")
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)
            self.virtio_user_pmd.quit()

        self.vhost_user_pmd.quit()
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:4]
        )
        vhost_param = (
            " --nb-cores=3 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in SPLIT_RING_PATH.items():
            if key == "inorder_mergeable_path":
                virtio_eal_param = (
                    "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8".format(
                        self.virtio_mac, path
                    )
                )

                mode = key + "_VA" + "_3_lcore"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)
                self.virtio_user_pmd.quit()

        self.vhost_user_pmd.quit()
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:9]
        )
        vhost_param = (
            " --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in SPLIT_RING_PATH.items():
            if key == "mergeable_path":
                virtio_eal_param = (
                    "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8".format(
                        self.virtio_mac, path
                    )
                )
                mode = key + "_VA" + "_8_lcore"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)
                self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path in SPLIT_RING_PATH.items():
                if key == "inorder_non_mergeable_path":
                    virtio_eal_param = "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8".format(
                        self.virtio_mac, path
                    )

                    mode = key + "_PA" + "_8_lcore"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Start virtio-user with {} path with {}".format(key, path)
                    )
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

                    mode += "_RestartVhost"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Restart host with {} path with {}".format(key, path)
                    )
                    self.vhost_user_pmd.execute_cmd("start")
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)
                    self.virtio_user_pmd.quit()

        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_all_path_vhost_txq_1_to_N_cbdma(self):
        """
        Test Case 4: PVP split ring all path vhost enqueue operations with 1 to N mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 8
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        dmas = self.generate_dmas_param(1)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        virtio_param = " --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=1".format(
                    self.virtio_mac, path
                )
            )
            if key == "non_mergeable_path":
                new_virtio_param = "--enable-hw-vlan-strip  " + virtio_param
            else:
                new_virtio_param = virtio_param

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.logger.info("Start virtio-user with {} path with {}".format(key, path))
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=new_virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets()

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.logger.info("Restart host with {} path with {}".format(key, path))
            self.vhost_user_pmd.execute_cmd("start")
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets()
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path in SPLIT_RING_PATH.items():
                if key == "non_mergeable_path":
                    virtio_eal_param = "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=1".format(
                        self.virtio_mac, path
                    )

                    mode = key + "_PA"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Start virtio-user with {} path with {}".format(key, path)
                    )
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets()

                    mode += "_RestartVhost"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Restart host with {} path with {}".format(key, path)
                    )
                    self.vhost_user_pmd.execute_cmd("start")
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets()
                    self.virtio_user_pmd.quit()

        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_all_path_multi_queues_vhost_txq_M_to_N_cbdma(self):
        """
        Test Case 5: PVP split ring all path multi-queues vhost enqueue operations with M to N mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 8
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        dmas = self.generate_dmas_param(3)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        virtio_param = "--nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in SPLIT_RING_PATH.items():
            virtio_eal_param = (
                "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8".format(
                    self.virtio_mac, path
                )
            )
            if key == "non_mergeable_path":
                virtio_param = "--enable-hw-vlan-strip  " + virtio_param

            mode = key + "_VA" + "_3dmas"
            self.mode_list.append(mode)
            self.logger.info("Start virtio-user with {} path with {}".format(key, path))
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.logger.info("Restart host with {} path with {}".format(key, path))
            self.vhost_user_pmd.execute_cmd("start")
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)
            self.virtio_user_pmd.quit()

        self.vhost_user_pmd.quit()
        dmas = self.generate_dmas_param(8)
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in SPLIT_RING_PATH.items():
            if key == "inorder_non_mergeable_path":
                virtio_eal_param = (
                    "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8".format(
                        self.virtio_mac, path
                    )
                )

                mode = key + "_VA" + "_8dmas"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)
                self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path in SPLIT_RING_PATH.items():
                if key == "vectorized_path":
                    virtio_eal_param = "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8".format(
                        self.virtio_mac, path
                    )

                    mode = key + "_PA" + "_8dmas"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Start virtio-user with {} path with {}".format(key, path)
                    )
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

                    mode += "_RestartVhost"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Restart host with {} path with {}".format(key, path)
                    )
                    self.vhost_user_pmd.execute_cmd("start")
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)
                    self.virtio_user_pmd.quit()

        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_dynamic_queues_vhost_txq_M_to_N_cbdma(self):
        """
        Test Case 6: PVP split ring dynamic queue number vhost enqueue operations with M to N mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 8
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=1,client=1'"
        vhost_param = " --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci[0:1],
            iova_mode="va",
        )
        for key, path in SPLIT_RING_PATH.items():
            if key == "inorder_mergeable_path":
                virtio_eal_param = "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8,server=1".format(
                    self.virtio_mac, path
                )

                mode = key + "_VA" + "_without_cbdma"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets()

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets()

        self.vhost_user_pmd.quit()
        dmas = self.generate_dmas_param(4)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list[0:4], core_list=self.vhost_core_list[1:5]
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=/tmp/s0,queues=4,client=1,dmas={}'".format(dmas)
        )
        vhost_param = (
            " --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )

        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci[0:5],
            iova_mode="va",
        )

        for key, path in SPLIT_RING_PATH.items():
            if key == "inorder_mergeable_path":

                mode = key + "_VA" + "_1:1"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=4)

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=4)

        self.vhost_user_pmd.quit()
        dmas = self.generate_dmas_param(queues=8)
        core1 = self.vhost_core_list[1]
        core2 = self.vhost_core_list[2]
        core3 = self.vhost_core_list[3]
        core4 = self.vhost_core_list[4]
        core5 = self.vhost_core_list[5]
        cbdma0 = self.cbdma_list[0]
        cbdma1 = self.cbdma_list[1]
        cbdma2 = self.cbdma_list[2]
        cbdma3 = self.cbdma_list[3]
        cbdma4 = self.cbdma_list[4]
        cbdma5 = self.cbdma_list[5]
        cbdma6 = self.cbdma_list[6]
        cbdma7 = self.cbdma_list[7]
        lcore_dma = (
            f"[lcore{core1}@{cbdma0},lcore{core1}@{cbdma7},"
            + f"lcore{core2}@{cbdma1},lcore{core2}@{cbdma2},lcore{core2}@{cbdma3},"
            + f"lcore{core3}@{cbdma2},lcore{core3}@{cbdma3},lcore{core3}@{cbdma4},"
            f"lcore{core4}@{cbdma2},lcore{core4}@{cbdma3},lcore{core4}@{cbdma4},lcore{core4}@{cbdma5},"
            f"lcore{core5}@{cbdma0},lcore{core5}@{cbdma1},lcore{core5}@{cbdma2},lcore{core5}@{cbdma3},"
            f"lcore{core5}@{cbdma4},lcore{core5}@{cbdma5},lcore{core5}@{cbdma6},lcore{core5}@{cbdma7}]"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas={}'".format(dmas)
        )
        vhost_param = (
            " --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci[0:9],
            iova_mode="va",
        )

        for key, path in SPLIT_RING_PATH.items():
            if key == "inorder_mergeable_path":

                mode = key + "_VA" + "_M<N"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

        self.vhost_user_pmd.quit()
        dmas = self.generate_dmas_param(7)
        lcore_dma = (
            f"[lcore{core1}@{cbdma0},lcore{core2}@{cbdma0},lcore{core3}@{cbdma1},lcore{core3}@{cbdma2},"
            f"lcore{core4}@{cbdma1},lcore{core4}@{cbdma2},lcore{core5}@{cbdma1},lcore{core5}@{cbdma2}]"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas={}'".format(dmas)
        )
        vhost_param = (
            " --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )

        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci[0:5],
            iova_mode="va",
        )

        for key, path in SPLIT_RING_PATH.items():
            if key == "inorder_mergeable_path":

                mode = key + "_VA" + "_M>N"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            dmas = self.generate_dmas_param(queues=8)

            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas={}'".format(
                    dmas
                )
            )
            vhost_param = " --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci[0:5],
                iova_mode="pa",
            )

            for key, path in SPLIT_RING_PATH.items():
                if key == "inorder_mergeable_path":

                    mode = key + "_PA" + "_M>N"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Start virtio-user with {} path with {}".format(key, path)
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

                    mode += "_RestartVhost"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "ReLaunch host with {} path with {}".format(key, path)
                    )
                    self.vhost_user_pmd.execute_cmd("start")
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.virtio_user_pmd.quit()
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_all_path_vhost_txq_1_to_1_cbdma(self):
        """
        Test Case 7: PVP packed ring all path vhost enqueue operations with 1 to 1 mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        dmas = self.generate_dmas_param(1)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                " --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=1'".format(
                    self.virtio_mac, path
                )
            )
            virtio_param = " --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
            if key == "vectorized_path_not_power_of_2":
                virtio_eal_param += ",queue_size=1025"
                virtio_param = " --nb-cores=1 --txq=1 --rxq=1 --txd=1025 --rxd=1025"
            if "vectorized" in key:
                virtio_eal_param += "  --force-max-simd-bitwidth=512"

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.logger.info("Start virtio-user with {} path with {}".format(key, path))
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets()

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.logger.info("Restart host with {} path with {}".format(key, path))
            self.vhost_user_pmd.execute_cmd("start")
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets()
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path in PACKED_RING_PATH.items():
                if key == "inorder_mergeable_path":
                    virtio_eal_param = " --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=1'".format(
                        self.virtio_mac, path
                    )
                    virtio_param = " --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"

                    mode = key + "_PA"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Start virtio-user with {} path with {}".format(key, path)
                    )
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets()

                    mode += "_RestartVhost"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Restart host with {} path with {}".format(key, path)
                    )
                    self.vhost_user_pmd.execute_cmd("start")
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets()
                    self.virtio_user_pmd.quit()

        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_all_path_multi_queues_vhost_txq_1_to_1_cbdma(self):
        """
        Test Case 8: PVP packed ring all path multi-queues vhost enqueue operations with 1 to 1 mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 8
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        dmas = self.generate_dmas_param(8)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                " --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=8'".format(
                    self.virtio_mac, path
                )
            )
            virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
            if key == "vectorized_path_not_power_of_2":
                virtio_eal_param += ",queue_size=1025"
                virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1025 --rxd=1025"
            if "vectorized" in key:
                virtio_eal_param += "  --force-max-simd-bitwidth=512"

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.logger.info("Start virtio-user with {} path with {}".format(key, path))
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.logger.info("Restart host with {} path with {}".format(key, path))
            self.vhost_user_pmd.execute_cmd("start")
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path in PACKED_RING_PATH.items():
                if key == "mergeable_path":
                    virtio_param = (
                        " --nb-cores=1  --txq=8 --rxq=8 --txd=1024 --rxd=1024"
                    )
                    virtio_eal_param = "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8".format(
                        self.virtio_mac, path
                    )

                    mode = key + "_PA"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Start virtio-user with {} path with {}".format(key, path)
                    )
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

                    mode += "_RestartVhost"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Restart host with {} path with {}".format(key, path)
                    )
                    self.vhost_user_pmd.execute_cmd("start")
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)
                    self.virtio_user_pmd.quit()

        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_all_path_multi_queues_vhost_txq_M_to_1_cbdma(self):
        """
        Test Case 9: PVP packed ring all path multi-queues vhost enqueue operations with M to 1 mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        dmas = self.generate_dmas_param(8)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                " --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=8'".format(
                    self.virtio_mac, path
                )
            )
            virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
            if key == "vectorized_path_not_power_of_2":
                virtio_eal_param += ",queue_size=1025"
                virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1025 --rxd=1025"

            mode = key + "_VA" + "_1_lcore"
            self.mode_list.append(mode)
            self.logger.info("Start virtio-user with {} path with {}".format(key, path))
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.logger.info("Restart host with {} path with {}".format(key, path))
            self.vhost_user_pmd.execute_cmd("start")
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets(queues=8)
            self.virtio_user_pmd.quit()

        self.vhost_user_pmd.quit()
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:4]
        )
        vhost_param = (
            " --nb-cores=3 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            if key == "inorder_mergeable_path":
                virtio_eal_param = (
                    " --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=8'".format(
                        self.virtio_mac, path
                    )
                )
                virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"

                mode = key + "_VA" + "_3_lcore"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)
                self.virtio_user_pmd.quit()

        self.vhost_user_pmd.quit()
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:9]
        )
        vhost_param = (
            " --nb-cores=8 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            if key == "mergeable_path":
                virtio_eal_param = (
                    " --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=8'".format(
                        self.virtio_mac, path
                    )
                )
                virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"

                mode = key + "_VA" + "_8_lcore"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)
                self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path in PACKED_RING_PATH.items():
                if key == "inorder_non_mergeable_path":
                    virtio_eal_param = " --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=8'".format(
                        self.virtio_mac, path
                    )
                    virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"

                    mode = key + "_PA" + "_8_lcore"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Start virtio-user with {} path with {}".format(key, path)
                    )
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

                    mode += "_RestartVhost"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Restart host with {} path with {}".format(key, path)
                    )
                    self.vhost_user_pmd.execute_cmd("start")
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)
                    self.virtio_user_pmd.quit()

        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_all_path_vhost_txq_1_to_N_cbdma(self):
        """
        Test Case 10: PVP packed ring all path vhost enqueue operations with 1 to N mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 8
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        dmas = self.generate_dmas_param(1)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txq=1 --rxq=1--txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                " --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=1'".format(
                    self.virtio_mac, path
                )
            )
            virtio_param = " --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
            if key == "vectorized_path_not_power_of_2":
                virtio_eal_param += ",queue_size=1025"
                virtio_param = " --nb-cores=1 --txq=1 --rxq=1 --txd=1025 --rxd=1025"

            mode = key + "_VA"
            self.mode_list.append(mode)
            self.logger.info("Start virtio-user with {} path with {}".format(key, path))
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets()

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.logger.info("Restart host with {} path with {}".format(key, path))
            self.vhost_user_pmd.execute_cmd("start")
            self.send_imix_packets(mode=mode)
            self.check_each_queue_of_port_packets()
            self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path in PACKED_RING_PATH.items():
                if key == "non_mergeable_path":
                    virtio_eal_param = " --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=1'".format(
                        self.virtio_mac, path
                    )
                    virtio_param = " --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"

                    mode = key + "_PA"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Start virtio-user with {} path with {}".format(key, path)
                    )
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets()

                    mode += "_RestartVhost"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Restart host with {} path with {}".format(key, path)
                    )
                    self.vhost_user_pmd.execute_cmd("start")
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets()
                    self.virtio_user_pmd.quit()

        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_all_path_multi_queues_vhost_txq_M_to_N_cbdma(self):
        """
        Test Case 11: PVP packed ring all path vhost enqueue operations with M to N mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 8
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        dmas = self.generate_dmas_param(3)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            virtio_eal_param = (
                " --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=8'".format(
                    self.virtio_mac, path
                )
            )
            virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
            if key == "vectorized_path_not_power_of_2":
                virtio_eal_param += ",queue_size=1025"
                virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1025 --rxd=1025"

            mode = key + "_VA" + "_3dmas"
            self.mode_list.append(mode)
            self.start_virtio_testpmd(
                cores=self.virtio_core_list,
                param=virtio_param,
                eal_param=virtio_eal_param,
            )
            self.send_imix_packets(mode=mode)
            self.logger.info("Start virtio-user with {} path with {}".format(key, path))
            self.check_each_queue_of_port_packets(queues=8)

            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.vhost_user_pmd.execute_cmd("start")
            self.send_imix_packets(mode=mode)
            self.logger.info("Restart host with {} path with {}".format(key, path))
            self.check_each_queue_of_port_packets(queues=8)
            self.virtio_user_pmd.quit()

        self.vhost_user_pmd.quit()
        dmas = self.generate_dmas_param(queues=8)
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            if key == "inorder_non_mergeable_path":
                virtio_eal_param = (
                    " --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=8'".format(
                        self.virtio_mac, path
                    )
                )
                virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"

                mode = key + "_VA" + "_8dmas"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)
                self.virtio_user_pmd.quit()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path in PACKED_RING_PATH.items():
                if key == "vectorized_path":
                    virtio_eal_param = " --force-max-simd-bitwidth=512 --vdev 'net_virtio_user0,mac={},path=/tmp/s0,{},queues=8'".format(
                        self.virtio_mac, path
                    )
                    virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"

                    mode = key + "_PA" + "_8dmas"
                    self.mode_list.append(mode)
                    self.start_virtio_testpmd(
                        cores=self.virtio_core_list,
                        param=virtio_param,
                        eal_param=virtio_eal_param,
                    )
                    self.send_imix_packets(mode=mode)
                    self.logger.info(
                        "Start virtio-user with {} path with {}".format(key, path)
                    )
                    self.check_each_queue_of_port_packets(queues=8)

                    mode += "_RestartVhost"
                    self.mode_list.append(mode)
                    self.vhost_user_pmd.execute_cmd("start")
                    self.send_imix_packets(mode=mode)
                    self.logger.info(
                        "Restart host with {} path with {}".format(key, path)
                    )
                    self.check_each_queue_of_port_packets(queues=8)
                    self.virtio_user_pmd.quit()

        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()

    def test_perf_pvp_packed_dynamic_queues_vhost_txq_M_to_N_cbdma(self):
        """
        Test Case 12: PVP packed ring dynamic queue number vhost enqueue operations with M to N mapping between vrings and CBDMA virtual channels
        """
        cbdma_num = 8
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num)
        vhost_eal_param = "--vdev 'net_vhost0,iface=/tmp/s0,queues=1,client=1'"
        vhost_param = " --nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        virtio_param = " --nb-cores=1 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for i in range(cbdma_num):
            allow_pci.append(self.cbdma_list[i])
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci[0:1],
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            if key == "inorder_mergeable_path":
                virtio_eal_param = "--vdev=net_virtio_user0,mac={},path=/tmp/s0,{},queues=8,server=1".format(
                    self.virtio_mac, path
                )

                mode = key + "_VA" + "_without_cbdma"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.start_virtio_testpmd(
                    cores=self.virtio_core_list,
                    param=virtio_param,
                    eal_param=virtio_eal_param,
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets()

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets()

        self.vhost_user_pmd.quit()
        dmas = self.generate_dmas_param(4)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list[0:4], core_list=self.vhost_core_list[1:5]
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=/tmp/s0,queues=4,client=1,dmas={}'".format(dmas)
        )
        vhost_param = (
            " --nb-cores=4 --txq=4 --rxq=4 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )

        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci[0:5],
            iova_mode="va",
        )
        for key, path in PACKED_RING_PATH.items():
            if key == "inorder_mergeable_path":

                mode = key + "_VA" + "_1:1"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=4)

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=4)

        self.vhost_user_pmd.quit()
        dmas = self.generate_dmas_param(8)
        core1 = self.vhost_core_list[1]
        core2 = self.vhost_core_list[2]
        core3 = self.vhost_core_list[3]
        core4 = self.vhost_core_list[4]
        core5 = self.vhost_core_list[5]
        cbdma0 = self.cbdma_list[0]
        cbdma1 = self.cbdma_list[1]
        cbdma2 = self.cbdma_list[2]
        cbdma3 = self.cbdma_list[3]
        cbdma4 = self.cbdma_list[4]
        cbdma5 = self.cbdma_list[5]
        cbdma6 = self.cbdma_list[6]
        cbdma7 = self.cbdma_list[7]
        lcore_dma = (
            f"[lcore{core1}@{cbdma0},lcore{core1}@{cbdma7},"
            + f"lcore{core2}@{cbdma1},lcore{core2}@{cbdma2},lcore{core2}@{cbdma3},"
            + f"lcore{core3}@{cbdma2},lcore{core3}@{cbdma3},lcore{core3}@{cbdma4},"
            f"lcore{core4}@{cbdma2},lcore{core4}@{cbdma3},lcore{core4}@{cbdma4},lcore{core4}@{cbdma5},"
            f"lcore{core5}@{cbdma0},lcore{core5}@{cbdma1},lcore{core5}@{cbdma2},lcore{core5}@{cbdma3},"
            f"lcore{core5}@{cbdma4},lcore{core5}@{cbdma5},lcore{core5}@{cbdma6},lcore{core5}@{cbdma7}]"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas={}'".format(dmas)
        )
        vhost_param = (
            " --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci[0:9],
            iova_mode="va",
        )

        for key, path in PACKED_RING_PATH.items():
            if key == "inorder_mergeable_path":

                mode = key + "_VA" + "_M<N"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

        self.vhost_user_pmd.quit()
        dmas = self.generate_dmas_param(7)
        lcore_dma = (
            f"[lcore{core1}@{cbdma0},lcore{core2}@{cbdma0},lcore{core3}@{cbdma1},lcore{core3}@{cbdma2},"
            f"lcore{core4}@{cbdma1},lcore{core4}@{cbdma2},lcore{core5}@{cbdma1},lcore{core5}@{cbdma2}]"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas={}'".format(dmas)
        )
        vhost_param = (
            " --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
        )

        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            param=vhost_param,
            eal_param=vhost_eal_param,
            ports=allow_pci[0:5],
            iova_mode="va",
        )

        for key, path in PACKED_RING_PATH.items():
            if key == "inorder_mergeable_path":

                mode = key + "_VA" + "_M>N"
                self.mode_list.append(mode)
                self.logger.info(
                    "Start virtio-user with {} path with {}".format(key, path)
                )
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.logger.info("Restart host with {} path with {}".format(key, path))
                self.vhost_user_pmd.execute_cmd("start")
                self.send_imix_packets(mode=mode)
                self.check_each_queue_of_port_packets(queues=8)

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            dmas = self.generate_dmas_param(8)
            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=/tmp/s0,queues=8,client=1,dmas={}'".format(
                    dmas
                )
            )
            vhost_param = " --nb-cores=5 --txq=8 --rxq=8 --txd=1024 --rxd=1024 --lcore-dma={}".format(
                lcore_dma
            )
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                param=vhost_param,
                eal_param=vhost_eal_param,
                ports=allow_pci[0:5],
                iova_mode="pa",
            )

            for key, path in PACKED_RING_PATH.items():
                if key == "inorder_mergeable_path":

                    mode = key + "_PA" + "_M>N"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Start virtio-user with {} path with {}".format(key, path)
                    )
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

                    mode += "_RestartVhost"
                    self.mode_list.append(mode)
                    self.logger.info(
                        "Restart host with {} path with {}".format(key, path)
                    )
                    self.vhost_user_pmd.execute_cmd("start")
                    self.send_imix_packets(mode=mode)
                    self.check_each_queue_of_port_packets(queues=8)

        self.result_table_print()
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)
        self.vhost_user_pmd.quit()
        self.virtio_user_pmd.quit()

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
            pkt.assign_layers(["ether", "ipv4", "raw"])
            pkt.config_layers(
                [
                    ("ether", {"dst": "%s" % self.virtio_mac}),
                    ("ipv4", {"src": "1.1.1.1"}),
                    ("raw", {"payload": ["01"] * int("%d" % payload_size)}),
                ]
            )
            pkt.save_pcapfile(
                self.tester,
                "%s/multiqueuerandomip_%s.pcap" % (self.out_path, frame_size),
            )
            tgenInput.append(
                (
                    port,
                    port,
                    "%s/multiqueuerandomip_%s.pcap" % (self.out_path, frame_size),
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
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)
        self.dut.kill_all()
