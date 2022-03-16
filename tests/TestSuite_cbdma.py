# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation. All rights reserved.
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
"""

import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import TRANSMIT_CONT
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestCBDMA(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.frame_sizes = [64, 256, 512, 1024, 1518]
        self.cbdma_dev_infos = []
        self.device_str = None
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.get_cbdma_ports_info_and_bind_to_dpdk()
        # default --proc-type=primary, case 1-6 use default values, case7 use --proc-type=secondary
        self.cbdma_proc = "--proc-type=primary"
        # default v_dev is None, case 1-6 use default None values, case7 use --vdev net_null_0
        self.v_dev = ""
        out = self.dut.build_dpdk_apps("./examples/dma")
        self.dma_path = self.dut.apps_name["dma"]
        self.verify("Error" not in out, "compilation dma error")

    def set_up(self):
        """
        Run before each test case.
        """
        # Prepare the result table
        self.table_header = ["Frame"]
        self.table_header.append("Mpps")
        self.table_header.append("Thread Num")
        self.table_header.append("Queue Num")
        self.table_header.append("Copy Mode")
        self.table_header.append("Updating MAC")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)
        self.send_session = self.dut.new_session("new_session")

    def get_core_list(self):
        """
        get cores list depend on thread_num
        """
        core_config = "1S/%dC/1T" % self.cbdma_cores_num
        self.core_list = self.dut.get_core_list(core_config, socket=self.ports_socket)
        self.verify(
            len(self.core_list) >= self.cbdma_cores_num,
            "There no enough cores to run this case",
        )

    def get_cbdma_ports_info_and_bind_to_dpdk(self):
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
                # the numa id of dma dev, only add the device which
                # on same socket with nic dev
                bus = int(dev_info[5:7], base=16)
                if bus >= 128:
                    cur_socket = 1
                else:
                    cur_socket = 0
                if self.ports_socket == cur_socket:
                    self.cbdma_dev_infos.append(pci_info.group(1))
        self.verify(
            len(self.cbdma_dev_infos) >= 8,
            "There no enough cbdma device to run this suite",
        )
        self.device_str = " ".join(self.cbdma_dev_infos[0:8])
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

    def get_ports_info(self):
        dev_info = []
        for i in range(self.cbdma_nic_dev_num):
            dev_info.append(self.dut.ports_info[i]["pci"])
        for i in range(self.cbdma_dma_dev_num):
            dev_info.append(self.cbdma_dev_infos[i])
        return dev_info

    def launch_dma_app(self, eal_params, session=None):
        """
        launch dma with different params
        """
        port_info = 0
        for i in range(self.cbdma_nic_dev_num):
            port_info |= 1 << i

        mac_info = ""
        if self.cbdma_updating_mac == "disable":
            mac_info = "--no-mac-updating"
        elif self.cbdma_updating_mac == "enable":
            mac_info = "--mac-updating"
        """
        when start cbdma app, default cores num is 2, it will only one thread
        when the cores num > 2, there will have 2 thread, and the max value of thread
        num is 2
        """
        if session is None:
            session = self.send_session
        expected = self.dma_path.split("/")[-1].strip()
        self.logger.info("expected: {}".format(expected))
        cmd_command = "%s %s %s %s -- -p %s -q %d %s -c %s" % (
            self.dma_path,
            eal_params,
            self.cbdma_proc,
            self.v_dev,
            hex(port_info),
            self.cbdma_dma_dev_num / self.cbdma_nic_dev_num,
            mac_info,
            self.cbdma_copy_mode,
        )
        out = session.send_expect(cmd_command, expected)
        time.sleep(1)
        out = session.get_session_before(timeout=1)
        self.logger.info("out before: {}".format(out))
        thread_num = 2 if self.cbdma_cores_num > 2 else 1
        o_thread_info = "Worker Threads = %d" % thread_num
        o_copy_info = "Copy Mode = %s" % self.cbdma_copy_mode
        o_update_mac = "Updating MAC = %s" % self.cbdma_updating_mac
        o_queue_info = "Rx Queues = %d" % (
            self.cbdma_dma_dev_num / self.cbdma_nic_dev_num
        )
        self.verify(
            o_thread_info in out
            and o_copy_info in out
            and o_update_mac in out
            and o_queue_info in out,
            "The output info not match setting for the cmd, please check",
        )

    def config_stream(self, frame_size):
        stream_ids = []
        for port in range(self.cbdma_nic_dev_num):
            tx_port = self.tester.get_local_port(self.dut_ports[port])
            rx_port = tx_port
            if self.cbdma_nic_dev_num > 1:
                if port % self.cbdma_nic_dev_num == 0:
                    rx_port = self.tester.get_local_port(self.dut_ports[port + 1])
                else:
                    rx_port = self.tester.get_local_port(self.dut_ports[port - 1])
            dst_mac = self.dut.get_mac_address(self.dut_ports[port])
            # pkt config
            pkt = Packet(pkt_type="UDP", pkt_len=frame_size)
            pkt.config_layer("ether", {"dst": "%s" % dst_mac})
            pkt.config_layer("udp", {"src": 1111, "dst": 1112})
            pkt.save_pcapfile(
                self.tester, "%s/cbdma_%d.pcap" % (self.tester.tmp_file, port)
            )
            stream_option = {
                "pcap": "%s/cbdma_%d.pcap" % (self.tester.tmp_file, port),
                "fields_config": {
                    "ip": {
                        "src": {
                            "action": "random",
                            "start": "16.0.0.1",
                            "step": 1,
                            "end": "16.0.0.64",
                        }
                    }
                },
                "stream_config": {
                    "rate": 100,
                    "transmit_mode": TRANSMIT_CONT,
                },
            }
            stream_id = self.tester.pktgen.add_stream(
                tx_port, tx_port, "%s/cbdma_%d.pcap" % (self.tester.tmp_file, port)
            )
            self.tester.pktgen.config_stream(stream_id, stream_option)
            stream_ids.append(stream_id)
        return stream_ids

    def send_and_verify_throughput(self, check_channel=False):
        """
        Send packet with packet generator and verify
        """
        for frame_size in self.frame_sizes:
            self.tester.pktgen.clear_streams()
            stream_ids = self.config_stream(frame_size)
            traffic_opt = {"method": "throughput", "rate": 100, "duration": 20}
            _, pps = self.tester.pktgen.measure(stream_ids, traffic_opt)
            self.verify(
                pps > 0,
                "%s can not receive packets of frame size %d"
                % (self.running_case, frame_size),
            )
            self.update_result_tables(frame_size, pps)
            if check_channel:
                self.check_enqueue_packets_of_each_channel()

    def check_enqueue_packets_of_each_channel(self):
        """
        Check stats of dma app, each dma channel can enqueue packets
        """
        out = self.send_session.get_session_before(timeout=2)
        index = out.rfind("Statistics for port 0")
        out = out[index:]
        data_info = re.findall("Total completed ops:\s*(\d*)", out)
        self.verify(
            (len(data_info) - 1) == self.cbdma_dma_dev_num,
            "There miss some queue, the run queue is "
            "%d, and expect queue num is %d"
            % ((len(data_info) - 1), self.cbdma_dma_dev_num),
        )
        for index in range(self.cbdma_dma_dev_num):
            self.verify(
                data_info[index] != 0, "the queue %d can not enqueues data" % index
            )

    def update_result_tables(self, frame_size, pps):
        Mpps = pps / 1000000.0
        throughput = (
            Mpps
            * 100
            / float(self.wirespeed(self.nic, frame_size, self.cbdma_nic_dev_num))
        )
        thread_num = 2 if self.cbdma_cores_num > 2 else 1
        results_row = [frame_size]
        results_row.append(Mpps)
        results_row.append(thread_num)
        results_row.append(self.cbdma_dma_dev_num / self.cbdma_nic_dev_num)
        results_row.append(self.cbdma_copy_mode)
        results_row.append(self.cbdma_updating_mac)
        results_row.append(throughput)
        self.result_table_add(results_row)

    def test_perf_cbdma_basic_test(self):
        """
        CMDBMA basic test with differnet size packets
        one cbdma port and one nic port with 1 queue 1 thread
        """
        self.cbdma_cores_num = 2
        self.cbdma_nic_dev_num = 1
        self.cbdma_dma_dev_num = 1
        self.cbdma_updating_mac = "enable"
        self.cbdma_copy_mode = "hw"
        self.get_core_list()
        dev_info = self.get_ports_info()
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list, ports=dev_info, prefix="cbdma"
        )
        self.launch_dma_app(eal_params)
        self.send_and_verify_throughput(check_channel=True)
        self.result_table_print()

    def test_perf_cbdma_with_multi_thread(self):
        """
        CBDMA test with multi-thread
        one cbdma port and on nic port with 1 queue 2 thread
        """
        self.cbdma_cores_num = 3
        self.cbdma_nic_dev_num = 1
        self.cbdma_dma_dev_num = 1
        self.cbdma_updating_mac = "enable"
        self.cbdma_copy_mode = "hw"
        self.get_core_list()
        dev_info = self.get_ports_info()
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list, ports=dev_info, prefix="cbdma"
        )
        self.launch_dma_app(eal_params)
        self.send_and_verify_throughput(check_channel=True)
        self.result_table_print()

    def test_perf_cbdma_with_multi_nic_ports(self):
        """
        CBDMA test with multi nic ports
        two cbdma port and two nic port with 1 queue 1 thread
        """
        self.cbdma_cores_num = 5
        self.cbdma_nic_dev_num = 2
        self.cbdma_dma_dev_num = 2
        self.cbdma_updating_mac = "enable"
        self.cbdma_copy_mode = "hw"
        self.get_core_list()
        dev_info = self.get_ports_info()
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list, ports=dev_info, prefix="cbdma"
        )
        self.launch_dma_app(eal_params)
        self.send_and_verify_throughput(check_channel=True)
        self.result_table_print()

    def test_perf_cbdma_with_multi_queues(self):
        """
        CBDMA test with multi queues
        one nic port and 2/4/8 cbdma port with 2 thread
        """
        self.cbdma_cores_num = 3
        self.cbdma_nic_dev_num = 1
        self.cbdma_updating_mac = "enable"
        self.cbdma_copy_mode = "hw"
        queue_num_list = [2, 4, 8]
        self.get_core_list()
        for queue_num in queue_num_list:
            self.cbdma_dma_dev_num = queue_num
            dev_info = self.get_ports_info()
            eal_params = self.dut.create_eal_parameters(
                cores=self.core_list, ports=dev_info, prefix="cbdma"
            )
            self.launch_dma_app(eal_params)
            self.send_and_verify_throughput(check_channel=True)
            self.send_session.send_expect("^c", "# ")
        self.result_table_print()

    def test_perf_cbdma_with_diff_update_mac(self):
        """
        CBDMA performance cmparison between mac-updating and no-mac-updating
        2 cbdma port and 1 nic port with 2 queue 1 thread
        """
        self.cbdma_cores_num = 2
        self.cbdma_nic_dev_num = 1
        self.cbdma_dma_dev_num = 2
        self.cbdma_updating_mac = "enable"
        self.cbdma_copy_mode = "hw"
        self.get_core_list()
        dev_info = self.get_ports_info()
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list, ports=dev_info, prefix="cbdma"
        )
        self.launch_dma_app(eal_params)
        self.send_and_verify_throughput(check_channel=True)
        self.send_session.send_expect("^c", "# ")
        self.cbdma_updating_mac = "disable"
        self.launch_dma_app(eal_params)
        self.send_and_verify_throughput(check_channel=True)
        self.result_table_print()

    def test_perf_cbdma_with_diff_copy_mode(self):
        """
        CBDMA performance cmparison between hardware copies and software copies
        4 cbdma port and 1 nic port with 4 queue 2 thread
        """
        self.cbdma_cores_num = 3
        self.cbdma_nic_dev_num = 1
        self.cbdma_dma_dev_num = 4
        self.cbdma_updating_mac = "enable"
        self.cbdma_copy_mode = "hw"
        self.get_core_list()
        dev_info = self.get_ports_info()
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list, ports=dev_info, prefix="cbdma"
        )
        self.launch_dma_app(eal_params)
        self.send_and_verify_throughput(check_channel=False)
        self.send_session.send_expect("^c", "# ")
        self.cbdma_copy_mode = "sw"
        self.launch_dma_app(eal_params)
        self.send_and_verify_throughput(check_channel=False)
        self.result_table_print()

    def test_multi_app_mode(self):
        """
        CBDMA multi app tests for the simultanous exection of primary
        and secondary app
        """
        self.cbdma_cores_num = 3
        self.cbdma_nic_dev_num = 1
        self.cbdma_dma_dev_num = 4
        self.cbdma_updating_mac = "disable"
        self.cbdma_copy_mode = "hw"
        self.v_dev = "--vdev net_null_0"
        dev_info = self.get_ports_info()
        dev_info.pop(0)
        self.get_core_list()
        self.pmdout = PmdOutput(self.dut)
        self.pmdout.start_testpmd(
            cores="", eal_param="--vdev net_null_0 --proc-type=primary", ports=dev_info
        )
        self.pmdout.execute_cmd("port stop all")
        self.cbdma_proc = "--proc-type=secondary"
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list, ports=dev_info
        )
        self.launch_dma_app(eal_params)
        self.send_session.send_expect("^C", "#")
        self.pmdout.execute_cmd("^C")
        self.result_table_print()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.send_session.send_expect("^c", "# ")
        self.dut.close_session(self.send_session)
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.bind_cbdma_device_to_kernel()
