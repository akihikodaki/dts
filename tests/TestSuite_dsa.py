# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2023 Intel Corporation
#

import re
import time

from framework.packet import Packet
from framework.pktgen import TRANSMIT_CONT
from framework.test_case import TestCase

from .virtio_common import dsa_common as DC


class TestDSA(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.frame_sizes = [64, 256, 512, 1024, 1518]
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        out = self.dut.build_dpdk_apps("./examples/dma")
        self.verify("Error" not in out, "compilation dma error")
        self.dma_path = self.dut.apps_name["dma"]
        self.dma_name = self.dma_path.split("/")[-1]
        self.core_num = 1
        self.DC = DC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        # Prepare the result table
        self.table_header = ["Frame"]
        self.table_header.append("Mpps")
        self.table_header.append("Worker Threads")
        self.table_header.append("Copy Mode")
        self.table_header.append("Updating MAC")
        self.table_header.append("Rx Queues")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)
        self.dut.send_expect("killall -I %s" % self.dma_name, "#", 20)

    def get_core_list(self):
        """
        get cores list depend on self.work_thread
        """
        core_config = "1S/%dC/1T" % self.core_num
        core_list = self.dut.get_core_list(core_config, socket=self.ports_socket)
        return core_list

    def launch_dma_app(self, eal_params):
        """
        launch dma with different params
        """
        port_info = 0
        for i in range(self.nic_port_num):
            port_info |= 1 << i
        updating_mac = (
            "--mac-updating" if self.updating_mac == "enabled" else "--no-mac-updating"
        )
        rx_queues = self.rx_queues / self.nic_port_num
        cmd = "%s %s -- -p %s -q %d %s -c %s" % (
            self.dma_path,
            eal_params,
            hex(port_info),
            rx_queues,
            updating_mac,
            self.copy_mode,
        )
        expected = self.dma_path.split("/")[-1].strip()
        self.dut.send_expect(cmd, expected)
        time.sleep(3)
        out = self.dut.get_session_output(timeout=1)
        self.logger.info("out before: {}".format(out))
        """
        when start DSA app, default cores num is 2, it will only one thread
        when the cores num > 2, there will have 2 thread, and the max value of thread
        num is 2.
        """
        self.work_thread = 2 if self.core_num > 2 else 1
        work_thread_info = "Worker Threads = %d" % self.work_thread
        copy_mode_info = "Copy Mode = %s" % self.copy_mode
        update_mac_info = "Updating MAC = %s" % self.updating_mac
        rx_queues_info = "Rx Queues = %d" % rx_queues
        self.verify(
            work_thread_info in out
            and copy_mode_info in out
            and update_mac_info in out
            and rx_queues_info in out,
            "The output info not match setting for the cmd, please check",
        )

    def config_stream(self, frame_size):
        stream_ids = []
        for port in range(self.nic_port_num):
            tx_port = self.tester.get_local_port(self.dut_ports[port])
            rx_port = tx_port
            if self.nic_port_num > 1:
                if port % self.nic_port_num == 0:
                    rx_port = self.tester.get_local_port(self.dut_ports[port + 1])
                else:
                    rx_port = self.tester.get_local_port(self.dut_ports[port - 1])
            dst_mac = self.dut.get_mac_address(self.dut_ports[port])
            # pkt config
            pkt = Packet(pkt_type="UDP", pkt_len=frame_size)
            # pkt.config_layer("ether", {"dst": "%s" % dst_mac})
            pkt.config_layer("udp", {"src": 1111, "dst": 1112})
            pkt.save_pcapfile(
                self.tester, "%s/dsa_%d.pcap" % (self.tester.tmp_file, port)
            )
            stream_option = {
                "pcap": "%s/dsa_%d.pcap" % (self.tester.tmp_file, port),
                "fields_config": {
                    "ether": {
                        "dst": {
                            "action": "random",
                        }
                    },
                    "ip": {
                        "src": {
                            "action": "random",
                            "start": "16.0.0.1",
                            "step": 1,
                            "end": "16.0.0.64",
                        }
                    },
                },
                "stream_config": {
                    "rate": 100,
                    "transmit_mode": TRANSMIT_CONT,
                },
            }
            stream_id = self.tester.pktgen.add_stream(
                tx_port, tx_port, "%s/dsa_%d.pcap" % (self.tester.tmp_file, port)
            )
            self.tester.pktgen.config_stream(stream_id, stream_option)
            stream_ids.append(stream_id)
        return stream_ids

    def send_and_verify(self, check_each_queue=True):
        """
        Send packet with packet generator and verify
        """
        for frame_size in self.frame_sizes:
            self.tester.pktgen.clear_streams()
            stream_ids = self.config_stream(frame_size)
            traffic_opt = {"method": "throughput", "rate": 100, "duration": 20}
            self.logger.info(
                "start to send %d frame size packets from pktgen" % frame_size
            )
            _, pps = self.tester.pktgen.measure(stream_ids, traffic_opt)
            self.verify(
                pps > 0,
                "%s can not receive packets of frame size %d"
                % (self.running_case, frame_size),
            )
            self.update_result_tables(frame_size, pps)
            if check_each_queue:
                self.check_enqueue_packets_of_each_channel()

    def check_enqueue_packets_of_each_channel(self):
        """
        Check stats of dma app, each dma channel can enqueue packets
        """
        out = self.dut.get_session_output(timeout=2)
        index = out.rfind("Statistics for port 0")
        out = out[index:]
        data_info = re.findall("Total completed ops:\s*(\d*)", out)
        self.verify(
            (len(data_info) - 1) == self.rx_queues,
            "There miss some queue, the run queue is "
            "%d, and expect queue num is %d" % ((len(data_info) - 1), self.rx_queues),
        )
        for index in range(self.rx_queues):
            self.verify(
                data_info[index] != 0, "the queue %d can not enqueues data" % index
            )

    def update_result_tables(self, frame_size, pps):
        Mpps = pps / 1000000.0
        linerate = (
            Mpps * 100 / float(self.wirespeed(self.nic, frame_size, self.nic_port_num))
        )
        self.work_thread = 2 if self.core_num > 2 else 1
        results_row = [frame_size]
        results_row.append(Mpps)
        results_row.append(self.work_thread)
        results_row.append(self.copy_mode)
        results_row.append(self.updating_mac)
        results_row.append(self.rx_queues / self.nic_port_num)
        results_row.append(linerate)
        self.result_table_add(results_row)

    def test_perf_dsa_basic_test_using_dpdk_driver(self):
        """
        Test Case 1: DMA basic test with differnet size packets using DSA dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.core_num = 2
        self.rx_queues = 1
        self.nic_port_num = 1
        self.updating_mac = "enabled"
        self.copy_mode = "hw"
        ports = dsas
        for i in range(self.nic_port_num):
            ports.append(self.dut.ports_info[i]["pci"])
        port_options = {dsas[0]: "max_queues=%s" % self.rx_queues}
        eal_params = self.dut.create_eal_parameters(
            cores=self.get_core_list(), ports=ports, port_options=port_options
        )
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)
        self.result_table_print()

    def test_perf_dsa_with_multi_threads_using_dpdk_driver(self):
        """
        Test Case 2: DMA test with multi-threads using DSA dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.core_num = 3
        self.rx_queues = 1
        self.nic_port_num = 1
        self.updating_mac = "enabled"
        self.copy_mode = "hw"
        ports = dsas
        for i in range(self.nic_port_num):
            ports.append(self.dut.ports_info[i]["pci"])
        port_options = {dsas[0]: "max_queues=%s" % self.rx_queues}
        eal_params = self.dut.create_eal_parameters(
            cores=self.get_core_list(), ports=ports, port_options=port_options
        )
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)
        self.result_table_print()

    def test_perf_dsa_with_multi_nic_ports_using_dpdk_driver(self):
        """
        Test Case 3: DMA test with multi nic ports using DSA dpdk driver
        """
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for testing")
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.core_num = 5
        self.rx_queues = 2
        self.nic_port_num = 2
        self.updating_mac = "enabled"
        self.copy_mode = "hw"
        ports = dsas
        for i in range(self.nic_port_num):
            ports.append(self.dut.ports_info[i]["pci"])
        port_options = {dsas[0]: "max_queues=%s" % self.rx_queues}
        eal_params = self.dut.create_eal_parameters(
            cores=self.get_core_list(), ports=ports, port_options=port_options
        )
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)
        self.result_table_print()

    def test_perf_dsa_with_multi_queues_using_dpdk_driver(self):
        """
        Test Case 4: DMA test with multi-queues using DSA dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.core_num = 3
        self.nic_port_num = 1
        self.updating_mac = "enabled"
        self.copy_mode = "hw"
        queue_list = [2, 4, 8]
        ports = dsas
        for i in range(self.nic_port_num):
            ports.append(self.dut.ports_info[i]["pci"])
        for self.rx_queues in queue_list:
            port_options = {dsas[0]: "max_queues=%s" % self.rx_queues}
            eal_params = self.dut.create_eal_parameters(
                cores=self.get_core_list(), ports=ports, port_options=port_options
            )
            self.launch_dma_app(eal_params=eal_params)
            self.send_and_verify(check_each_queue=True)
            self.dut.send_expect("^c", "# ")
        self.result_table_print()

    def test_perf_dsa_with_diff_update_mac_using_dpdk_driver(self):
        """
        Test Case 5: DMA performance comparison between mac-updating and no-mac-updating using DSA dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.core_num = 2
        self.rx_queues = 2
        self.nic_port_num = 1
        self.updating_mac = "disabled"
        self.copy_mode = "hw"
        ports = dsas
        for i in range(self.nic_port_num):
            ports.append(self.dut.ports_info[i]["pci"])
        port_options = {dsas[0]: "max_queues=%s" % self.rx_queues}
        eal_params = self.dut.create_eal_parameters(
            cores=self.get_core_list(), ports=ports, port_options=port_options
        )
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)

        self.dut.send_expect("^c", "# ")
        self.updating_mac = "enabled"
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)
        self.result_table_print()

    def test_perf_dsa_with_diff_copy_mode_using_dpdk_driver(self):
        """
        Test Case 6: DMA performance comparison between SW copies and HW copies using DSA dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        self.core_num = 3
        self.rx_queues = 4
        self.nic_port_num = 1
        self.updating_mac = "enabled"
        self.copy_mode = "sw"
        ports = dsas
        for i in range(self.nic_port_num):
            ports.append(self.dut.ports_info[i]["pci"])
        port_options = {dsas[0]: "max_queues=%s" % self.rx_queues}
        eal_params = self.dut.create_eal_parameters(
            cores=self.get_core_list(), ports=ports, port_options=port_options
        )
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=False)

        self.dut.send_expect("^c", "# ")
        self.copy_mode = "hw"
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)
        self.result_table_print()

    def test_perf_dsa_basic_test_using_kernel_driver(self):
        """
        Test Case 7: DMA basic test with differnet size packets using DSA kernel driver
        """
        self.DC.create_wq(wq_num=1, dsa_idxs=[0])
        self.core_num = 2
        self.rx_queues = 1
        self.nic_port_num = 1
        self.updating_mac = "enabled"
        self.copy_mode = "hw"
        ports = [self.dut.ports_info[0]["pci"]]
        eal_params = self.dut.create_eal_parameters(
            cores=self.get_core_list(), ports=ports
        )
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)
        self.result_table_print()

    def test_perf_dsa_with_multi_thread_using_kernel_driver(self):
        """
        Test Case 8: DMA test with multi-threads using DSA kernel driver
        """
        self.DC.create_wq(wq_num=1, dsa_idxs=[0])
        self.core_num = 3
        self.rx_queues = 1
        self.nic_port_num = 1
        self.updating_mac = "enabled"
        self.copy_mode = "hw"
        ports = [self.dut.ports_info[0]["pci"]]
        eal_params = self.dut.create_eal_parameters(
            cores=self.get_core_list(), ports=ports
        )
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)
        self.result_table_print()

    def test_perf_dsa_with_multi_nic_ports_using_kernle_driver(self):
        """
        Test Case 9: DMA test with multi nic ports using DSA kernel driver
        """
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for testing")
        self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        self.core_num = 5
        self.rx_queues = 2
        self.nic_port_num = 2
        self.updating_mac = "enabled"
        self.copy_mode = "hw"
        ports = [self.dut.ports_info[0]["pci"], self.dut.ports_info[1]["pci"]]
        eal_params = self.dut.create_eal_parameters(
            cores=self.get_core_list(), ports=ports
        )
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)
        self.result_table_print()

    def test_perf_dsa_with_multi_queues_using_kernel_driver(self):
        """
        Test Case 10: DMA test with multi-queues using DSA kernel driver
        """
        self.DC.create_wq(wq_num=8, dsa_idxs=[0])
        self.core_num = 3
        self.nic_port_num = 1
        self.updating_mac = "enabled"
        self.copy_mode = "hw"
        queue_list = [2, 4, 8]
        for self.rx_queues in queue_list:
            ports = [self.dut.ports_info[0]["pci"]]
            eal_params = self.dut.create_eal_parameters(
                cores=self.get_core_list(), ports=ports
            )
            self.launch_dma_app(eal_params=eal_params)
            self.send_and_verify(check_each_queue=True)
            self.dut.send_expect("^c", "# ")
        self.result_table_print()

    def test_perf_dsa_with_diff_update_mac_using_kernel_driver(self):
        """
        Test Case 11: DMA performance comparison between mac-updating and no-mac-updating using DSA kernel driver
        """
        self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        self.core_num = 2
        self.rx_queues = 2
        self.nic_port_num = 1
        self.updating_mac = "disabled"
        self.copy_mode = "hw"
        ports = [self.dut.ports_info[0]["pci"]]
        eal_params = self.dut.create_eal_parameters(
            cores=self.get_core_list(), ports=ports
        )
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)

        self.dut.send_expect("^c", "# ")
        self.updating_mac = "enabled"
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)
        self.result_table_print()

    def test_perf_dsa_with_diff_copy_mode_using_kernel_driver(self):
        """
        Test Case 12: DMA performance comparison between SW copies and HW copies using DSA kernel driver
        """
        self.DC.create_wq(wq_num=4, dsa_idxs=[0])
        self.core_num = 3
        self.rx_queues = 4
        self.nic_port_num = 1
        self.updating_mac = "enabled"
        self.copy_mode = "sw"
        ports = [self.dut.ports_info[0]["pci"]]
        eal_params = self.dut.create_eal_parameters(
            cores=self.get_core_list(), ports=ports
        )
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=False)

        self.dut.send_expect("^c", "# ")
        self.copy_mode = "hw"
        self.launch_dma_app(eal_params=eal_params)
        self.send_and_verify(check_each_queue=True)
        self.result_table_print()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("^c", "# ")
        self.dut.send_expect("killall -I %s" % self.dma_name, "#", 20)
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
