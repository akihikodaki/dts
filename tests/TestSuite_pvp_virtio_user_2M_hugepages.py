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
vhost/virtio-user pvp with 2M hugepage.
"""

import time

import framework.utils as utils
from framework.pktgen import PacketGeneratorHelper
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase


class TestPVPVirtioWith2Mhuge(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        hugepages_size = self.dut.send_expect("awk '/Hugepagesize/ {print $2}' /proc/meminfo", "# ")
        self.verify(int(hugepages_size) == 2048, "Please config you hugepages_size to 2048")
        self.core_config = "1S/4C/1T"
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(len(self.core_list) >= 4,
                    "There has not enought cores to test this suite %s" %
                    self.suite_name)

        self.core_list_virtio_user = self.core_list[0:2]
        self.core_list_vhost_user = self.core_list[2:4]
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.header_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip'] + HEADER_SIZE['tcp']
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.logger.info("You can config packet_size in file %s.cfg," % self.suite_name + \
                        " in region 'suite' like packet_sizes=[64, 128, 256]")
        if 'packet_sizes' in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()['packet_sizes']
        self.out_path = '/tmp'
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.pci_info = self.dut.ports_info[0]['pci']
        self.number_of_ports = 1
        self.path=self.dut.apps_name['test-pmd']
        self.testpmd_name = self.path.split("/")[-1]

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf ./vhost-net*", "# ")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        # Prepare the result table
        self.table_header = ['Frame']
        self.table_header.append("Mode")
        self.table_header.append("Mpps")
        self.table_header.append("Queue Num")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)

    @property
    def check_value(self):
        check_dict = dict.fromkeys(self.frame_sizes)
        linerate = {64: 0.085, 128: 0.12, 256: 0.20, 512: 0.35, 1024: 0.50, 1280: 0.55, 1518: 0.60}
        for size in self.frame_sizes:
            speed = self.wirespeed(self.nic, size, self.number_of_ports)
            check_dict[size] = round(speed * linerate[size], 2)
        return check_dict

    def send_and_verify(self):
        """
        Send packet with packet generator and verify
        """
        for frame_size in self.frame_sizes:
            payload_size = frame_size - self.header_size
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
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
            Mpps = pps / 1000000.0
            self.verify(Mpps > self.check_value[frame_size],
                        "%s of frame size %d speed verify failed, expect %s, result %s" % (
                            self.running_case, frame_size, self.check_value[frame_size], Mpps))
            throughput = Mpps * 100 / \
                     float(self.wirespeed(self.nic, 64, 1))

            results_row = [frame_size]
            results_row.append("2M Hugepages")
            results_row.append(Mpps)
            results_row.append("1")
            results_row.append(throughput)
            self.result_table_add(results_row)

    def start_testpmd_as_vhost(self):
        """
        start testpmd on vhost
        """
        vdev = ["net_vhost0,iface=vhost-net,queues=1"]
        eal_params = self.dut.create_eal_parameters(cores=self.core_list_vhost_user, prefix='vhost', ports=[self.pci_info], vdevs=vdev)
        command_line_client = self.path + eal_params + " -- -i"
        self.vhost_user.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def start_testpmd_as_virtio(self, packed=False):
        """
        start testpmd on virtio
        """
        vdev = 'net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1' if not packed else 'net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1,packed_vq=1'
        eal_params = self.dut.create_eal_parameters(cores=self.core_list_virtio_user, no_pci=True, prefix='virtio-user', vdevs=[vdev])
        command_line_user = self.path + eal_params + ' --single-file-segments -- -i'
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd mac", "testpmd> ", 120)
        self.virtio_user.send_expect("start", "testpmd> ", 120)

    def close_all_apps(self):
        """
        close testpmd and vhost-switch
        """
        self.virtio_user.send_expect("quit", "# ", 60)
        self.vhost_user.send_expect("quit", "# ", 60)
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)

    def test_perf_pvp_virtio_user_split_ring_2M_hugepages(self):
        """
        Basic test for virtio-user 2M hugepage
        """
        self.start_testpmd_as_vhost()
        self.start_testpmd_as_virtio()
        self.send_and_verify()
        self.result_table_print()
        self.close_all_apps()

    def test_perf_pvp_virtio_user_packed_ring_2M_hugepages(self):
        """
        Basic test for virtio-user 2M hugepage
        """
        self.start_testpmd_as_vhost()
        self.start_testpmd_as_virtio(packed=True)
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
        pass
