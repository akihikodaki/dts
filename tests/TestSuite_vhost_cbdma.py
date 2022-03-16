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
 $ ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c f -n 4 \
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
        self.dut_ports = self.dut.get_ports()
        self.number_of_ports = 1
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.virtio_user1 = self.dut.new_session(suite="virtio-user1")
        self.pmdout_vhost_user = PmdOutput(self.dut, self.vhost_user)
        self.pmdout_virtio_user = PmdOutput(self.dut, self.virtio_user)
        self.virtio_mac = "00:01:02:03:04:05"
        self.headers_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"]
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("all", socket=self.socket)
        self.cbdma_dev_infos = []
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
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
        self.table_header = ["Frame"]
        self.table_header.append("Mode/RXD-TXD")
        self.used_cbdma = []
        self.table_header.append("Mpps")
        self.table_header.append("% linerate")
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

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num):
        """
        get all cbdma ports
        """
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
                if self.ports_socket == cur_socket:
                    self.cbdma_dev_infos.append(pci_info.group(1))
        self.verify(
            len(self.cbdma_dev_infos) >= cbdma_num,
            "There no enough cbdma device to run this suite",
        )
        self.used_cbdma = self.cbdma_dev_infos[0:cbdma_num]
        self.device_str = " ".join(self.used_cbdma)
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=%s %s"
            % (self.drivername, self.device_str),
            "# ",
            60,
        )

    def bind_cbdma_device_to_kernel(self):
        if self.device_str is not None:
            self.dut.send_expect("modprobe ioatdma", "# ")
            self.dut.send_expect(
                "./usertools/dpdk-devbind.py -u %s" % self.device_str, "# ", 30
            )
            self.dut.send_expect(
                "./usertools/dpdk-devbind.py --force --bind=ioatdma  %s"
                % self.device_str,
                "# ",
                60,
            )

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
            self.verify(
                rx_packets > 0 and tx_packets > 0,
                "The queue %d rx-packets or tx-packets is 0 about " % queue_index
                + "rx-packets:%d, tx-packets:%d" % (rx_packets, tx_packets),
            )
        self.vhost_user.send_expect("clear port stats all", "testpmd> ", 30)
        self.vhost_user.send_expect("start", "testpmd> ", 30)

    def check_port_stats_result(self, session):
        out = session.send_expect("show port stats all", "testpmd> ", 30)
        self.result_first = re.findall(r"RX-packets: (\w+)", out)
        self.result_secondary = re.findall(r"TX-packets: (\w+)", out)
        self.verify(
            int(self.result_first[0]) > 1 and int(self.result_secondary[0]) > 1,
            "forward packets no correctly",
        )

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def launch_testpmd_as_vhost_user(
        self,
        command,
        cores="Default",
        dev="",
        ports="",
        iova_mode="pa",
        set_pmd_param=True,
    ):
        if iova_mode:
            iova_parm = "--iova=" + iova_mode
        else:
            iova_parm = ""
        self.pmdout_vhost_user.start_testpmd(
            cores=cores,
            param=command,
            vdevs=[dev],
            ports=ports,
            prefix="vhost",
            eal_param=iova_parm,
        )
        if set_pmd_param:
            self.vhost_user.send_expect("set fwd mac", "testpmd> ", 30)
            self.vhost_user.send_expect("start", "testpmd> ", 30)

    def launch_testpmd_as_virtio_user(
        self, command, cores="Default", dev="", set_pmd_param=True, eal_param=""
    ):
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        self.pmdout_virtio_user.start_testpmd(
            cores,
            command,
            vdevs=[dev],
            no_pci=True,
            prefix="virtio",
            eal_param=eal_param,
        )
        if set_pmd_param:
            self.virtio_user.send_expect("set fwd mac", "testpmd> ", 30)
            self.virtio_user.send_expect("start", "testpmd> ", 30)
            self.virtio_user.send_expect("show port info all", "testpmd> ", 30)

    def diff_param_launch_send_and_verify(
        self, mode, params, dev, cores, eal_param="", is_quit=True, launch_virtio=True
    ):
        if launch_virtio:
            self.launch_testpmd_as_virtio_user(
                params, cores, dev=dev, eal_param=eal_param
            )
        self.send_and_verify(mode)
        if is_quit:
            self.virtio_user.send_expect("quit", "# ")
            time.sleep(3)

    def test_perf_pvp_spilt_ring_all_path_vhost_enqueue_operations_with_cbdma(self):
        """
        Test Case 1: PVP split ring all path vhost enqueue operations with cbdma
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        txd_rxd = 1024
        vhost_param = " --nb-cores=%d --txd=%d --rxd=%d"
        nb_cores = 1
        queues = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(1)
        vhost_vdevs = (
            f"'net_vhost0,iface=/tmp/s0,queues=%d,dmas=[txq0@{self.device_str}]'"
        )
        virtio_path_dict = {
            "inorder_mergeable_path": "mrg_rxbuf=1,in_order=1",
            "mergeable_path": "mrg_rxbuf=1,in_order=0",
            "inorder_non_mergeable_path": "mrg_rxbuf=0,in_order=1",
            "non_mergeable_path": "mrg_rxbuf=0,in_order=0",
            "vector_rx_path": "mrg_rxbuf=0,in_order=0,vectorized=1",
        }
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for index in range(1):
            allow_pci.append(self.cbdma_dev_infos[index])
        self.launch_testpmd_as_vhost_user(
            vhost_param % (nb_cores, txd_rxd, txd_rxd),
            self.cores[0:2],
            dev=vhost_vdevs % (nb_cores),
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path_mode in virtio_path_dict.items():
            if key == "non_mergeable_path":
                virtio_param = (
                    " --enable-hw-vlan-strip --nb-cores=%d --txd=%d --rxd=%d"
                    % (nb_cores, txd_rxd, txd_rxd)
                )
            else:
                virtio_param = " --nb-cores=%d --txd=%d --rxd=%d" % (
                    nb_cores,
                    txd_rxd,
                    txd_rxd,
                )
            vdevs = (
                f"'net_virtio_user0,mac={self.virtio_mac},path=/tmp/s0,{path_mode},queues=%d'"
                % nb_cores
            )
            mode = key + "_VA"
            self.mode_list.append(mode)
            self.diff_param_launch_send_and_verify(
                mode,
                virtio_param,
                vdevs,
                self.cores[2:4],
                is_quit=False,
                launch_virtio=True,
            )
            self.vhost_user.send_expect("show port stats all", "testpmd> ", 10)
            self.vhost_user.send_expect("stop", "testpmd> ", 10)
            self.vhost_user.send_expect("start", "testpmd> ", 10)
            self.vhost_user.send_expect("show port info all", "testpmd> ", 30)
            self.vhost_user.send_expect("show port stats all", "testpmd> ", 10)
            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.diff_param_launch_send_and_verify(
                mode,
                virtio_param,
                vdevs,
                self.cores[2:4],
                is_quit=True,
                launch_virtio=False,
            )

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost testpmd with PA mode")
            self.vhost_user.send_expect("quit", "# ")
            self.launch_testpmd_as_vhost_user(
                vhost_param % (nb_cores, txd_rxd, txd_rxd),
                self.cores[0:2],
                dev=vhost_vdevs % (nb_cores),
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path_mode in virtio_path_dict.items():
                if key == "non_mergeable_path":
                    virtio_param = (
                        " --enable-hw-vlan-strip --nb-cores=%d --txd=%d --rxd=%d"
                        % (nb_cores, txd_rxd, txd_rxd)
                    )
                else:
                    virtio_param = " --nb-cores=%d --txd=%d --rxd=%d" % (
                        nb_cores,
                        txd_rxd,
                        txd_rxd,
                    )
                vdevs = (
                    f"'net_virtio_user0,mac={self.virtio_mac},path=/tmp/s0,{path_mode},queues=%d'"
                    % queues
                )
                mode = key + "_PA"
                self.mode_list.append(mode)
                self.diff_param_launch_send_and_verify(
                    mode,
                    virtio_param,
                    vdevs,
                    self.cores[2:4],
                    is_quit=False,
                    launch_virtio=True,
                )
                self.vhost_user.send_expect("show port stats all", "testpmd> ", 10)
                self.vhost_user.send_expect("stop", "testpmd> ", 10)
                self.vhost_user.send_expect("start", "testpmd> ", 10)
                self.vhost_user.send_expect("show port info all", "testpmd> ", 30)
                self.vhost_user.send_expect("show port stats all", "testpmd> ", 10)
                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.diff_param_launch_send_and_verify(
                    mode,
                    virtio_param,
                    vdevs,
                    self.cores[2:4],
                    is_quit=True,
                    launch_virtio=False,
                )
        self.result_table_print()
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)

    def test_perf_pvp_spilt_ring_all_dynamic_queue_number_vhost_enqueue_operations_with_cbdma(
        self,
    ):
        """
        Test Case2: PVP split ring dynamic queue number vhost enqueue operations with cbdma
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        nb_cores = 1
        txd_rxd = 1024
        queues = 8
        virtio_path = "/tmp/s0"
        path_mode = "mrg_rxbuf=1,in_order=1"
        self.get_cbdma_ports_info_and_bind_to_dpdk(8)
        vhost_param = " --nb-cores=%d --txd=%d --rxd=%d --txq=%d --rxq=%d "
        virtio_param = " --nb-cores=%d --txd=%d --rxd=%d --txq=%d --rxq=%d "
        vhost_dev = f"'net_vhost0,iface={virtio_path},queues=%d,client=1,%s'"
        virtio_dev = f"net_virtio_user0,mac={self.virtio_mac},path={virtio_path},{path_mode},queues={queues},server=1"
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for index in range(8):
            allow_pci.append(self.cbdma_dev_infos[index])
        self.launch_testpmd_as_vhost_user(
            vhost_param % (nb_cores, txd_rxd, txd_rxd, queues, queues),
            self.cores[0:2],
            dev=vhost_dev % (queues, ""),
            ports=[allow_pci[0]],
            iova_mode="va",
        )
        self.mode_list.append("with_0_cbdma")
        self.launch_testpmd_as_virtio_user(
            virtio_param % (nb_cores, txd_rxd, txd_rxd, queues, queues),
            self.cores[2:4],
            dev=virtio_dev,
        )
        self.send_and_verify("with_0_cbdma", queue_list=range(queues))

        self.vhost_user.send_expect("quit", "#")
        vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]};txq2@{self.used_cbdma[2]};txq3@{self.used_cbdma[3]}]"
        self.launch_testpmd_as_vhost_user(
            vhost_param % (nb_cores, txd_rxd, txd_rxd, queues, queues),
            self.cores[0:2],
            dev=vhost_dev % (queues, vhost_dmas),
            ports=allow_pci[:5],
            iova_mode="va",
        )
        self.mode_list.append("with_4_cbdma")
        self.send_and_verify("with_4_cbdma", queue_list=range(int(queues / 2)))

        self.vhost_user.send_expect("quit", "#")
        vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]};txq2@{self.used_cbdma[2]};txq3@{self.used_cbdma[3]};txq4@{self.used_cbdma[4]};txq5@{self.used_cbdma[5]};txq6@{self.used_cbdma[6]};txq7@{self.used_cbdma[7]}]"
        self.launch_testpmd_as_vhost_user(
            vhost_param % (nb_cores, txd_rxd, txd_rxd, queues, queues),
            self.cores[0:2],
            dev=vhost_dev % (queues, vhost_dmas),
            ports=allow_pci,
            iova_mode="va",
        )
        self.mode_list.append("with_8_cbdma")
        self.send_and_verify("with_8_cbdma", queue_list=range(queues))

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost testpmd with PA mode")
            self.vhost_user.send_expect("quit", "#")
            vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]};txq2@{self.used_cbdma[2]};txq3@{self.used_cbdma[3]};txq4@{self.used_cbdma[4]};txq5@{self.used_cbdma[5]}]"
            self.launch_testpmd_as_vhost_user(
                vhost_param % (nb_cores, txd_rxd, txd_rxd, queues, queues),
                self.cores[0:2],
                dev=vhost_dev % (queues, vhost_dmas),
                ports=allow_pci,
                iova_mode="pa",
            )
            self.mode_list.append("with_6_cbdma")
            self.send_and_verify("with_6_cbdma", queue_list=range(queues))

        self.virtio_user.send_expect("quit", "# ")
        self.vhost_user.send_expect("quit", "# ")
        self.result_table_print()
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)

    def test_perf_pvp_packed_ring_all_path_vhost_enqueue_operations_with_cbdma(self):
        """
        Test Case 3: PVP packed ring all path vhost enqueue operations with cbdma
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        txd_rxd = 1024
        vhost_param = " --nb-cores=%d --txd=%d --rxd=%d"
        nb_cores = 1
        queues = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(1)
        vhost_vdevs = (
            f"'net_vhost0,iface=/tmp/s0,queues=%d,dmas=[txq0@{self.device_str}]'"
        )
        virtio_path_dict = {
            "inorder_mergeable_path": "mrg_rxbuf=1,in_order=1,packed_vq=1",
            "mergeable_path": "mrg_rxbuf=1,in_order=0,packed_vq=1",
            "inorder_non_mergeable_path": "mrg_rxbuf=0,in_order=1,packed_vq=1",
            "non_mergeable_path": "mrg_rxbuf=0,in_order=0,packed_vq=1",
            "vector_rx_path": "mrg_rxbuf=0,in_order=1,vectorized=1,packed_vq=1",
            "vector_rx_path_not_power_of_2": "mrg_rxbuf=0,in_order=1,vectorized=1,packed_vq=1,queue_size=1025",
        }
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for index in range(1):
            allow_pci.append(self.cbdma_dev_infos[index])
        self.launch_testpmd_as_vhost_user(
            vhost_param % (nb_cores, txd_rxd, txd_rxd),
            self.cores[0:2],
            dev=vhost_vdevs % (nb_cores),
            ports=allow_pci,
            iova_mode="va",
        )
        for key, path_mode in virtio_path_dict.items():
            if key == "vector_rx_path_not_power_of_2":
                virtio_param = " --nb-cores=%d --txd=%d --rxd=%d" % (
                    nb_cores,
                    (txd_rxd + 1),
                    (txd_rxd + 1),
                )
            else:
                virtio_param = " --nb-cores=%d --txd=%d --rxd=%d" % (
                    nb_cores,
                    txd_rxd,
                    txd_rxd,
                )
            if "vector_rx_path" in key:
                eal_param = "--force-max-simd-bitwidth=512"
            else:
                eal_param = ""
            vdevs = (
                f"'net_virtio_user0,mac={self.virtio_mac},path=/tmp/s0,{path_mode},queues=%d'"
                % queues
            )
            mode = key + "_VA"
            self.mode_list.append(mode)
            self.diff_param_launch_send_and_verify(
                mode,
                virtio_param,
                vdevs,
                self.cores[2:4],
                eal_param=eal_param,
                is_quit=False,
                launch_virtio=True,
            )
            self.vhost_user.send_expect("show port stats all", "testpmd> ", 10)
            self.vhost_user.send_expect("stop", "testpmd> ", 10)
            self.vhost_user.send_expect("start", "testpmd> ", 10)
            self.vhost_user.send_expect("show port info all", "testpmd> ", 30)
            self.vhost_user.send_expect("show port stats all", "testpmd> ", 10)
            mode += "_RestartVhost"
            self.mode_list.append(mode)
            self.diff_param_launch_send_and_verify(
                mode,
                virtio_param,
                vdevs,
                self.cores[2:4],
                is_quit=True,
                launch_virtio=False,
            )
        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost testpmd with PA mode")
            self.vhost_user.send_expect("quit", "# ")
            self.launch_testpmd_as_vhost_user(
                vhost_param % (queues, txd_rxd, txd_rxd),
                self.cores[0:2],
                dev=vhost_vdevs % (queues),
                ports=allow_pci,
                iova_mode="pa",
            )
            for key, path_mode in virtio_path_dict.items():
                if key == "vector_rx_path_not_power_of_2":
                    virtio_param = " --nb-cores=%d --txd=%d --rxd=%d" % (
                        nb_cores,
                        (txd_rxd + 1),
                        (txd_rxd + 1),
                    )
                else:
                    virtio_param = " --nb-cores=%d --txd=%d --rxd=%d" % (
                        nb_cores,
                        txd_rxd,
                        txd_rxd,
                    )
                if "vector_rx_path" in key:
                    eal_param = "--force-max-simd-bitwidth=512"
                else:
                    eal_param = ""
                vdevs = (
                    f"'net_virtio_user0,mac={self.virtio_mac},path=/tmp/s0,{path_mode},queues=%d'"
                    % queues
                )
                mode = key + "_PA"
                self.mode_list.append(mode)
                self.diff_param_launch_send_and_verify(
                    mode,
                    virtio_param,
                    vdevs,
                    self.cores[2:4],
                    eal_param=eal_param,
                    is_quit=False,
                    launch_virtio=True,
                )

                self.vhost_user.send_expect("show port stats all", "testpmd> ", 10)
                self.vhost_user.send_expect("stop", "testpmd> ", 10)
                self.vhost_user.send_expect("start", "testpmd> ", 10)
                self.vhost_user.send_expect("show port info all", "testpmd> ", 30)
                self.vhost_user.send_expect("show port stats all", "testpmd> ", 10)
                mode += "_RestartVhost"
                self.mode_list.append(mode)
                self.diff_param_launch_send_and_verify(
                    mode,
                    virtio_param,
                    vdevs,
                    self.cores[2:4],
                    is_quit=True,
                    launch_virtio=False,
                )

        self.result_table_print()
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)

    def test_perf_pvp_packed_ring_all_dynamic_queue_number_vhost_enqueue_operations_with_cbdma(
        self,
    ):
        """
        Test Case 4: PVP packed ring dynamic queue number vhost enqueue operations with cbdma
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        nb_cores = 1
        txd_rxd = 1024
        queues = 8
        virtio_path = "/tmp/s0"
        path_mode = "mrg_rxbuf=1,in_order=1,packed_vq=1"
        self.get_cbdma_ports_info_and_bind_to_dpdk(8)
        vhost_param = " --nb-cores=%d --txd=%d --rxd=%d --txq=%d --rxq=%d "
        virtio_param = " --nb-cores=%d --txd=%d --rxd=%d --txq=%d --rxq=%d "
        vhost_dev = f"'net_vhost0,iface={virtio_path},queues=%d,client=1,%s'"
        virtio_dev = f"net_virtio_user0,mac={self.virtio_mac},path={virtio_path},{path_mode},queues={queues},server=1"
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for index in range(8):
            allow_pci.append(self.cbdma_dev_infos[index])
        self.launch_testpmd_as_vhost_user(
            vhost_param % (nb_cores, txd_rxd, txd_rxd, queues, queues),
            self.cores[0:2],
            dev=vhost_dev % (queues, ""),
            ports=[allow_pci[0]],
            iova_mode="va",
        )
        self.mode_list.append("with_0_cbdma")
        self.launch_testpmd_as_virtio_user(
            virtio_param % (nb_cores, txd_rxd, txd_rxd, queues, queues),
            self.cores[2:4],
            dev=virtio_dev,
        )
        self.send_and_verify("with_0_cbdma", queue_list=range(queues))

        self.vhost_user.send_expect("quit", "#")
        vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]};txq2@{self.used_cbdma[2]};txq3@{self.used_cbdma[3]}]"
        self.launch_testpmd_as_vhost_user(
            vhost_param % (nb_cores, txd_rxd, txd_rxd, queues, queues),
            self.cores[0:2],
            dev=vhost_dev % (queues, vhost_dmas),
            ports=allow_pci[:5],
            iova_mode="va",
        )
        self.mode_list.append("with_4_cbdma")
        self.send_and_verify("with_4_cbdma", queue_list=range(int(queues / 2)))

        self.vhost_user.send_expect("quit", "#")
        vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]};txq2@{self.used_cbdma[2]};txq3@{self.used_cbdma[3]};txq4@{self.used_cbdma[4]};txq5@{self.used_cbdma[5]};txq6@{self.used_cbdma[6]};txq7@{self.used_cbdma[7]}]"
        self.launch_testpmd_as_vhost_user(
            vhost_param % (nb_cores, txd_rxd, txd_rxd, queues, queues),
            self.cores[0:2],
            dev=vhost_dev % (queues, vhost_dmas),
            ports=allow_pci,
            iova_mode="va",
        )
        self.mode_list.append("with_8_cbdma")
        self.send_and_verify("with_8_cbdma", queue_list=range(queues))

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost testpmd with PA mode")
            self.vhost_user.send_expect("quit", "#")
            vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]};txq2@{self.used_cbdma[2]};txq3@{self.used_cbdma[3]};txq4@{self.used_cbdma[4]};txq5@{self.used_cbdma[5]}]"
            self.launch_testpmd_as_vhost_user(
                vhost_param % (nb_cores, txd_rxd, txd_rxd, queues, queues),
                self.cores[0:2],
                dev=vhost_dev % (queues, vhost_dmas),
                ports=allow_pci,
                iova_mode="pa",
            )
            self.mode_list.append("with_6_cbdma")
            self.send_and_verify("with_6_cbdma", queue_list=range(queues))

        self.virtio_user.send_expect("quit", "# ")
        self.vhost_user.send_expect("quit", "# ")
        self.result_table_print()
        self.handle_expected(mode_list=self.mode_list)
        self.handle_results(mode_list=self.mode_list)

    def send_chain_packets_and_verify(self):
        self.pmdout_virtio_user.execute_cmd("clear port stats all")
        self.pmdout_virtio_user.execute_cmd("start")
        self.pmdout_vhost_user.execute_cmd("vhost enable tx all")
        self.pmdout_vhost_user.execute_cmd("set txpkts 65535,65535,65535,65535,65535")
        self.pmdout_vhost_user.execute_cmd("start tx_first 32")
        self.pmdout_vhost_user.execute_cmd("show port stats all")
        out = self.pmdout_virtio_user.execute_cmd("show port stats all")
        rx_pkts = int(re.search("RX-packets: (\d+)", out).group(1))
        self.verify(rx_pkts > 0, "virtio-user can not received packets")

    def test_loopback_split_ring_large_chain_packets_stress_test_with_cbdma_enqueue(
        self,
    ):
        """
        Test Case5: loopback split ring large chain packets stress test with cbdma enqueue
        """
        nb_cores = 1
        queues = 1
        txd_rxd = 2048
        txq_rxq = 1
        virtio_path = "/tmp/s0"
        path_mode = "mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048"
        self.get_cbdma_ports_info_and_bind_to_dpdk(1)
        vhost_param = " --nb-cores=%d --mbuf-size=65535"
        virtio_param = " --nb-cores=%d --txd=%d --rxd=%d --txq=%d --rxq=%d "
        virtio_dev = f"net_virtio_user0,mac={self.virtio_mac},path={virtio_path},{path_mode},queues=%d"
        vhost_vdevs = (
            f"'net_vhost0,iface=/tmp/s0,queues=%d,dmas=[txq0@{self.device_str}]'"
        )
        allow_pci = []
        for index in range(1):
            allow_pci.append(self.cbdma_dev_infos[index])
        self.launch_testpmd_as_vhost_user(
            vhost_param % (nb_cores),
            self.cores[0:2],
            dev=vhost_vdevs % (queues),
            ports=allow_pci,
            iova_mode="va",
            set_pmd_param=False,
        )
        self.launch_testpmd_as_virtio_user(
            virtio_param % (nb_cores, txd_rxd, txd_rxd, txq_rxq, txq_rxq),
            self.cores[2:4],
            dev=virtio_dev % (queues),
            set_pmd_param=False,
        )
        self.send_chain_packets_and_verify()

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost testpmd with PA mode")
            self.pmdout_virtio_user.execute_cmd("quit", "#")
            self.pmdout_vhost_user.execute_cmd("quit", "#")
            self.launch_testpmd_as_vhost_user(
                vhost_param % (nb_cores),
                self.cores[0:2],
                dev=vhost_vdevs % (queues),
                ports=allow_pci,
                iova_mode="pa",
                set_pmd_param=False,
            )
            self.launch_testpmd_as_virtio_user(
                virtio_param % (nb_cores, txd_rxd, txd_rxd, txq_rxq, txq_rxq),
                self.cores[2:4],
                dev=virtio_dev % (queues),
                set_pmd_param=False,
            )
        self.send_chain_packets_and_verify()

    def test_loopback_packed_ring_large_chain_packets_stress_test_with_cbdma_enqueue(
        self,
    ):
        """
        Test Case6: loopback packed ring large chain packets stress test with cbdma enqueue
        """
        nb_cores = 1
        queues = 1
        txd_rxd = 2048
        txq_rxq = 1
        virtio_path = "/tmp/s0"
        path_mode = "mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048"
        self.get_cbdma_ports_info_and_bind_to_dpdk(1)
        vhost_param = " --nb-cores=%d --mbuf-size=65535"
        virtio_param = " --nb-cores=%d --txd=%d --rxd=%d --txq=%d --rxq=%d "
        virtio_dev = f"net_virtio_user0,mac={self.virtio_mac},path={virtio_path},{path_mode},queues=%d"
        vhost_vdevs = (
            f"'net_vhost0,iface=/tmp/s0,queues=%d,dmas=[txq0@{self.device_str}]'"
        )
        allow_pci = []
        for index in range(1):
            allow_pci.append(self.cbdma_dev_infos[index])
        self.launch_testpmd_as_vhost_user(
            vhost_param % (nb_cores),
            self.cores[0:2],
            dev=vhost_vdevs % (queues),
            ports=allow_pci,
            iova_mode="va",
            set_pmd_param=False,
        )
        self.launch_testpmd_as_virtio_user(
            virtio_param % (nb_cores, txd_rxd, txd_rxd, txq_rxq, txq_rxq),
            self.cores[2:4],
            dev=virtio_dev % (queues),
            set_pmd_param=False,
        )
        self.send_chain_packets_and_verify()

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost testpmd with PA mode")
            self.pmdout_virtio_user.execute_cmd("quit", "#")
            self.pmdout_vhost_user.execute_cmd("quit", "#")
            self.launch_testpmd_as_vhost_user(
                vhost_param % (nb_cores),
                self.cores[0:2],
                dev=vhost_vdevs % (queues),
                ports=allow_pci,
                iova_mode="pa",
                set_pmd_param=False,
            )
            self.launch_testpmd_as_virtio_user(
                virtio_param % (nb_cores, txd_rxd, txd_rxd, txq_rxq, txq_rxq),
                self.cores[2:4],
                dev=virtio_dev % (queues),
                set_pmd_param=False,
            )
            self.send_chain_packets_and_verify()

    def send_imix_and_verify(self, mode, multiple_queue=True, queue_list=[]):
        """
        Send imix packet with packet generator and verify
        """
        frame_sizes = [
            64,
            128,
            256,
            512,
            1024,
            1280,
            1518,
        ]
        tgenInput = []
        for frame_size in frame_sizes:
            payload_size = frame_size - self.headers_size
            port = self.tester.get_local_port(self.dut_ports[0])
            fields_config = {
                "ip": {
                    "src": {"action": "random"},
                },
            }
            if not multiple_queue:
                fields_config = None
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
        if queue_list:
            self.check_packets_of_each_queue(queue_list=queue_list)

    def send_and_verify(
        self,
        mode,
        multiple_queue=True,
        queue_list=[],
        frame_sizes=None,
        pkt_length_mode="imix",
    ):
        """
        Send packet with packet generator and verify
        """
        if pkt_length_mode == "imix":
            self.send_imix_and_verify(mode, multiple_queue, queue_list)
            return

        self.throughput[mode] = dict()
        for frame_size in frame_sizes:
            self.throughput[mode][frame_size] = dict()
            payload_size = frame_size - self.headers_size
            tgenInput = []
            port = self.tester.get_local_port(self.dut_ports[0])
            fields_config = {
                "ip": {
                    "src": {"action": "random"},
                },
            }
            if not multiple_queue:
                fields_config = None
            pkt1 = Packet()
            pkt1.assign_layers(["ether", "ipv4", "raw"])
            pkt1.config_layers(
                [
                    ("ether", {"dst": "%s" % self.virtio_mac}),
                    ("ipv4", {"src": "1.1.1.1"}),
                    ("raw", {"payload": ["01"] * int("%d" % payload_size)}),
                ]
            )
            pkt1.save_pcapfile(
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
            trans_options = {"delay": 5, "duration": 20}
            _, pps = self.tester.pktgen.measure_throughput(
                stream_ids=streams, options=trans_options
            )
            Mpps = pps / 1000000.0
            self.verify(
                Mpps > 0,
                "%s can not receive packets of frame size %d"
                % (self.running_case, frame_size),
            )
            throughput = Mpps * 100 / float(self.wirespeed(self.nic, frame_size, 1))
            self.throughput[mode][frame_size][self.nb_desc] = Mpps
            results_row = [frame_size]
            results_row.append(mode)
            results_row.append(Mpps)
            results_row.append(throughput)
            self.result_table_add(results_row)
        if queue_list:
            self.check_packets_of_each_queue(queue_list=queue_list)

    def handle_expected(self, mode_list):
        """
        Update expected numbers to configurate file: $DTS_CFG_FOLDER/$suite_name.cfg
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
        # Create test results table
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
