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
Virtio user for container networking
"""

import utils
import time
from test_case import TestCase
from settings import HEADER_SIZE
from pktgen import PacketGeneratorHelper


class TestVirtioUserForContainer(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.queue_number = 1
        self.nb_cores = 1
        self.dut_ports = self.dut.get_ports()
        self.mem_channels = self.dut.get_memory_channels()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.verify(len(self.dut_ports) >= 1, 'Insufficient ports for testing')
        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip'] + HEADER_SIZE['udp']

        self.verify('docker_image' in self.get_suite_cfg(),
                'Pls config docker image in the conf %s' % self.suite_name)
        self.docker_image = self.get_suite_cfg()['docker_image']
        self.container_base_dir = self.dut.base_dir
        self.container_base_dir = self.container_base_dir.replace('~', '/root')
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
        self.dut.send_expect('rm -rf ./vhost-net*', '# ')
        self.dut.send_expect('killall -s INT testpmd', '# ')
        self.vhost_user = self.dut.new_session(suite='vhost-user')
        self.virtio_user = self.dut.new_session(suite='virtio-user')
        # Prepare the result table
        self.virtio_mac = '00:11:22:33:44:10'
        self.table_header = ['Frame']
        self.table_header.append('Mode')
        self.table_header.append('Mpps')
        self.table_header.append('Queue Num')
        self.table_header.append('% linerate')
        self.result_table_create(self.table_header)

    def get_core_mask(self):
        core_config = '1S/%dC/1T' % (self.nb_cores*2 + 2)
        core_list = self.dut.get_core_list(
            core_config, socket=self.ports_socket)
        self.verify(len(core_list) >= (self.nb_cores*2 + 2),
                    'There has not enought cores to test this case %s' %
                    self.running_case)
        self.core_list_vhost_user = core_list[0:self.nb_cores+1]
        core_list_virtio_user = core_list[self.nb_cores+1:self.nb_cores*2+2]
        self.core_list_virtio_user = core_list[self.nb_cores+1:self.nb_cores*2+2]
        self.core_mask_virtio_user = utils.create_mask(core_list_virtio_user)

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
                'wrpcap("%s/vhost.pcap", [Ether(dst="%s")/IP()/UDP()/("X"*%d)])' %
                (self.out_path, self.virtio_mac, payload_size))
            tgen_input.append((tx_port, rx_port, "%s/vhost.pcap" % self.out_path))

            self.tester.scapy_execute()
            self.tester.pktgen.clear_streams()
            vm_config = {'mac':{'dst':{'range': 1, 'step': 1, 'action': 'inc'},},}
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100,
                        vm_config, self.tester.pktgen)
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
            Mpps = pps / 1000000.0
            self.verify(Mpps > 0, '%s can not receive packets of frame size %d' % (self.running_case, frame_size))
            throughput = Mpps * 100 / \
                     float(self.wirespeed(self.nic, frame_size, 1))

            results_row = [frame_size]
            results_row.append('virtio in container')
            results_row.append(Mpps)
            results_row.append(self.queue_number)
            results_row.append(throughput)
            self.result_table_add(results_row)

    @property
    def check_2M_env(self):
        hugepage_size = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        return True if hugepage_size == '2048' else False

    def launch_testpmd_as_vhost(self):
        """
        start testpmd as vhost
        """
        eal_param = self.dut.create_eal_parameters(cores=self.core_list_vhost_user, prefix='vhost', vdevs=["net_vhost0,iface=vhost-net,queues=%d,client=0" % self.queue_number])
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        command_line_client = self.dut.target + '/app/testpmd ' + eal_param + ' -- -i --nb-cores=%d' % self.nb_cores
        self.vhost_user.send_expect(command_line_client, 'testpmd> ', 30)
        self.vhost_user.send_expect('start', 'testpmd> ', 30)

    def launch_testpmd_as_virtio_in_container(self):
        """
        start testpmd as virtio
        """
        if self.check_2M_env:
            command_line_user = 'docker run -i -t --privileged -v %s/vhost-net:/tmp/vhost-net ' + \
                            '-v /mnt/huge:/dev/hugepages ' + \
                            '-v %s:%s %s .%s/%s/app/testpmd -c %s -n %d ' + \
                            '-m 1024 --no-pci --file-prefix=container --single-file-segments ' + \
                            '--vdev=virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=%d ' + \
                            '-- -i --rxq=%d --txq=%d --nb-cores=%d'
        else:
            command_line_user = 'docker run -i -t --privileged -v %s/vhost-net:/tmp/vhost-net ' + \
                            '-v /mnt/huge:/dev/hugepages ' + \
                            '-v %s:%s %s .%s/%s/app/testpmd -c %s -n %d ' + \
                            '-m 1024 --no-pci --file-prefix=container --single-file-segments ' + \
                            '--vdev=virtio_user0,mac=00:11:22:33:44:10,path=/tmp/vhost-net,queues=%d ' + \
                            '-- -i --rxq=%d --txq=%d --nb-cores=%d'
        command_line_user = command_line_user % (self.container_base_dir,
            self.container_base_dir, self.container_base_dir, self.docker_image,
            self.container_base_dir, self.dut.target, self.core_mask_virtio_user,
            self.mem_channels, self.queue_number, self.queue_number,
            self.queue_number, self.nb_cores)
        self.virtio_user.send_expect(command_line_user, 'testpmd> ', 120)
        self.virtio_user.send_expect('start', 'testpmd> ', 120)

    def close_all_apps(self):
        """
        close testpmd and vhost-switch
        """
        self.virtio_user.send_expect('quit', '# ', 60)
        self.vhost_user.send_expect('quit', '# ', 60)
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)

    def test_perf_packet_fwd_for_container(self):
        """
        packet forward test for container networking
        """
        self.queue_number = 1
        self.nb_cores = 1
        self.get_core_mask()
        self.launch_testpmd_as_vhost()
        self.launch_testpmd_as_virtio_in_container()
        self.send_and_verify()
        self.result_table_print()
        self.close_all_apps()

    def test_perf_packet_fwd_with_multi_queues_for_container(self):
        """
        packet forward with multi-queues for container networking
        """
        self.queue_number = 2
        self.nb_cores = 2
        self.get_core_mask()
        self.launch_testpmd_as_vhost()
        self.launch_testpmd_as_virtio_in_container()
        self.send_and_verify()
        self.result_table_print()
        self.close_all_apps()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect('killall -s INT testpmd', '# ')

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
