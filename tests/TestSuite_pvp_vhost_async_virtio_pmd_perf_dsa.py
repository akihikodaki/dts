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
from framework.settings import HEADER_SIZE, UPDATE_EXPECTED, load_global_setting
from framework.test_case import TestCase
from framework.virt_common import VM

from .virtio_common import dsa_common as DC


class TestPVPVhostAsyncVirtioPmdPerfDsa(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.headers_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"] + HEADER_SIZE["tcp"]
        self.virtio_mac = "00:11:22:33:44:55"
        self.number_of_ports = 1
        self.testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.testpmd_path.split("/")[-1]
        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.logger.info(self.base_dir)
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
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.DC.reset_all_work_queue()
        self.DC.bind_all_dsa_to_kernel()
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

    def start_vhost_user_testpmd(self, cores, eal_param, param, ports):
        """
        start testpmd on vhost-user
        """
        self.vhost_user_pmd.start_testpmd(
            cores=cores,
            eal_param=eal_param,
            param=param,
            ports=ports,
            prefix="vhost-user",
            fixed_prefix=True,
        )

    def start_one_vm(self, packed=False):
        """
        start qemus
        """
        self.vm = VM(self.dut, "vm0", "vhost_sample")
        self.vm.load_config()
        vm_params = {}
        vm_params["driver"] = "vhost-user"
        vm_params["opt_path"] = "%s/vhost-net" % self.base_dir
        vm_params["opt_mac"] = "%s" % self.virtio_mac
        vm_params["opt_queue"] = self.queues
        packed_param = ",packed=on" if packed else ""
        mq_param = (
            "mq=on,vectors=%s," % (2 + self.queues * 2) if self.queues > 1 else ""
        )
        vm_params["opt_settings"] = (
            "disable-modern=false,mrg_rxbuf=on,%srx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso= off,host_tso4=off,guest_tso4=off,guest_ecn=off%s"
            % (mq_param, packed_param)
        )
        self.vm.set_vm_device(**vm_params)
        try:
            self.vm_dut = self.vm.start(load_config=False)
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

    def start_vm_testpmd(self):
        """
        start testpmd in VM
        """
        self.vm0_pmd = PmdOutput(self.vm_dut)
        param = "--nb-cores=%d --txq=%d --rxq=%d --txd=2048 --rxd=2048" % (
            self.nb_cores,
            self.queues,
            self.queues,
        )
        cores = self.vm_dut.get_core_list(config="all")[0 : (self.nb_cores + 1)]
        self.vm0_pmd.start_testpmd(cores=cores, param=param)
        self.vm0_pmd.execute_cmd("set fwd csum")
        self.vm0_pmd.execute_cmd("start")

    def send_and_verify(self, case_info):
        """
        Send packet with packet generator and verify
        """
        if "4c_4q" or "4c_8q" not in self.running_case:
            frame_sizes = [64, 128, 256, 512, 1024, 1280, 1518]
        else:
            frame_sizes = [64, 128, 256, 512, 1024, 1280, 1518, 2048, 4096]
        for frame_size in frame_sizes:
            payload_size = frame_size - self.headers_size
            tgen_input = []
            self.throughput[frame_size] = dict()
            self.logger.info(
                "Test running at parameters: "
                + "framesize: {}, rxd/txd: {}".format(frame_size, self.nb_desc)
            )
            rx_port = self.tester.get_local_port(self.dut_ports[0])
            tx_port = self.tester.get_local_port(self.dut_ports[0])
            fields_config = {
                "ip": {
                    "src": {"action": "random"},
                    "dst": {"action": "random"},
                },
            }
            pkt = Packet()
            pkt.assign_layers(["ether", "ipv4", "tcp", "raw"])
            pkt.config_layers(
                [
                    ("ether", {"dst": "%s" % self.virtio_mac}),
                    ("ipv4", {"src": "1.1.1.1", "dst": "2.2.2.2"}),
                    ("raw", {"payload": ["01"] * int("%d" % payload_size)}),
                ]
            )
            pkt.save_pcapfile(
                self.tester,
                "%s/pvp_virtio_pmd_perf_dsa_%s.pcap" % (self.out_path, frame_size),
            )
            tgen_input.append(
                (
                    tx_port,
                    rx_port,
                    "%s/pvp_virtio_pmd_perf_dsa_%s.pcap" % (self.out_path, frame_size),
                )
            )
            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(
                tgen_input, 100, fields_config, self.tester.pktgen
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

    def perf_test(self, case_info, ports, packed=False, port_options=""):
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        vhost_eal_param = (
            "--socket-mem 8192 --vdev 'net_vhost0,iface=vhost-net,queues=%d,dmas=[%s]'"
            % (self.queues, self.dmas)
        )
        if "4c_4q" or "4c_8q" not in self.running_case:
            max_len_param = ""
        else:
            max_len_param = "--max-pkt-len=5200 --tx-offloads=0x00008000"
        vhost_param = (
            "--nb-cores=%d --txq=%d --rxq=%d --txd=2048 --rxd=2048 %s --forward-mode=mac -a"
            % (self.nb_cores, self.queues, self.queues, max_len_param)
        )
        cores = self.core_list[0 : (self.nb_cores + 1)]
        if not port_options:
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=ports,
                prefix="vhost-user",
                fixed_prefix=True,
            )
        else:
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=ports,
                port_options=port_options,
                prefix="vhost-user",
                fixed_prefix=True,
            )

        self.start_one_vm(packed=packed)
        self.start_vm_testpmd()
        self.send_and_verify(case_info=case_info)
        self.result_table_print()
        self.handle_expected()
        self.handle_results()

    def test_perf_virtio_pmd_split_ring_1c_1q_idxd(self):
        """
        Test Case 1: pvp split ring vhost async test with 1core 1queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=2, dsa_index=0)
        self.queues = 1
        self.dmas = "txq0@wq0.0;rxq0@wq0.1"
        self.nb_cores = 1
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=False, port_options=""
        )

    def test_perf_virtio_pmd_split_ring_1c_2q_idxd(self):
        """
        Test Case 2: pvp split ring vhost async test with 1core 2queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=4, dsa_index=0)
        self.queues = 2
        self.dmas = "txq0@wq0.0;rxq0@wq0.1;txq1@wq0.2;rxq1@wq0.3"
        self.nb_cores = 1
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=False, port_options=""
        )

    def test_perf_virtio_pmd_split_ring_2c_2q_idxd(self):
        """
        Test Case 3: pvp split ring vhost async test with 2core 2queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=4, dsa_index=0)
        self.queues = 2
        self.dmas = "txq0@wq0.0;rxq0@wq0.1;txq1@wq0.2;rxq1@wq0.3"
        self.nb_cores = 2
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=False, port_options=""
        )

    def test_perf_virtio_pmd_split_ring_2c_4q_idxd(self):
        """
        Test Case 4: pvp split ring vhost async test with 2core 4queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.queues = 4
        self.dmas = (
            "txq0@wq0.0;"
            "rxq0@wq0.1;"
            "txq1@wq0.2;"
            "rxq1@wq0.3;"
            "txq2@wq0.4;"
            "rxq2@wq0.5;"
            "txq3@wq0.6;"
            "rxq3@wq0.7"
        )
        self.nb_cores = 2
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=False, port_options=""
        )

    def test_perf_virtio_pmd_split_ring_4c_4q_idxd(self):
        """
        Test Case 5: pvp split ring vhost async test with 4core 4queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.queues = 4
        self.dmas = (
            "txq0@wq0.0;"
            "rxq0@wq0.1;"
            "txq1@wq0.2;"
            "rxq1@wq0.3;"
            "txq2@wq0.4;"
            "rxq2@wq0.5;"
            "txq3@wq0.6;"
            "rxq3@wq0.7"
        )
        self.nb_cores = 4
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=False, port_options=""
        )

    def test_perf_virtio_pmd_split_ring_4c_8q_idxd(self):
        """
        Test Case 6: pvp split ring vhost async test with 4core 8queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.queues = 8
        self.dmas = (
            "txq0@wq0.0;"
            "rxq0@wq0.0;"
            "txq1@wq0.1;"
            "rxq1@wq0.1;"
            "txq2@wq0.2;"
            "rxq2@wq0.2;"
            "txq3@wq0.3;"
            "rxq3@wq0.3;"
            "txq4@wq0.4;"
            "rxq4@wq0.4;"
            "txq5@wq0.5;"
            "rxq5@wq0.5;"
            "txq6@wq0.6;"
            "rxq6@wq0.6;"
            "txq7@wq0.7;"
            "rxq7@wq0.7"
        )
        self.nb_cores = 4
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=False, port_options=""
        )

    def test_perf_virtio_pmd_packed_ring_1c_1q_idxd(self):
        """
        Test Case 7: pvp packed ring vhost async test with 1core 1queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=2, dsa_index=0)
        self.queues = 1
        self.dmas = "txq0@wq0.0;rxq0@wq0.1"
        self.nb_cores = 1
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=True, port_options=""
        )

    def test_perf_virtio_pmd_packed_ring_1c_2q_idxd(self):
        """
        Test Case 8: pvp packed ring vhost async test with 1core 2queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=4, dsa_index=0)
        self.queues = 2
        self.dmas = "txq0@wq0.0;rxq0@wq0.1;txq1@wq0.2;rxq1@wq0.3"
        self.nb_cores = 1
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=True, port_options=""
        )

    def test_perf_virtio_pmd_packed_ring_2c_2q_idxd(self):
        """
        Test Case 9: pvp packed ring vhost async test with 2core 2queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=4, dsa_index=0)
        self.queues = 2
        self.dmas = "txq0@wq0.0;rxq0@wq0.1;txq1@wq0.2;rxq1@wq0.3"
        self.nb_cores = 2
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=True, port_options=""
        )

    def test_perf_virtio_pmd_packed_ring_2c_4q_idxd(self):
        """
        Test Case 10: pvp packed ring vhost async test with 2core 4queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.queues = 4
        self.dmas = (
            "txq0@wq0.0;"
            "rxq0@wq0.1;"
            "txq1@wq0.2;"
            "rxq1@wq0.3;"
            "txq2@wq0.4;"
            "rxq2@wq0.5;"
            "txq3@wq0.6;"
            "rxq3@wq0.7"
        )
        self.nb_cores = 2
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=True, port_options=""
        )

    def test_perf_virtio_pmd_packed_ring_4c_4q_idxd(self):
        """
        Test Case 11: pvp packed ring vhost async test with 4core 4queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.queues = 4
        self.dmas = (
            "txq0@wq0.0;"
            "rxq0@wq0.1;"
            "txq1@wq0.2;"
            "rxq1@wq0.3;"
            "txq2@wq0.4;"
            "rxq2@wq0.5;"
            "txq3@wq0.6;"
            "rxq3@wq0.7"
        )
        self.nb_cores = 4
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=True, port_options=""
        )

    def test_perf_virtio_pmd_packed_ring_4c_8q_idxd(self):
        """
        Test Case 12: pvp packed ring vhost async test with 4core 8queue using idxd kernel driver
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.queues = 8
        self.dmas = (
            "txq0@wq0.0;"
            "rxq0@wq0.0;"
            "txq1@wq0.1;"
            "rxq1@wq0.1;"
            "txq2@wq0.2;"
            "rxq2@wq0.2;"
            "txq3@wq0.3;"
            "rxq3@wq0.3;"
            "txq4@wq0.4;"
            "rxq4@wq0.4;"
            "txq5@wq0.5;"
            "rxq5@wq0.5;"
            "txq6@wq0.6;"
            "rxq6@wq0.6;"
            "txq7@wq0.7;"
            "rxq7@wq0.7"
        )
        self.nb_cores = 4
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        self.perf_test(
            case_info=self.running_case, ports=ports, packed=True, port_options=""
        )

    def test_perf_virtio_pmd_split_ring_1c_1q_vfio_pci(self):
        """
        Test Case 13: pvp split ring vhost async test with 1core 1queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 1
        self.dmas = "txq0@%s-q0;rxq0@%s-q1" % (
            self.use_dsa_list[0],
            self.use_dsa_list[0],
        )
        self.nb_cores = 1
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=2"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=False,
            port_options=port_options,
        )

    def test_perf_virtio_pmd_split_ring_1c_2q_vfio_pci(self):
        """
        Test Case 14: pvp split ring vhost async test with 1core 2queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 2
        self.dmas = (
            "txq0@%s-q0;"
            "rxq0@%s-q1;"
            "txq1@%s-q2;"
            "rxq1@%s-q3"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        self.nb_cores = 1
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=False,
            port_options=port_options,
        )

    def test_perf_virtio_pmd_split_ring_2c_2q_vfio_pci(self):
        """
        Test Case 15: pvp split ring vhost async test with 2core 2queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 2
        self.dmas = (
            "txq0@%s-q0;"
            "rxq0@%s-q1;"
            "txq1@%s-q2;"
            "rxq1@%s-q3"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        self.nb_cores = 2
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=False,
            port_options=port_options,
        )

    def test_perf_virtio_pmd_split_ring_2c_4q_vfio_pci(self):
        """
        Test Case 16: pvp split ring vhost async test with 2core 4queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 4
        self.dmas = (
            "txq0@%s-q0;"
            "rxq0@%s-q1;"
            "txq1@%s-q2;"
            "rxq1@%s-q3;"
            "txq2@%s-q4;"
            "rxq2@%s-q5;"
            "txq3@%s-q6;"
            "rxq3@%s-q7"
            % (
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
        self.nb_cores = 2
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=8"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=False,
            port_options=port_options,
        )

    def test_perf_virtio_pmd_split_ring_4c_4q_vfio_pci(self):
        """
        Test Case 17: pvp split ring vhost async test with 4core 4queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 4
        self.dmas = (
            "txq0@%s-q0;"
            "rxq0@%s-q1;"
            "txq1@%s-q2;"
            "rxq1@%s-q3;"
            "txq2@%s-q4;"
            "rxq2@%s-q5;"
            "txq3@%s-q6;"
            "rxq3@%s-q7"
            % (
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
        self.nb_cores = 4
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=8"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=False,
            port_options=port_options,
        )

    def test_perf_virtio_pmd_split_ring_4c_8q_vfio_pci(self):
        """
        Test Case 18: pvp split ring vhost async test with 4core 8queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 8
        self.dmas = (
            "txq0@%s-q0;"
            "rxq0@%s-q1;"
            "txq1@%s-q2;"
            "rxq1@%s-q3;"
            "txq2@%s-q4;"
            "rxq2@%s-q5;"
            "txq3@%s-q6;"
            "rxq3@%s-q7"
            % (
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
        self.nb_cores = 4
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=8"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=False,
            port_options=port_options,
        )

    def test_perf_virtio_pmd_packed_ring_1c_1q_vfio_pci(self):
        """
        Test Case 19: pvp packed ring vhost async test with 1core 1queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 1
        self.dmas = "txq0@%s-q0;rxq0@%s-q1" % (
            self.use_dsa_list[0],
            self.use_dsa_list[0],
        )
        self.nb_cores = 1
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=2"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=True,
            port_options=port_options,
        )

    def test_perf_virtio_pmd_packed_ring_1c_2q_vfio_pci(self):
        """
        Test Case 20: pvp packed ring vhost async test with 1core 2queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 2
        self.dmas = (
            "txq0@%s-q0;"
            "rxq0@%s-q1;"
            "txq1@%s-q2;"
            "rxq1@%s-q3"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        self.nb_cores = 1
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=True,
            port_options=port_options,
        )

    def test_perf_virtio_pmd_packed_ring_2c_2q_vfio_pci(self):
        """
        Test Case 21: pvp packed ring vhost async test with 2core 2queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 2
        self.dmas = (
            "txq0@%s-q0;"
            "rxq0@%s-q1;"
            "txq1@%s-q2;"
            "rxq1@%s-q3"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        self.nb_cores = 2
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=True,
            port_options=port_options,
        )

    def test_perf_virtio_pmd_packed_ring_2c_4q_vfio_pci(self):
        """
        Test Case 22: pvp packed ring vhost async test with 2core 4queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 4
        self.dmas = (
            "txq0@%s-q0;"
            "rxq0@%s-q1;"
            "txq1@%s-q2;"
            "rxq1@%s-q3;"
            "txq2@%s-q4;"
            "rxq2@%s-q5;"
            "txq3@%s-q6;"
            "rxq3@%s-q7"
            % (
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
        self.nb_cores = 2
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=8"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=True,
            port_options=port_options,
        )

    def test_perf_virtio_pmd_packed_ring_4c_4q_vfio_pci(self):
        """
        Test Case 23: pvp packed ring vhost async test with 4core 4queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 4
        self.dmas = (
            "txq0@%s-q0;"
            "rxq0@%s-q1;"
            "txq1@%s-q2;"
            "rxq1@%s-q3;"
            "txq2@%s-q4;"
            "rxq2@%s-q5;"
            "txq3@%s-q6;"
            "rxq3@%s-q7"
            % (
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
        self.nb_cores = 4
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=8"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=True,
            port_options=port_options,
        )

    def test_perf_virtio_pmd_packed_ring_4c_8q_vfio_pci(self):
        """
        Test Case 24: pvp packed ring vhost async test with 4core 8queue using vfio-pci driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.queues = 8
        self.dmas = (
            "txq0@%s-q0;"
            "rxq0@%s-q1;"
            "txq1@%s-q2;"
            "rxq1@%s-q3;"
            "txq2@%s-q4;"
            "rxq2@%s-q5;"
            "txq3@%s-q6;"
            "rxq3@%s-q7"
            % (
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
        self.nb_cores = 4
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        ports.append(self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=8"}
        self.perf_test(
            case_info=self.running_case,
            ports=ports,
            packed=True,
            port_options=port_options,
        )

    def stop_vm_and_quit_testpmd(self):
        self.vm.stop()
        out = self.vhost_user_pmd.execute_cmd("stop")
        self.logger.info(out)
        self.vhost_user_pmd.quit()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.stop_vm_and_quit_testpmd()
        self.DC.reset_all_work_queue()
        self.DC.bind_all_dsa_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)
