# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

"""
DPDK Test suite.
"""

import json
import os
import re
import time
from copy import deepcopy

import framework.rst as rst
import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import UPDATE_EXPECTED, load_global_setting
from framework.test_case import TestCase


class TestVswitchPvpMultiPathsPerformanceWithCbdma(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.build_vhost_app()
        self.dut_ports = self.dut.get_ports()
        self.number_of_ports = 1
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("all", socket=self.ports_socket)
        self.vhost_core_list = self.cores[0:2]
        self.vuser0_core_list = self.cores[2:4]
        self.vhost_core_mask = utils.create_mask(self.vhost_core_list)
        self.mem_channels = self.dut.get_memory_channels()
        # get cbdma device
        self.cbdma_dev_infos = []
        self.dmas_info = None
        self.device_str = None
        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        txport = self.tester.get_local_port(self.dut_ports[0])
        self.txItf = self.tester.get_interface(txport)
        self.virtio_user0_mac = "00:11:22:33:44:10"
        self.vm_num = 2
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.pktgen_helper = PacketGeneratorHelper()
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user0")
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.frame_size = [64, 128, 256, 512, 1024, 1518]
        self.save_result_flag = True
        self.json_obj = {}

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -I dpdk-vhost", "#", 20)
        self.dut.send_expect("killall -I dpdk-testpmd", "#", 20)
        self.dut.send_expect("killall -I qemu-system-x86_64", "#", 20)

        # Prepare the result table
        self.table_header = ["Frame"]
        self.table_header.append("Mode/RXD-TXD")
        self.table_header.append("Mpps")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)

        self.test_parameters = self.get_suite_cfg()["test_parameters"]
        # test parameters include: frames size, descriptor numbers
        self.test_parameters = self.get_suite_cfg()["test_parameters"]

        # traffic duraion in second
        self.test_duration = self.get_suite_cfg()["test_duration"]

        # initilize throughput attribution
        # {'$framesize':{"$nb_desc": 'throughput'}
        self.throughput = {}

        # Accepted tolerance in Mpps
        self.gap = self.get_suite_cfg()["accepted_tolerance"]
        self.test_result = {}
        self.nb_desc = self.test_parameters[64][0]

    def build_vhost_app(self):
        out = self.dut.build_dpdk_apps("./examples/vhost")
        self.verify("Error" not in out, "compilation vhost error")

    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def start_vhost_app(self, allow_pci):
        """
        launch the vhost app on vhost side
        """
        self.app_path = self.dut.apps_name["vhost"]
        socket_file_param = "--socket-file ./vhost-net"
        allow_option = ""
        for item in allow_pci:
            allow_option += " -a {}".format(item)
        params = (
            " -c {} -n {} {} -- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 "
            + socket_file_param
            + " --dmas [{}] --total-num-mbufs 600000"
        ).format(
            self.vhost_core_mask,
            self.mem_channels,
            allow_option,
            self.dmas_info,
        )
        self.command_line = self.app_path + params
        self.vhost_user.send_command(self.command_line)
        time.sleep(3)

    def start_virtio_testpmd(
        self,
        virtio_path,
        vlan_strip=False,
        force_max_simd_bitwidth=False,
    ):
        """
        launch the testpmd as virtio with vhost_net0
        """
        eal_params = (
            " --vdev=net_virtio_user0,mac={},path=./vhost-net,queues=1,{}".format(
                self.virtio_user0_mac, virtio_path
            )
        )
        if self.check_2M_env():
            eal_params += " --single-file-segments"
        if force_max_simd_bitwidth:
            eal_params += " --force-max-simd-bitwidth=512"
        params = "--rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1"
        if vlan_strip:
            params = "--rx-offloads=0x0 --enable-hw-vlan-strip " + params
        self.virtio_user0_pmd.start_testpmd(
            cores=self.vuser0_core_list,
            param=params,
            eal_param=eal_params,
            no_pci=True,
            ports=[],
            prefix="virtio-user0",
            fixed_prefix=True,
        )
        self.virtio_user0_pmd.execute_cmd("set fwd mac")
        self.virtio_user0_pmd.execute_cmd("start tx_first")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.execute_cmd("start")

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
        used_cbdma = self.cbdma_dev_infos[0:cbdma_num]
        dmas_info = ""
        for dmas in used_cbdma:
            number = used_cbdma.index(dmas)
            dmas = "txd{}@{},".format(number, dmas)
            dmas_info += dmas
        self.dmas_info = dmas_info[:-1]
        self.device_str = " ".join(used_cbdma)
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

    def config_stream(self, frame_size):
        tgen_input = []
        rx_port = self.tester.get_local_port(self.dut_ports[0])
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        pkt = Packet(pkt_type="UDP", pkt_len=frame_size)
        pkt.config_layer("ether", {"dst": self.virtio_user0_mac})
        pcap = os.path.join(
            self.out_path, "vswitch_pvp_multi_path_%s.pcap" % (frame_size)
        )
        pkt.save_pcapfile(self.tester, pcap)
        tgen_input.append((rx_port, tx_port, pcap))
        return tgen_input

    def perf_test(self, case_info):
        for frame_size in self.frame_size:
            self.throughput[frame_size] = dict()
            self.logger.info(
                "Test running at parameters: " + "framesize: {}".format(frame_size)
            )
            tgenInput = self.config_stream(frame_size)
            # clear streams before add new streams
            self.tester.pktgen.clear_streams()
            # run packet generator
            streams = self.pktgen_helper.prepare_stream_from_tginput(
                tgenInput, 100, None, self.tester.pktgen
            )
            # set traffic option
            traffic_opt = {"duration": 5}
            _, pps = self.tester.pktgen.measure_throughput(
                stream_ids=streams, options=traffic_opt
            )
            Mpps = pps / 1000000.0
            linerate = (
                Mpps
                * 100
                / float(self.wirespeed(self.nic, frame_size, self.number_of_ports))
            )
            self.throughput[frame_size][self.nb_desc] = Mpps
            results_row = [frame_size]
            results_row.append(case_info)
            results_row.append(Mpps)
            results_row.append(linerate)
            self.result_table_add(results_row)
        self.result_table_print()

    def handle_expected(self):
        """
        Update expected numbers to configurate file: $DTS_CFG_FOLDER/$suite_name.cfg
        """
        if load_global_setting(UPDATE_EXPECTED) == "yes":
            for frame_size in self.test_parameters.keys():
                for nb_desc in self.test_parameters[frame_size]:
                    self.expected_throughput[frame_size][nb_desc] = round(
                        self.throughput[frame_size][nb_desc], 3
                    )

    def handle_results(self):
        """
        results handled process:
        1, save to self.test_results
        2, create test results table
        3, save to json file for Open Lab
        """
        header = self.table_header
        header.append("Expected Throughput")
        header.append("Throughput Difference")
        for frame_size in self.test_parameters.keys():
            wirespeed = self.wirespeed(self.nic, frame_size, self.number_of_ports)
            ret_datas = {}
            for nb_desc in self.test_parameters[frame_size]:
                ret_data = {}
                ret_data[header[0]] = frame_size
                ret_data[header[1]] = nb_desc
                ret_data[header[2]] = "{:.3f} Mpps".format(
                    self.throughput[frame_size][nb_desc]
                )
                ret_data[header[3]] = "{:.3f}%".format(
                    self.throughput[frame_size][nb_desc] * 100 / wirespeed
                )
                ret_data[header[4]] = "{:.3f} Mpps".format(
                    self.expected_throughput[frame_size][nb_desc]
                )
                ret_data[header[5]] = "{:.3f} Mpps".format(
                    self.throughput[frame_size][nb_desc]
                    - self.expected_throughput[frame_size][nb_desc]
                )
                ret_datas[nb_desc] = deepcopy(ret_data)
            self.test_result[frame_size] = deepcopy(ret_datas)
        # Create test results table
        self.result_table_create(header)
        for frame_size in self.test_parameters.keys():
            for nb_desc in self.test_parameters[frame_size]:
                table_row = list()
                for i in range(len(header)):
                    table_row.append(self.test_result[frame_size][nb_desc][header[i]])
                self.result_table_add(table_row)
        # present test results to screen
        self.result_table_print()
        # save test results as a file
        if self.save_result_flag:
            self.save_result(self.test_result)

    def save_result(self, data):
        """
        Saves the test results as a separated file named with
        self.nic+_perf_virtio_user_pvp.json in output folder
        if self.save_result_flag is True
        """
        case_name = self.running_case
        self.json_obj[case_name] = list()
        status_result = []
        for frame_size in self.test_parameters.keys():
            for nb_desc in self.test_parameters[frame_size]:
                row_in = self.test_result[frame_size][nb_desc]
                row_dict0 = dict()
                row_dict0["performance"] = list()
                row_dict0["parameters"] = list()
                row_dict0["parameters"] = list()
                result_throughput = float(row_in["Mpps"].split()[0])
                expected_throughput = float(row_in["Expected Throughput"].split()[0])
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
                    name="Throughput", value=result_throughput, unit="Mpps", delta=delta
                )
                row_dict2 = dict(
                    name="Txd/Rxd", value=row_in["Mode/RXD-TXD"], unit="descriptor"
                )
                row_dict3 = dict(name="frame_size", value=row_in["Frame"], unit="bytes")
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

    def test_perf_vswitch_pvp_split_ring_inorder_mergeable_path_performance_with_cbdma(
        self,
    ):
        """
        Test Case 1: Vswitch PVP split ring inorder mergeable path performance with CBDMA
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]

        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=cbdma_num)
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for item in range(cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[item])
        self.start_vhost_app(allow_pci=allow_pci)
        virtio_path = "packed_vq=0,mrg_rxbuf=1,in_order=1"
        self.start_virtio_testpmd(virtio_path=virtio_path)
        case_info = "split ring inorder mergeable"
        self.perf_test(case_info)
        self.handle_expected()
        self.handle_results()

    def test_perf_vswitch_pvp_split_ring_inorder_no_mergeable_path_performance_with_cbdma(
        self,
    ):
        """
        Test Case 2: Vswitch PVP split ring inorder non-mergeable path performance with CBDMA
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]

        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=cbdma_num)
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for item in range(cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[item])
        self.start_vhost_app(allow_pci=allow_pci)
        virtio_path = "packed_vq=0,mrg_rxbuf=0,in_order=1"
        self.start_virtio_testpmd(virtio_path=virtio_path)
        case_info = "split ring inorder non-mergeable"
        self.perf_test(case_info)
        self.handle_expected()
        self.handle_results()

    def test_perf_vswitch_pvp_split_ring_mergeable_path_performance_with_cbdma(self):
        """
        Test Case 3: Vswitch PVP split ring mergeable path performance with CBDMA
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]

        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=cbdma_num)
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for item in range(cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[item])
        self.start_vhost_app(allow_pci=allow_pci)
        virtio_path = "packed_vq=0,mrg_rxbuf=1,in_order=0"
        self.start_virtio_testpmd(virtio_path=virtio_path)
        case_info = "split ring mergeable"
        self.perf_test(case_info)
        self.handle_expected()
        self.handle_results()

    def test_perf_vswitch_pvp_split_ring_non_mergeable_path_performance_with_cbdma(
        self,
    ):
        """
        Test Case 4: Vswitch PVP split ring non-mergeable path performance with CBDMA
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]

        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=cbdma_num)
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for item in range(cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[item])
        self.start_vhost_app(allow_pci=allow_pci)
        virtio_path = "packed_vq=0,mrg_rxbuf=0,in_order=0"
        self.start_virtio_testpmd(virtio_path=virtio_path, vlan_strip=True)
        case_info = "split ring non-mergeable"
        self.perf_test(case_info)
        self.handle_expected()
        self.handle_results()

    def test_perf_vswitch_pvp_split_ring_vectorized_path_performance_with_cbdma(self):
        """
        Test Case 5: Vswitch PVP split ring vectorized path performance with CBDMA
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]

        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=cbdma_num)
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for item in range(cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[item])
        self.start_vhost_app(allow_pci=allow_pci)
        virtio_path = "packed_vq=0,mrg_rxbuf=0,in_order=1,vectorized=1"
        self.start_virtio_testpmd(virtio_path=virtio_path)
        case_info = "split ring vectorized"
        self.perf_test(case_info)
        self.handle_expected()
        self.handle_results()

    def test_perf_vswitch_pvp_packed_ring_inorder_mergeable_path_performance_with_cbdma(
        self,
    ):
        """
        Test Case 6: Vswitch PVP virtio 1.1 inorder mergeable path performance with CBDMA
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]

        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=cbdma_num)
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for item in range(cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[item])
        self.start_vhost_app(allow_pci=allow_pci)
        virtio_path = "packed_vq=1,mrg_rxbuf=1,in_order=1"
        self.start_virtio_testpmd(virtio_path=virtio_path)
        case_info = "split ring inorder mergeable"
        self.perf_test(case_info)
        self.handle_expected()
        self.handle_results()

    def test_perf_vswitch_pvp_packed_ring_inorder_no_mergeable_path_performance_with_cbdma(
        self,
    ):
        """
        Test Case 7: Vswitch PVP virtio 1.1 inorder non-mergeable path performance with CBDMA
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]

        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=cbdma_num)
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for item in range(cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[item])
        self.start_vhost_app(allow_pci=allow_pci)
        virtio_path = "packed_vq=1,mrg_rxbuf=0,in_order=1"
        self.start_virtio_testpmd(virtio_path=virtio_path)
        case_info = "split ring inorder non-mergeable"
        self.perf_test(case_info)
        self.handle_expected()
        self.handle_results()

    def test_perf_vswitch_pvp_packed_ring_mergeable_path_performance_with_cbdma(self):
        """
        Test Case 8: Vswitch PVP virtio 1.1 mergeable path performance with CBDMA
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]

        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=cbdma_num)
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for item in range(cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[item])
        self.start_vhost_app(allow_pci=allow_pci)
        virtio_path = "packed_vq=1,mrg_rxbuf=1,in_order=0"
        self.start_virtio_testpmd(virtio_path=virtio_path)
        case_info = "split ring mergeable"
        self.perf_test(case_info)
        self.handle_expected()
        self.handle_results()

    def test_perf_vswitch_pvp_packed_ring_non_mergeable_path_performance_with_cbdma(
        self,
    ):
        """
        Test Case 9: Vswitch PVP virtio 1.1 non-mergeable path performance with CBDMA
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]

        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=cbdma_num)
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for item in range(cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[item])
        self.start_vhost_app(allow_pci=allow_pci)
        virtio_path = "packed_vq=1,mrg_rxbuf=0,in_order=0"
        self.start_virtio_testpmd(virtio_path=virtio_path)
        case_info = "split ring non-mergeable"
        self.perf_test(case_info)
        self.handle_expected()
        self.handle_results()

    def test_perf_vswitch_pvp_packed_ring_vectorized_path_performance_with_cbdma(self):
        """
        Test Case 10: Vswitch PVP virtio 1.1 vectorized path performance with CBDMA
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]

        cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=cbdma_num)
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for item in range(cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[item])
        self.start_vhost_app(allow_pci=allow_pci)
        virtio_path = "packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1"
        self.start_virtio_testpmd(virtio_path=virtio_path)
        case_info = "split ring vectorized"
        self.perf_test(case_info)
        self.handle_expected()
        self.handle_results()

    def close_all_session(self):
        if getattr(self, "vhost_user", None):
            self.dut.close_session(self.vhost_user)
        if getattr(self, "virtio-user0", None):
            self.dut.close_session(self.virtio_user0)
        if getattr(self, "virtio-user1", None):
            self.dut.close_session(self.virtio_user1)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.virtio_user0_pmd.quit()
        self.vhost_user.send_expect("^C", "# ", 20)
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.close_all_session()
