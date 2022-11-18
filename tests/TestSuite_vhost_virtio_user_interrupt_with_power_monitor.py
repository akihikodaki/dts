# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

"""
DPDK Test suite.
Virtio-user interrupt need test with l3fwd-power sample
"""

import re
import time

import framework.rst as rst
import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE, UPDATE_EXPECTED, load_global_setting
from framework.test_case import TestCase


class TestVirtioUserInterruptDsa(TestCase):
    def set_up_all(self):
        """
        run at the start of each test suite.
        """
        self.core_config = "1S/4C/1T"
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n["socket"]) == 0])
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(
            self.cores_num >= 4, "There has not enought cores to test this case"
        )
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket
        )
        self.core_list_vhost = self.core_list[0:2]
        self.core_list_l3fwd = self.core_list[2:4]
        self.core_mask_vhost = utils.create_mask(self.core_list_vhost)
        self.core_mask_l3fwd = utils.create_mask(self.core_list_l3fwd)
        self.core_mask_virtio = self.core_mask_l3fwd
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.prepare_l3fwd_power()
        self.app_l3fwd_power_path = self.dut.apps_name["l3fwd-power"]
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.l3fwdpower_name = self.app_l3fwd_power_path.split("/")[-1]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.virtio_user_pmd = PmdOutput(self.dut, self.virtio_user)
        self.l3fwd = self.dut.new_session(suite="l3fwd")
        self.headers_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"]
        self.out_path = "/tmp/%s" % self.suite_name
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        self.pktgen_helper = PacketGeneratorHelper()

    def set_up(self):
        """
        run before each test case.
        """
        self.table_header = ["Frame Size(Byte)", "Mode", "Throughput(Mpps)"]
        self.result_table_create(self.table_header)

        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall %s" % self.l3fwdpower_name, "#")
        self.dut.send_expect("rm -rf vhost-net*", "#")

    def close_all_session(self):
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)
        self.dut.close_session(self.l3fwd)

    def prepare_l3fwd_power(self):
        out = self.dut.build_dpdk_apps("./examples/l3fwd-power")
        self.verify("Error" not in out, "compilation l3fwd-power error")

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def launch_l3fwd_power(self, path, queues=1, packed=False, vhost=False):
        example_para = "./%s " % self.app_l3fwd_power_path
        if not vhost:
            if not packed:
                vdev = "virtio_user0,path=%s,cq=1,queues=%d" % (path, queues)
            else:
                vdev = "virtio_user0,path=%s,cq=1,packed_vq=1,queues=%d" % (
                    path,
                    queues,
                )
        else:
            vdev = "net_vhost0,iface=%s,queues=%d,client=1" % (path, queues)
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list_l3fwd, prefix="l3fwd-pwd", no_pci=True, vdevs=[vdev]
        )
        if self.check_2M_env:
            eal_params += " --single-file-segments"

        config_info = ""
        for queue in range(queues):
            if config_info != "":
                config_info += ","
            config_info += "(%d,%d,%s)" % (0, queue, self.core_list_l3fwd[queue])
        para = " --config='%s' --parse-ptype --pmd-mgmt=monitor" % config_info
        cmd_l3fwd = example_para + eal_params + " --log-level='user1,7' -- -p 1 " + para
        self.l3fwd.get_session_before(timeout=2)
        self.l3fwd.send_expect(cmd_l3fwd, "POWER", 40)
        time.sleep(10)
        out = self.l3fwd.get_session_before()
        if "Error" in out and "Error opening" not in out:
            self.logger.error("Launch l3fwd-power sample error")
        else:
            self.logger.info("Launch l3fwd-power sample finished")

    def launch_virtio_user(self, path="./vhost-net", queues=1, packed=False):
        """
        launch virtio-user with server mode
        """
        vdev = (
            "net_virtio_user0,path=%s,server=1,queues=%d" % (path, queues)
            if not packed
            else "net_virtio_user0,path=%s,server=1,queues=%d,packed_vq=1"
            % (path, queues)
        )
        core_list_virtio = self.core_list_vhost
        eal_params = self.dut.create_eal_parameters(
            cores=core_list_virtio,
            prefix="virtio",
            no_pci=False,
            ports=[self.pci_info],
            vdevs=[vdev],
        )
        if self.check_2M_env:
            eal_params += " --single-file-segments"
        para = " -- -i --rxq=%d --txq=%d --rss-ip" % (queues, queues)
        command_line_client = self.app_testpmd_path + " " + eal_params + para
        self.virtio_user.send_expect(
            command_line_client, "waiting for client connection...", 120
        )

    def get_vhost_port_num(self):
        out = self.vhost_user.send_expect("show port summary all", "testpmd> ", 60)
        port_num = re.search("Number of available ports:\s*(\d*)", out)
        return int(port_num.group(1))

    def get_virtio_port_num(self):
        out = self.virtio_user.send_expect("show port summary all", "testpmd> ", 60)
        port_num = re.search("Number of available ports:\s*(\d*)", out)
        return int(port_num.group(1))

    def check_each_queue_of_port_packets(self, queues, vhost=True):
        """
        check each queue of each port has receive packets
        """
        if vhost:
            out = self.vhost_user_pmd.execute_cmd("stop")
            port_num = self.get_vhost_port_num()
        else:
            out = self.virtio_user_pmd.execute_cmd("stop")
            port_num = self.get_virtio_port_num()
        for port in range(port_num):
            for queue in range(queues):
                if queue > 0:
                    reg = "Port= %d/Queue= %d" % (port, queue)
                else:
                    reg = "Forward statistics for port %d" % port
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

    def send_imix_packets(self):
        """
        Send imix packet with packet generator and verify
        """
        test_result = {}
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
                    ("ether", {"dst": "52:54:00:00:00:01"}),
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
        trans_options = {"delay": 5, "duration": 10}
        bps, pps = self.tester.pktgen.measure_throughput(
            stream_ids=streams, options=trans_options
        )
        Mpps = pps / 1000000.0
        Mbps = bps / 1000000.0
        self.verify(
            Mbps > 0,
            f"{self.running_case} can not receive packets of frame size {frame_sizes}",
        )
        test_result["imix"] = Mpps
        return test_result

    def test_perf_split_ring_virtio_user_interrupt_test_with_vhost_user_as_backend(
        self,
    ):
        """
        Test Case 1: Split ring virtio-user interrupt test with vhost-user as backend
        """
        perf_result = []
        vhost_param = "--rxq=1 --txq=1"
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net,queues=1'"
        ports = [self.dut.ports_info[0]["pci"]]
        self.logger.info(ports)
        self.vhost_user_pmd.start_testpmd(
            cores=self.core_list_vhost,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_user_pmd.execute_cmd("start")
        self.launch_l3fwd_power(path="./vhost-net")
        before_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=1)

        self.logger.info("Stop and restart vhost port")
        self.vhost_user_pmd.execute_cmd("start")
        after_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=1)

        for key in before_restart.keys():
            perf_result.append(["imix", "Before Re-launch vhost", before_restart[key]])
        for key in after_restart.keys():
            perf_result.append(["imix", "After Re-launch vhost", after_restart[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_perf_split_ring_multi_queues_virtio_user_interrupt_test_with_vhost_user_as_backend(
        self,
    ):
        """
        Test Case 2: Split ring multi-queues virtio-user interrupt test with vhost-user as backend
        """
        perf_result = []
        vhost_param = "--rxq=2 --txq=2"
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net,queues=2'"
        ports = [self.dut.ports_info[0]["pci"]]
        self.logger.info(ports)
        self.vhost_user_pmd.start_testpmd(
            cores=self.core_list_vhost,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_user_pmd.execute_cmd("start")
        self.launch_l3fwd_power(path="./vhost-net", queues=2)
        before_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=2)

        self.logger.info("Stop and restart vhost port")
        self.vhost_user_pmd.execute_cmd("start")
        after_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=2)

        for key in before_restart.keys():
            perf_result.append(["imix", "Before Re-start vhost", before_restart[key]])
        for key in after_restart.keys():
            perf_result.append(["imix", "After Re-start vhost", after_restart[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_perf_wake_up_split_ring_vhost_user_core_with_l3fwd_power_sample(
        self,
    ):
        """
        Test Case 3:Wake up split ring vhost-user core with l3fwd-power sample
        """
        perf_result = []
        self.launch_virtio_user(path="./vhost-net")
        self.launch_l3fwd_power(path="./vhost-net", vhost=True)
        self.virtio_user_pmd.execute_cmd("start")
        before_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=1, vhost=False)

        self.logger.info("Stop and restart virtio-user")
        self.virtio_user_pmd.execute_cmd("start")
        after_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=1, vhost=False)

        for key in before_restart.keys():
            perf_result.append(["imix", "Before Re-start vhost", before_restart[key]])
        for key in after_restart.keys():
            perf_result.append(["imix", "After Re-start vhost", after_restart[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_perf_wake_up_split_ring_multi_queues_vhost_user_core_with_l3fwd_power_sample(
        self,
    ):
        """
        Test Case 4:Wake up split ring multi-queues vhost-user core with l3fwd-power sample
        """
        perf_result = []
        self.launch_virtio_user(queues=2, path="./vhost-net")
        self.launch_l3fwd_power(queues=2, path="./vhost-net", vhost=True)
        self.virtio_user_pmd.execute_cmd("start")
        before_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=2, vhost=False)

        self.logger.info("Stop and restart virtio-user")
        self.virtio_user_pmd.execute_cmd("start")
        after_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=2, vhost=False)

        for key in before_restart.keys():
            perf_result.append(["imix", "Before Re-start vhost", before_restart[key]])
        for key in after_restart.keys():
            perf_result.append(["imix", "After Re-start vhost", after_restart[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_perf_packed_ring_virtio_user_interrupt_test_with_vhost_user_as_backend(
        self,
    ):
        """
        Test Case 5: Packed ring virtio-user interrupt test with vhost-user as backend
        """
        perf_result = []
        vhost_param = "--rxq=1 --txq=1"
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net,queues=1'"
        ports = [self.dut.ports_info[0]["pci"]]
        self.logger.info(ports)
        self.vhost_user_pmd.start_testpmd(
            cores=self.core_list_vhost,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_user_pmd.execute_cmd("start")
        self.launch_l3fwd_power(path="./vhost-net", packed=True)
        before_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=1)

        self.logger.info("Stop and restart vhost port")
        self.vhost_user_pmd.execute_cmd("start")
        after_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=1)

        for key in before_restart.keys():
            perf_result.append(["imix", "Before Re-launch vhost", before_restart[key]])
        for key in after_restart.keys():
            perf_result.append(["imix", "After Re-launch vhost", after_restart[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_perf_packed_ring_multi_queues_virtio_user_interrupt_test_with_vhost_user_as_backend(
        self,
    ):
        """
        Test Case 6: Packed ring multi-queues virtio-user interrupt test with vhost-user as backend
        """
        perf_result = []
        vhost_param = "--rxq=2 --txq=2"
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net,queues=2'"
        ports = [self.dut.ports_info[0]["pci"]]
        self.logger.info(ports)
        self.vhost_user_pmd.start_testpmd(
            cores=self.core_list_vhost,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_user_pmd.execute_cmd("start")
        self.launch_l3fwd_power(path="./vhost-net", queues=2, packed=True)
        before_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=2)

        self.logger.info("Stop and restart vhost port")
        self.vhost_user_pmd.execute_cmd("start")
        after_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=2)

        for key in before_restart.keys():
            perf_result.append(["imix", "Before Re-start vhost", before_restart[key]])
        for key in after_restart.keys():
            perf_result.append(["imix", "After Re-start vhost", after_restart[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_perf_wake_up_packed_ring_vhost_user_core_with_l3fwd_power_sample(
        self,
    ):
        """
        Test Case 7:Wake up packed ring vhost-user core with l3fwd-power sample
        """
        perf_result = []
        self.launch_virtio_user(path="./vhost-net", packed=True)
        self.launch_l3fwd_power(path="./vhost-net", vhost=True)
        self.virtio_user_pmd.execute_cmd("start")
        before_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=1, vhost=False)

        self.logger.info("Stop and restart virtio-user")
        self.virtio_user_pmd.execute_cmd("start")
        after_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=1, vhost=False)

        for key in before_restart.keys():
            perf_result.append(["imix", "Before Re-start vhost", before_restart[key]])
        for key in after_restart.keys():
            perf_result.append(["imix", "After Re-start vhost", after_restart[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_perf_wake_up_packed_ring_multi_queues_vhost_user_core_with_l3fwd_power_sample(
        self,
    ):
        """
        Test Case 8:Wake up packed ring multi-queues vhost-user core with l3fwd-power sample
        """
        perf_result = []
        self.launch_virtio_user(queues=2, path="./vhost-net", packed=True)
        self.launch_l3fwd_power(queues=2, path="./vhost-net", vhost=True)
        self.virtio_user_pmd.execute_cmd("start")
        before_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=2, vhost=False)

        self.logger.info("Stop and restart virtio-user")
        self.virtio_user_pmd.execute_cmd("start")
        after_restart = self.send_imix_packets()
        self.check_each_queue_of_port_packets(queues=2, vhost=False)

        for key in before_restart.keys():
            perf_result.append(["imix", "Before Re-start vhost", before_restart[key]])
        for key in after_restart.keys():
            perf_result.append(["imix", "After Re-start vhost", after_restart[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def tear_down(self):
        """
        run after each test case.
        """
        self.dut.send_expect("killall %s" % self.l3fwdpower_name, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")

    def tear_down_all(self):
        """
        run after each test suite.
        """
        self.close_all_session()
