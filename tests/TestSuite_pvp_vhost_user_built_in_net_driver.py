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
"""

import utils
import time
import re
from test_case import TestCase
from settings import HEADER_SIZE
from pktgen import PacketGeneratorHelper
from pmd_output import PmdOutput


class TestPVPVhostUserBuiltInNetDriver(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
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
        self.core_mask_virtio_user = utils.create_mask(self.core_list_virtio_user)
        self.core_mask_vhost_user = utils.create_mask(self.core_list_vhost_user)
        self.mem_channels = self.dut.get_memory_channels()
        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip']
        self.prepare_vhost_switch()

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

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf ./vhost-net*", "# ")
        self.dut.send_expect("rm -rf ./vhost.out", "# ")
        self.dut.send_expect("killall -s INT vhost", "# ")
        self.dut.send_expect("killall -s INT testpmd", "# ")
        self.vhost_switch = self.dut.new_session(suite="vhost-switch")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.pmd_out = PmdOutput(self.dut, self.virtio_user)
        # Prepare the result table
        self.virtio_mac = "00:11:22:33:44:10"
        self.vlan_id = 1000
        self.table_header = ['Frame']
        self.table_header.append("Mode")
        self.table_header.append("Mpps")
        self.table_header.append("Queue Num")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)

    def prepare_vhost_switch(self):
        cmd_info = self.dut.send_expect("grep 'define MAX_QUEUES' %s" %
                        "./examples/vhost/main.c", "# ")
        out = re.search("#define MAX_QUEUES\s*(\d*)", cmd_info)
        if out is not None:
            self.default_queue = out.group(1)
        else:
            self.default_queue = 128
        sed_cmd = "sed -i -e 's/#define MAX_QUEUES.*$/#define MAX_QUEUES %d/' " + \
                "./examples/vhost/main.c"
        if self.nic in ['niantic']:
            max_queues = 128
        else:
            max_queues = 512
        self.dut.send_expect(sed_cmd % max_queues, "#", 10)
        out = self.dut.build_dpdk_apps('./examples/vhost')
        self.verify('make: Leaving directory' in out, "Compilation failed")
        self.verify("Error" not in out, "compilation l3fwd-power error")
        self.verify("No such" not in out, "Compilation error")

    def send_and_verify(self):
        """
        Send packet with packet generator and verify
        """
        for frame_size in self.frame_sizes:
            payload_size = frame_size - self.headers_size
            tgen_input = []
            rx_port = self.tester.get_local_port(self.dut_ports[0])
            tx_port = self.tester.get_local_port(self.dut_ports[0])
            self.tester.scapy_append(
                'wrpcap("%s/vhost.pcap", [Ether(dst="%s")/Dot1Q(vlan=%s)/IP()/("X"*%d)])' %
                (self.out_path, self.virtio_mac, self.vlan_id, payload_size))
            tgen_input.append((tx_port, rx_port, "%s/vhost.pcap" % self.out_path))

            self.tester.scapy_execute()
            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100,
                            None, self.tester.pktgen)
            trans_options={'delay':5, 'duration': 20}
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=trans_options)
            Mpps = pps / 1000000.0
            self.verify(Mpps > 0, "%s can not receive packets of frame size %d" % (self.running_case, frame_size))
            throughput = Mpps * 100 / \
                     float(self.wirespeed(self.nic, frame_size, 1))

            results_row = [frame_size]
            results_row.append("builtin-net-driver")
            results_row.append(Mpps)
            results_row.append("1")
            results_row.append(throughput)
            self.result_table_add(results_row)

    def launch_vhost_switch(self):
        """
        start vhost-switch on vhost
        """
        self.dut.send_expect("rm -rf ./vhost.out", "#")
        command_line_client = "./examples/vhost/build/app/vhost-switch " + \
                              "-c %s -n %d --socket-mem 2048,2048 -- " + \
                              "-p 0x1 --mergeable 0 --vm2vm 1 " + \
                              "--builtin-net-driver  --socket-file ./vhost-net" + \
                              "> ./vhost.out &"
        command_line_client = command_line_client % (self.core_mask_vhost_user,
                                            self.mem_channels)
        self.vhost_switch.send_expect(command_line_client, "# ", 120)
        time.sleep(15)
        try:
            self.logger.info("Launch vhost sample:")
            self.dut.session.copy_file_from(self.dut.base_dir + "/vhost.out")
            fp = open('./vhost.out', 'r')
            out = fp.read()
            fp.close()
            if "Error" in out:
                raise Exception("Launch vhost sample failed")
            else:
                self.logger.info("Launch vhost sample finished")
        except Exception as e:
            self.verify(0, "ERROR: Failed to launch vhost sample: %s" %
                str(e))

    def start_virtio_testpmd(self):
        """
        start testpmd on virtio
        """
        command_line_user = "./%s/app/testpmd -n %d -c %s " + \
                            "--no-pci --socket-mem 2048,2048 --file-prefix=virtio-user " + \
                            "--vdev=net_virtio_user0,mac=%s,path=./vhost-net,queues=1 " + \
                            "-- -i --rxq=1 --txq=1"
        command_line_user = command_line_user % (self.target,
            self.mem_channels, self.core_mask_virtio_user, self.virtio_mac)
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd mac", "testpmd> ", 120)
        self.virtio_user.send_expect("start tx_first", "testpmd> ", 120)
        res = self.pmd_out.wait_link_status_up('all')
        self.verify(res is True, 'There has port link is down')

    def close_all_apps(self):
        """
        close testpmd and vhost-switch
        """
        self.virtio_user.send_expect("quit", "# ", 60)
        self.vhost_switch.send_expect("killall -s INT vhost", "# ", 60)
        self.dut.close_session(self.vhost_switch)
        self.dut.close_session(self.virtio_user)

    def test_perf_pvp_with_built_in_net_driver(self):
        """
        PVP test with vhost built-in net driver
        """
        self.launch_vhost_switch()
        self.start_virtio_testpmd()
        self.send_and_verify()
        self.result_table_print()
        self.close_all_apps()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT testpmd", "# ")
        self.dut.send_expect("killall -s INT vhost", "# ")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        sed_cmd = "sed -i -e 's/#define MAX_QUEUES.*$/#define MAX_QUEUES %d/' " + \
                "./examples/vhost/main.c"
        self.dut.send_expect(sed_cmd % int(self.default_queue), "#", 10)
        self.dut.build_dpdk_apps('./examples/vhost')
