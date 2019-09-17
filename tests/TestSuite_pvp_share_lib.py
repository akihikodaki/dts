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
The feature need compile dpdk as shared libraries.
"""

import utils
from test_case import TestCase
from settings import HEADER_SIZE
from pktgen import PacketGeneratorHelper


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
            self.core_config, socket=self.ports_socket)
        self.verify(len(self.core_list) >= 4,
                    "There has not enought cores to test this suite %s" %
                    self.suite_name)

        self.core_list_virtio_user = self.core_list[0:2]
        self.core_list_vhost_user = self.core_list[2:4]
        self.core_mask_virtio_user = utils.create_mask(self.core_list_virtio_user)
        self.core_mask_vhost_user = utils.create_mask(self.core_list_vhost_user)
        self.mem_channels = self.dut.get_memory_channels()
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.prepare_share_lib_env()

        self.out_path = '/tmp'
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf ./vhost-net*", "# ")
        self.dut.send_expect("killall -s INT testpmd", "# ")
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.vhost_user.send_expect("export LD_LIBRARY_PATH=%s/%s/lib:$LD_LIBRARY_PATH" %
                        (self.dut.base_dir, self.dut.target), "# ")
        self.virtio_user.send_expect("export LD_LIBRARY_PATH=%s/%s/lib:$LD_LIBRARY_PATH" %
                        (self.dut.base_dir, self.dut.target), "# ")
        # Prepare the result table
        self.table_header = ['Frame']
        self.table_header.append("Mode")
        self.table_header.append("Mpps")
        self.table_header.append("Queue Num")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)

    def prepare_share_lib_env(self):
        self.dut.send_expect("sed -i 's/CONFIG_RTE_BUILD_SHARED_LIB=n$/CONFIG_RTE_BUILD_SHARED_LIB=y/' config/common_base", "# ")
        self.dut.build_install_dpdk(self.dut.target)

    def restore_env(self):
        self.dut.send_expect("sed -i 's/CONFIG_RTE_BUILD_SHARED_LIB=y$/CONFIG_RTE_BUILD_SHARED_LIB=n/' config/common_base", "# ")
        self.dut.build_install_dpdk(self.dut.target)

    def send_and_verify(self):
        """
        Send packet with packet generator and verify
        """
        payload_size = 64 - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['tcp']
        tgen_input = []
        rx_port = self.tester.get_local_port(self.dut_ports[0])
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.tester.scapy_append(
            'wrpcap("%s/vhost.pcap", [Ether(dst="%s")/IP()/TCP()/("X"*%d)])' %
            (self.out_path, self.dst_mac, payload_size))
        tgen_input.append((tx_port, rx_port, "%s/vhost.pcap" % self.out_path))

        self.tester.scapy_execute()
        self.tester.pktgen.clear_streams()
        streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100,
                    None, self.tester.pktgen)
        _, Pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
        self.verify(Pps > 0, "%s can not receive packets" % (self.running_case))
        Pps /= 1E6
        Pct = (Pps * 100) / \
                self.wirespeed(self.nic, 64, 1)

        results_row = [64]
        results_row.append("share_lib")
        results_row.append(Pps)
        results_row.append("1")
        results_row.append(Pct)
        self.result_table_add(results_row)

    def start_testpmd_as_vhost(self, driver):
        """
        start testpmd on vhost
        """
        command_line_client = "%s/app/testpmd -c %s -n %d " + \
                              "--socket-mem 2048,2048 --legacy-mem " + \
                              "-d librte_pmd_vhost.so -d librte_pmd_%s.so " + \
                              "-d librte_mempool_ring.so --file-prefix=vhost " + \
                              "--vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i"
        command_line_client = command_line_client % (self.target,
                        self.core_mask_vhost_user, self.mem_channels, driver)
        self.vhost_user.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost_user.send_expect("set fwd mac", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def start_testpmd_as_virtio(self):
        """
        start testpmd on virtio
        """
        command_line_user = "./%s/app/testpmd -n %d -c %s " + \
                            "--no-pci --socket-mem 2048,2048 --legacy-mem " + \
                            "--file-prefix=virtio-user " + \
                            "-d librte_pmd_virtio.so -d librte_mempool_ring.so " + \
                            "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net -- -i"
        command_line_user = command_line_user % (self.target,
                self.mem_channels, self.core_mask_virtio_user)
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
        Vhost/virtio-user pvp share lib test with niantic
        """
        self.verify(self.nic in ['niantic'],
                    "the nic not support this case: %s" % self.running_case)
        self.start_testpmd_as_vhost(driver='ixgbe')
        self.start_testpmd_as_virtio()
        self.send_and_verify()
        self.result_table_print()
        self.close_all_apps()

    def test_perf_pvp_share_lib_of_fortville(self):
        """
        Vhost/virtio-user pvp share lib test with fortville
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit", "fortville_25g"],
                    "the nic not support this case: %s" % self.running_case)
        self.start_testpmd_as_vhost(driver='i40e')
        self.start_testpmd_as_virtio()
        self.send_and_verify()
        self.result_table_print()
        self.close_all_apps()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT testpmd", "# ")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.restore_env()
