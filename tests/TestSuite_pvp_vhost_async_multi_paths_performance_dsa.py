# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2023 Intel Corporation
#

import json
import os
from copy import deepcopy

import framework.rst as rst
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import UPDATE_EXPECTED, load_global_setting
from framework.test_case import TestCase

from .virtio_common import dsa_common as DC


class TestPVPVhostAsyncMultiPathsPerformanceDsa(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user_pmd = PmdOutput(self.dut, self.virtio_user)
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_user_core = self.core_list[0:2]
        self.virtio_user_core = self.core_list[2:4]
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.number_of_ports = 1
        self.testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.testpmd_path.split("/")[-1]
        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.save_result_flag = True
        self.json_obj = {}
        self.DC = DC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        # Prepare the result table
        self.table_header = ["Frame"]
        self.table_header.append("Mode/RXD-TXD")
        self.table_header.append("Mpps")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)

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

    def start_vhost_user_testpmd(self, eal_param, param, ports, port_options=""):
        """
        start testpmd on vhost-user
        """
        if port_options:
            self.vhost_user_pmd.start_testpmd(
                cores=self.vhost_user_core,
                eal_param=eal_param,
                param=param,
                ports=ports,
                port_options=port_options,
                prefix="vhost-user",
                fixed_prefix=True,
            )
        else:
            self.vhost_user_pmd.start_testpmd(
                cores=self.vhost_user_core,
                eal_param=eal_param,
                param=param,
                ports=ports,
                prefix="vhost-user",
                fixed_prefix=True,
            )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

    def start_virtio_user_testpmd(self, eal_param, param):
        """
        start testpmd on virtio-user
        """
        if "vectorized" and "packed" in self.running_case:
            eal_param += " --force-max-simd-bitwidth=512"
        self.virtio_user_pmd.start_testpmd(
            cores=self.virtio_user_core,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="virtio-user",
            fixed_prefix=True,
        )
        self.virtio_user_pmd.execute_cmd("set fwd mac")
        self.virtio_user_pmd.execute_cmd("start")

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
            pkt = Packet(pkt_type="TCP", pkt_len=frame_size)
            pkt.config_layer("ether", {"dst": "%s" % destination_mac})
            pkt.save_pcapfile(
                self.tester, "%s/multi_path_%s.pcap" % (self.out_path, frame_size)
            )
            tgen_input.append(
                (
                    tx_port,
                    rx_port,
                    "%s/multi_path_%s.pcap" % (self.out_path, frame_size),
                )
            )
            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(
                tgen_input, 100, None, self.tester.pktgen
            )
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
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

    def test_perf_pvp_split_ring_inorder_mergeable_idxd(self):
        """
        Test Case 1: pvp vhost async test with split ring inorder mergeable path using IDXD kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param, param=vhost_param, ports=ports
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=1"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "split_ring_inorder_mergeable_idxd"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_split_ring_inorder_non_mergeable_idxd(self):
        """
        Test Case 2: pvp vhost async test with split ring inorder non-mergeable path using IDXD kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param, param=vhost_param, ports=ports
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=0,"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "split_ring_inorder_non_mergeable_idxd"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_split_ring_mergeable_idxd(self):
        """
        Test Case 3: pvp vhost async test with split ring mergeable path using IDXD kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param, param=vhost_param, ports=ports
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=1,"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "split_ring_mergeable_idxd"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_split_ring_non_mergeable_idxd(self):
        """
        Test Case 4: pvp vhost async test with split ring non-mergeable path using IDXD kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param, param=vhost_param, ports=ports
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0,"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "split_ring_non_mergeable_idxd"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_split_ring_vectorized_idxd(self):
        """
        Test Case 5: pvp vhost async test with split ring vectorized path using IDXD kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param, param=vhost_param, ports=ports
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0,vectorized=1"
        virtio_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "split_ring_non_vectorized_idxd"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_packed_ring_inorder_mergeable_idxd(self):
        """
        Test Case 6: pvp vhost async test with packed ring inorder mergeable path using IDXD kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param, param=vhost_param, ports=ports
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=1"
        virtio_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "packed_ring_inorder_mergeable_idxd"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_packed_ring_inorder_non_mergeable_idxd(self):
        """
        Test Case 7: pvp vhost async test with packed ring inorder non-mergeable path using IDXD kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param, param=vhost_param, ports=ports
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=0"
        virtio_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "packed_ring_inorder_non_mergeable_idxd"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_packed_ring_mergeable_idxd(self):
        """
        Test Case 8: pvp vhost async test with packed ring mergeable path using IDXD kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param, param=vhost_param, ports=ports
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=0,mrg_rxbuf=1"
        virtio_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "packed_ring_mergeable_idxd"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_packed_ring_non_mergeable_idxd(self):
        """
        Test Case 9: pvp vhost async test with packed ring non-mergeable path using IDXD kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param, param=vhost_param, ports=ports
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=0,mrg_rxbuf=0"
        virtio_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "packed_ring_non_mergeable_idxd"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_packed_ring_vectorized_idxd(self):
        """
        Test Case 10: pvp vhost async test with packed ring vectorized path using IDXD kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param, param=vhost_param, ports=ports
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=0,vectorized=1"
        virtio_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "packed_ring_vectorized_idxd"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_split_ring_inorder_mergeable_vfio_pci(self):
        """
        Test Case 11: pvp vhost async test with split ring inorder mergeable path using vfio-pci driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=1"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "split_ring_inorder_mergeable_vfio_pci"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_split_ring_inorder_non_mergeable_vfio_pci(self):
        """
        Test Case 12: pvp vhost async test with split ring inorder non-mergeable path using vfio-pci driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=1,mrg_rxbuf=0"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "split_ring_inorder_non_mergeable_vfio_pci"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_split_ring_mergeable_vfio_pci(self):
        """
        Test Case 13: pvp vhost async test with split ring mergeable path using vfio-pci driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=1"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "split_ring_mergeable_vfio_pci"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_split_ring_non_mergeable_vfio_pci(self):
        """
        Test Case 14: pvp vhost async test with split ring non-mergeable path using vfio-pci driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "split_ring_non_mergeable_vfio_pci"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_split_ring_vectorized_vfio_pci(self):
        """
        Test Case 15: pvp vhost async test with split ring vectorized_rx path using vfio-pci driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,in_order=0,mrg_rxbuf=0,vectorized=1"
        virtio_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "split_ring_vectorized_vfio_pci"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_packed_ring_inorder_mergeable_vfio_pci(self):
        """
        Test Case 16: pvp vhost async test with packed ring inorder mergeable path using vfio-pci driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=1"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "packed_ring_inorder_mergeable_vfio_pci"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_packed_ring_inorder_non_mergeable_vfio_pci(self):
        """
        Test Case 17: pvp vhost async test with packed ring inorder non-mergeable path using vfio-pci driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=0"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "packed_ring_inorder_non_mergeable_vfio_pci"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_packed_ring_mergeable_vfio_pci(self):
        """
        Test Case 18: pvp vhost async test with packed ring mergeable path using vfio-pci driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=0,mrg_rxbuf=1"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "packed_ring_mergeable_vfio_pci"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_packed_ring_non_mergeable_vfio_pci(self):
        """
        Test Case 19: pvp vhost async test with packed ring non-mergeable path using vfio-pci driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=0,mrg_rxbuf=0"
        virtio_param = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "packed_ring_non_mergeable_vfio_pci"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_packed_ring_vectorized_vfio_pci(self):
        """
        Test Case 20: pvp vhost async test with split ring vectorized path using vfio-pci driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1,in_order=1,mrg_rxbuf=0,vectorized=1"
        virtio_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        self.start_virtio_user_testpmd(eal_param=virtio_eal_param, param=virtio_param)

        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        case_info = "packed_ring_vectorized_vfio_pci"
        self.send_and_verify(case_info)
        self.result_table_print()
        self.quit_all_testpmd()
        self.handle_expected()
        self.handle_results()

    def quit_all_testpmd(self):
        self.virtio_user_pmd.quit()
        self.vhost_user_pmd.quit()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.virtio_user)
        self.dut.close_session(self.vhost_user)
