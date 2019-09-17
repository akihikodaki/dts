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
vhost/virtio-user pvp with 4K pages.
"""

import utils
import time
from test_case import TestCase
from packet import Packet, save_packets
from pktgen import PacketGeneratorHelper


class TestPvpVirtioUser4kPages(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.core_config = "1S/4C/1T"
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n['socket']) == 0])
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(self.cores_num >= 4,
                    "There has not enought cores to test this suite %s" %
                    self.suite_name)
        # for this suite, only support for vfio-pci
        self.dut.send_expect('modprobe vfio-pci', '# ')
        for i in self.dut_ports:
            port = self.dut.ports_info[i]['port']
            port.bind_driver('vfio-pci')

        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket)
        self.core_list_virtio_user = self.core_list[0:2]
        self.core_list_vhost_user = self.core_list[2:4]
        self.core_mask_virtio_user = utils.create_mask(self.core_list_virtio_user)
        self.core_mask_vhost_user = utils.create_mask(self.core_list_vhost_user)
        self.mem_channels = self.dut.get_memory_channels()
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.logger.info("You can config packet_size in file %s.cfg," % self.suite_name + \
                        " in region 'suite' like packet_sizes=[64, 128, 256]")
        if 'packet_sizes' in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()['packet_sizes']

        self.out_path = '/tmp/%s' % self.suite_name
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
        # Prepare the result table
        self.table_header = ['Frame']
        self.table_header.append("Mode")
        self.table_header.append("Mpps")
        self.table_header.append("Queue Num")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)

    def send_and_verify(self):
        """
        Send packet with packet generator and verify
        """
        for frame_size in self.frame_sizes:
            tgen_input = []
            rx_port = self.tester.get_local_port(self.dut_ports[0])
            tx_port = self.tester.get_local_port(self.dut_ports[0])
            pkt = Packet(pkt_type='UDP', pkt_len=frame_size)
            pkt.config_layer('ether', {'dst': '%s' % self.dst_mac})
            save_packets([pkt], "%s/vhost.pcap" % self.out_path)
            tgen_input.append((tx_port, rx_port, "%s/vhost.pcap" % self.out_path))

            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100,
                            None, self.tester.pktgen)
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
            Mpps = pps / 1000000.0
            self.verify(Mpps > 0, "%s can not receive packets" % (self.running_case))
            throughput = Mpps * 100 / \
                     float(self.wirespeed(self.nic, 64, 1))

            results_row = [frame_size]
            results_row.append("4K pages")
            results_row.append(Mpps)
            results_row.append("1")
            results_row.append(throughput)
            self.result_table_add(results_row)

    def start_testpmd_as_vhost(self):
        """
        Start testpmd on vhost
        """
        command_line_client = "%s/app/testpmd -c %s -n %d " + \
                              "--file-prefix=vhost  -m 1024 --no-huge " + \
                              "--vdev 'net_vhost0,iface=vhost-net,queues=1' -- -i " + \
                              "--no-numa --socket-num=%d"
        command_line_client = command_line_client % (self.target,
                            self.core_mask_vhost_user, self.mem_channels, self.ports_socket)
        self.vhost_user.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def start_testpmd_as_virtio(self):
        """
        Start testpmd on virtio
        """
        command_line_user = "./%s/app/testpmd -n %d -c %s " + \
                            "--no-huge -m 1024 --file-prefix=virtio-user " + \
                            "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1 -- -i"
        command_line_user = command_line_user % (self.target,
                self.mem_channels, self.core_mask_virtio_user)
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd mac", "testpmd> ", 120)
        self.virtio_user.send_expect("start", "testpmd> ", 120)

    def prepare_tmpfs_for_4k(self):
        """
        Prepare tmpfs with 4K-pages
        """
        self.dut.send_expect('mkdir -p /mnt/tmpfs_nohuge', '# ')
        self.dut.send_expect('mount tmpfs /mnt/tmpfs_nohuge -t tmpfs -o size=4G', '# ')

    def restore_env_of_tmpfs_for_4k(self):
        self.dut.send_expect('umount /mnt/tmpfs_nohuge', '# ')

    def close_all_apps(self):
        """
        Close testpmd
        """
        self.virtio_user.send_expect("quit", "# ", 60)
        self.vhost_user.send_expect("quit", "# ", 60)
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)

    def test_perf_pvp_virtio_user_with_4K_pages(self):
        """
        Basic test for virtio-user 4K pages
        """
        self.start_testpmd_as_vhost()
        self.prepare_tmpfs_for_4k()
        self.start_testpmd_as_virtio()
        self.send_and_verify()
        self.result_table_print()
        self.close_all_apps()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT testpmd", "# ")
        self.restore_env_of_tmpfs_for_4k()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
