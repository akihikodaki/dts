# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

from copy import deepcopy

from framework.pktgen import PacketGeneratorHelper
from framework.settings import HEADER_SIZE, UPDATE_EXPECTED, load_global_setting
from framework.test_case import TestCase


class TestPVPVirtioWith2MHugepages(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        hugepages_size = self.dut.send_expect(
            "awk '/Hugepagesize/ {print $2}' /proc/meminfo", "# "
        )
        self.verify(
            int(hugepages_size) == 2048, "Please config you hugepages_size to 2048"
        )
        self.core_config = "1S/4C/1T"
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket
        )
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(
            len(self.core_list) >= 4,
            "There has not enought cores to test this suite %s" % self.suite_name,
        )

        self.core_list_virtio_user = self.core_list[0:2]
        self.core_list_vhost_user = self.core_list[2:4]
        self.nb_ports = 1
        self.gap = self.get_suite_cfg()["accepted_tolerance"]
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.header_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"] + HEADER_SIZE["tcp"]
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.logger.info(
            "You can config packet_size in file %s.cfg," % self.suite_name
            + " in region 'suite' like packet_sizes=[64, 128, 256]"
        )
        if "packet_sizes" in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()["packet_sizes"]
        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.number_of_ports = 1
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf ./vhost-net*", "# ")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.throughput = dict()
        self.test_result = dict()
        # Prepare the result table
        self.table_header = ["Frame"]
        self.table_header.append("Mpps")
        self.table_header.append("% linerate")

    def perf_test(self):
        """
        Send packet with packet generator
        """
        self.result_table_create(self.table_header)
        self.throughput = {}
        for frame_size in self.frame_sizes:
            payload_size = frame_size - self.header_size
            tgen_input = []
            rx_port = self.tester.get_local_port(self.dut_ports[0])
            tx_port = self.tester.get_local_port(self.dut_ports[0])
            self.tester.scapy_append(
                'wrpcap("%s/vhost.pcap", [Ether(dst="%s")/IP()/TCP()/("X"*%d)])'
                % (self.out_path, self.dst_mac, payload_size)
            )
            tgen_input.append((tx_port, rx_port, "%s/vhost.pcap" % self.out_path))

            self.tester.scapy_execute()
            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(
                tgen_input, 100, None, self.tester.pktgen
            )
            # set traffic option
            traffic_opt = {
                "delay": 5,
                "duration": self.get_suite_cfg()["test_duration"],
            }
            _, pps = self.tester.pktgen.measure_throughput(
                stream_ids=streams, options=traffic_opt
            )
            Mpps = pps / 1000000.0
            line_rate = (
                Mpps * 100 / float(self.wirespeed(self.nic, frame_size, self.nb_ports))
            )
            self.throughput[frame_size] = Mpps
            results_row = [frame_size]
            results_row.append(Mpps)
            results_row.append(line_rate)
            self.result_table_add(results_row)
        self.result_table_print()

    def handle_expected(self):
        """
        Update expected numbers to configurate file: $DTS_CFG_FOLDER/$suite_name.cfg
        """
        if load_global_setting(UPDATE_EXPECTED) == "yes":
            for frame_size in self.frame_sizes:
                self.expected_throughput[frame_size] = round(
                    self.throughput[frame_size], 3
                )

    def handle_results(self):
        """
        results handled process:
        1, save to self.test_results
        2, create test results table
        """
        # save test results to self.test_result
        header = self.table_header
        header.append("Expected Throughput(Mpps)")
        header.append("Status")
        self.result_table_create(self.table_header)
        for frame_size in self.frame_sizes:
            wirespeed = self.wirespeed(self.nic, frame_size, self.nb_ports)
            ret_data = {}
            ret_data[header[0]] = str(frame_size)
            _real = float(self.throughput[frame_size])
            _exp = float(self.expected_throughput[frame_size])
            ret_data[header[1]] = "{:.3f}".format(_real)
            ret_data[header[2]] = "{:.3f}%".format(_real * 100 / wirespeed)
            ret_data[header[3]] = "{:.3f}".format(_exp)
            gap = _exp * -self.gap * 0.01
            if _real > _exp + gap:
                ret_data[header[4]] = "PASS"
            else:
                ret_data[header[4]] = "FAIL"
            self.test_result[frame_size] = deepcopy(ret_data)

        for frame_size in self.test_result.keys():
            table_row = list()
            for i in range(len(header)):
                table_row.append(self.test_result[frame_size][header[i]])
            self.result_table_add(table_row)
        # present test results to screen
        self.result_table_print()
        self.verify(
            "FAIL" not in self.test_result,
            "Excessive gap between test results and expectations",
        )

    def start_testpmd_as_vhost(self):
        """
        start testpmd on vhost
        """
        vdev = ["net_vhost0,iface=vhost-net,queues=1"]
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list_vhost_user,
            prefix="vhost",
            ports=[self.pci_info],
            vdevs=vdev,
        )
        command_line_client = self.path + eal_params + " -- -i"
        self.vhost_user.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def start_testpmd_as_virtio(self, packed=False):
        """
        start testpmd on virtio
        """
        vdev = (
            "net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1"
            if not packed
            else "net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,packed_vq=1"
        )
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list_virtio_user,
            no_pci=True,
            prefix="virtio-user",
            vdevs=[vdev],
        )
        command_line_user = self.path + eal_params + " --single-file-segments -- -i"
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd mac", "testpmd> ", 120)
        self.virtio_user.send_expect("start", "testpmd> ", 120)

    def close_all_apps(self):
        """
        close testpmd and vhost-switch
        """
        self.virtio_user.send_expect("quit", "# ", 60)
        self.vhost_user.send_expect("quit", "# ", 60)

    def test_perf_pvp_virtio_user_split_ring_2M_hugepages(self):
        """
        Basic test for virtio-user 2M hugepage
        """
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        self.start_testpmd_as_vhost()
        self.start_testpmd_as_virtio()
        self.perf_test()
        self.handle_expected()
        self.handle_results()
        self.close_all_apps()

    def test_perf_pvp_virtio_user_packed_ring_2M_hugepages(self):
        """
        Basic test for virtio-user 2M hugepage
        """
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.running_case
        ]
        self.start_testpmd_as_vhost()
        self.start_testpmd_as_virtio(packed=True)
        self.perf_test()
        self.handle_expected()
        self.handle_results()
        self.close_all_apps()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)
