# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

"""
DPDK Test suite.
The feature need compile dpdk as shared libraries.
"""

import framework.utils as utils
from framework.pktgen import PacketGeneratorHelper
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase


class TestPVPShareLib(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.core_config = "1S/4C/1T"
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket
        )
        self.verify(
            len(self.core_list) >= 4,
            "There has not enought cores to test this suite %s" % self.suite_name,
        )

        self.core_list_virtio_user = self.core_list[0:2]
        self.core_list_vhost_user = self.core_list[2:4]
        self.mem_channels = self.dut.get_memory_channels()
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.prepare_share_lib_env()

        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf ./vhost-net*", "# ")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.vhost_user.send_expect(
            "export LD_LIBRARY_PATH=%s/%s/drivers:$LD_LIBRARY_PATH"
            % (self.dut.base_dir, self.dut.target),
            "# ",
        )
        self.virtio_user.send_expect(
            "export LD_LIBRARY_PATH=%s/%s/drivers:$LD_LIBRARY_PATH"
            % (self.dut.base_dir, self.dut.target),
            "# ",
        )
        # Prepare the result table
        self.table_header = ["Frame"]
        self.table_header.append("Mode")
        self.table_header.append("Mpps")
        self.table_header.append("Queue Num")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)

    def prepare_share_lib_env(self):
        self.dut.build_install_dpdk(
            self.dut.target, extra_options="-Dc_args=-DRTE_BUILD_SHARED_LIB"
        )

    def restore_env(self):
        self.dut.build_install_dpdk(self.dut.target)

    def send_and_verify(self):
        """
        Send packet with packet generator and verify
        """
        payload_size = 64 - HEADER_SIZE["eth"] - HEADER_SIZE["ip"] - HEADER_SIZE["tcp"]
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
        _, Pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
        self.verify(Pps > 0, "%s can not receive packets" % (self.running_case))
        Pps /= 1e6
        Pct = (Pps * 100) / self.wirespeed(self.nic, 64, 1)

        results_row = [64]
        results_row.append("share_lib")
        results_row.append(Pps)
        results_row.append("1")
        results_row.append(Pct)
        self.result_table_add(results_row)

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def start_testpmd_as_vhost(self, driver):
        """
        start testpmd on vhost
        """
        self.pci_info = self.dut.ports_info[0]["pci"]
        eal_param = self.dut.create_eal_parameters(
            socket=self.ports_socket,
            cores=self.core_list_vhost_user,
            prefix="vhost",
            vdevs=["net_vhost0,iface=vhost-net,queues=1"],
            ports=[self.pci_info],
        )
        eal_param += (
            " -d librte_net_vhost.so -d librte_net_%s.so -d librte_mempool_ring.so --file-prefix=vhost"
            % driver
        )
        command_line_client = self.path + eal_param + " -- -i"

        self.vhost_user.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost_user.send_expect("set fwd mac", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def start_testpmd_as_virtio(self):
        """
        start testpmd on virtio
        """
        eal_param = self.dut.create_eal_parameters(
            socket=self.ports_socket,
            cores=self.core_list_virtio_user,
            prefix="virtio-user",
            no_pci=True,
            vdevs=["net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net"],
        )
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        eal_param += " -d librte_net_virtio.so -d librte_mempool_ring.so"
        command_line_user = self.path + eal_param + " -- -i"
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("start", "testpmd> ", 120)

    def close_all_apps(self):
        """
        close testpmd and vhost-switch
        """
        self.virtio_user.send_expect("quit", "# ", 60)
        self.vhost_user.send_expect("quit", "# ", 60)
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)

    def test_perf_pvp_share_lib_of_niantic(self):
        """
        Vhost/virtio-user pvp share lib test with 82599
        """
        self.verify(
            self.nic in ["IXGBE_10G-82599_SFP"],
            "the nic not support this case: %s" % self.running_case,
        )
        self.start_testpmd_as_vhost(driver="ixgbe")
        self.start_testpmd_as_virtio()
        self.send_and_verify()
        self.result_table_print()
        self.close_all_apps()

    def test_perf_pvp_share_lib_of_fortville(self):
        """
        Vhost/virtio-user pvp share lib test with Intel® Ethernet 700 Series
        """
        self.verify(
            self.nic in ["I40E_10G-SFP_XL710", "I40E_40G-QSFP_A", "I40E_25G-25G_SFP28"],
            "the nic not support this case: %s" % self.running_case,
        )
        self.start_testpmd_as_vhost(driver="i40e")
        self.start_testpmd_as_virtio()
        self.send_and_verify()
        self.result_table_print()
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
        self.restore_env()
