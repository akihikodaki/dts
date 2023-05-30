# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

"""
DPDK Test suite.
Test PVP performance using virtio_user on 8 tx/rx path.
"""
import json
import os
from copy import deepcopy

import framework.rst as rst
import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import UPDATE_EXPECTED, load_global_setting
from framework.test_case import TestCase


class TestPVPMultiPathsPerformance(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.core_config = "1S/4C/1T"
        self.number_of_ports = 1
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket
        )
        self.core_list_user = self.core_list[0:2]
        self.core_list_host = self.core_list[2:4]

        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user0")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.save_result_flag = True
        self.json_obj = {}

    def set_up(self):
        """
        Run before each test case.
        """
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
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]

    def send_and_verify(self, case_info):
        """
        Send packet with packet generator and verify
        """
        for frame_size in self.frame_sizes:
            tgen_input = []
            self.throughput[frame_size] = dict()

            self.logger.info(
                "Test running at parameters: "
                + "framesize: {}, rxd/txd: {}".format(frame_size, self.nb_desc)
            )
            rx_port = self.tester.get_local_port(self.dut_ports[0])
            tx_port = self.tester.get_local_port(self.dut_ports[0])
            destination_mac = self.dut.get_mac_address(self.dut_ports[0])
            pkt = Packet(pkt_type="UDP", pkt_len=frame_size)
            pkt.config_layer("ether", {"dst": "%s" % destination_mac})
            pkt.save_pcapfile(self.tester, "%s/multi_path.pcap" % (self.out_path))
            tgen_input.append(
                (tx_port, rx_port, "%s/multi_path.pcap" % (self.out_path))
            )

            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(
                tgen_input, 100, None, self.tester.pktgen
            )
            trans_options = {"delay": 5, "duration": 30}
            _, pps = self.tester.pktgen.measure_throughput(
                stream_ids=streams, options=trans_options
            )
            Mpps = pps / 1000000.0
            self.throughput[frame_size][self.nb_desc] = Mpps
            linerate = (
                Mpps
                * 100
                / float(self.wirespeed(self.nic, frame_size, self.number_of_ports))
            )

            results_row = [frame_size]
            results_row.append(case_info)
            results_row.append(Mpps)
            results_row.append(linerate)
            self.result_table_add(results_row)

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def start_vhost_testpmd(self):
        """
        start testpmd on vhost
        """
        self.dut.send_expect("rm -rf ./vhost.out", "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        vdevs = ["net_vhost0,iface=vhost-net,queues=1,client=0"]
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        param = "--nb-cores=1 --txd=%d --rxd=%d" % (self.nb_desc, self.nb_desc)
        self.vhost_user_pmd.start_testpmd(
            cores=self.core_list_host,
            param=param,
            vdevs=vdevs,
            ports=ports,
            prefix="vhost",
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

    def start_virtio_testpmd(self, args):
        """
        start testpmd on virtio
        """
        eal_param = ""
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        if "virtio11_vectorized" in self.running_case:
            eal_param += " --force-max-simd-bitwidth=512"
        vdevs = [
            "net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,%s"
            % args["version"]
        ]
        param = "%s --rss-ip --nb-cores=1 --txd=%d --rxd=%d" % (
            args["path"],
            self.nb_desc,
            self.nb_desc,
        )
        self.virtio_user0_pmd.start_testpmd(
            cores=self.core_list_user,
            eal_param=eal_param,
            param=param,
            vdevs=vdevs,
            no_pci=True,
            prefix="virtio",
        )
        self.virtio_user0_pmd.execute_cmd("set fwd mac")
        self.virtio_user0_pmd.execute_cmd("start")

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

    def close_all_testpmd(self):
        """
        close all testpmd of vhost and virtio
        """
        self.vhost_user_pmd.execute_cmd("quit", "# ")
        self.virtio_user0_pmd.execute_cmd("quit", "# ")

    def close_all_session(self):
        """
        close all session of vhost an virtio
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user0)

    def test_perf_pvp_virtio11_mergeable(self):
        """
        performance for PVP virtio 1.1 Mergeable Path.
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        virtio_pmd_arg = {
            "version": "in_order=0,packed_vq=1,mrg_rxbuf=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virtio_1.1_mergeable on")
        self.close_all_testpmd()
        self.logger.info("result of all framesize result")
        self.result_table_print()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_virtio11_normal(self):
        """
        performance for PVP virtio1.1 Normal Path.
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        virtio_pmd_arg = {
            "version": "in_order=0,packed_vq=1,mrg_rxbuf=0",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virtio_1.1_normal")
        self.close_all_testpmd()
        self.logger.info("result of all framesize result")
        self.result_table_print()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_virtio11_inorder_mergeable(self):
        """
        performance for PVP virtio 1.1 inorder Mergeable Path.
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        virtio_pmd_arg = {
            "version": "in_order=1,packed_vq=1,mrg_rxbuf=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virtio_1.1_inorder_mergeable on")
        self.close_all_testpmd()
        self.logger.info("result of all framesize result")
        self.result_table_print()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_virtio11_inorder_normal(self):
        """
        performance for PVP virtio1.1 inorder Normal Path.
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        virtio_pmd_arg = {
            "version": "in_order=1,packed_vq=1,mrg_rxbuf=0",
            "path": "--rx-offloads=0x10 --enable-hw-vlan-strip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virtio_1.1_inorder_normal")
        self.close_all_testpmd()
        self.logger.info("result of all framesize result")
        self.result_table_print()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_virtio11_vectorized(self):
        """
        performance for PVP virtio1.1 Vectorized Path.
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        virtio_pmd_arg = {
            "version": "in_order=1,packed_vq=1,mrg_rxbuf=0,vectorized=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virtio_1.1_inorder_normal")
        self.close_all_testpmd()
        self.logger.info("result of all framesize result")
        self.result_table_print()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_inorder_mergeable(self):
        """
        performance for PVP In_order mergeable Path.
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        virtio_pmd_arg = {
            "version": "packed_vq=0,in_order=1,mrg_rxbuf=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("inoder mergeable on")
        self.close_all_testpmd()
        self.logger.info("result of all framesize result")
        self.result_table_print()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_inorder_normal(self):
        """
        performance for PVP In_order Normal Path.
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        virtio_pmd_arg = {
            "version": "packed_vq=0,in_order=1,mrg_rxbuf=0",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("inoder mergeable off")
        self.close_all_testpmd()
        self.logger.info("result of all framesize result")
        self.result_table_print()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_mergeable(self):
        """
        performance for PVP Mergeable Path.
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        virtio_pmd_arg = {
            "version": "packed_vq=0,in_order=0,mrg_rxbuf=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virito mergeable")
        self.close_all_testpmd()
        self.logger.info("result of all framesize result")
        self.result_table_print()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_normal(self):
        """
        performance for PVP Normal Path.
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        virtio_pmd_arg = {
            "version": "packed_vq=0,in_order=0,mrg_rxbuf=0,vectorized=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virito normal")
        self.close_all_testpmd()
        self.logger.info("result of all framesize result")
        self.result_table_print()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_vector_rx(self):
        """
        performance for PVP Vector_RX Path
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        virtio_pmd_arg = {
            "version": "packed_vq=0,in_order=0,mrg_rxbuf=0,vectorized=1",
            "path": "--tx-offloads=0x0 ",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virito vector rx")
        self.close_all_testpmd()
        self.logger.info("result of all framesize result")
        self.result_table_print()
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
