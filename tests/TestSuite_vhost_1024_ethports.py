# BSD LICENSE
#
# Copyright (c) <2019>, Intel Corporation.
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
Basic test for launch vhost with 1024 ethports
"""

import framework.utils as utils
from framework.test_case import TestCase


class TestVhost1024Ethports(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        # DPDK limits the number of vdev to 1023
        self.max_ethport = 1023
        self.queue = 1
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, 'Insufficient ports for testing')
        self.mem_channels = self.dut.get_memory_channels()
        cores = self.dut.get_core_list("1S/2C/1T")
        self.pci_info = self.dut.ports_info[0]['pci']
        self.build_user_dpdk()
        self.testpmd_path=self.dut.apps_name['test-pmd']
        self.testpmd_name = self.testpmd_path.split("/")[-1]

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect('rm -rf ./vhost-net*', '# ')
        self.dut.send_expect('killall -s INT %s' % self.testpmd_name, '# ')
        self.vhost_user = self.dut.new_session(suite='vhost-user')

    def build_user_dpdk(self):
        if self.dut.build_type == "meson":
            self.dut.build_install_dpdk(self.target, extra_options="-Dmax_ethports=1024")
        else:
            self.dut.send_expect("sed -i 's/CONFIG_RTE_MAX_ETHPORTS=32$/CONFIG_RTE_MAX_ETHPORTS=1024/' config/common_base", '#', 30)
            self.dut.build_install_dpdk(self.target)

    def restore_dpdk(self):
        if self.dut.build_type == "meson":
            self.dut.build_install_dpdk(self.target, extra_options="-Dmax_ethports=32")
        else:
            self.dut.send_expect("sed -i 's/CONFIG_RTE_MAX_ETHPORTS=1024$/CONFIG_RTE_MAX_ETHPORTS=32/' config/common_base", '#', 30)
            self.dut.build_install_dpdk(self.target)

    @property
    def check_2M_env(self):
        out = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        return True if out == '2048' else False

    def test_launch_vhost_with_1024_ethports(self):
        """
        Test function of launch vhost with 1024 ethports
        """
        if self.check_2M_env:
            hugepages = int(self.dut.get_total_huge_pages())
            if hugepages< 20480:
                self.dut.send_expect('echo 20480 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages', expected='# ', timeout=30)
        command_line_vdev = ''
        for ethport in range(self.max_ethport):
            command_line_vdev += '--vdev "eth_vhost%d,iface=vhost-net%d,queues=%d" ' %(ethport, ethport, self.queue)
        eal_params = self.dut.create_eal_parameters(cores="1S/2C/1T", prefix='vhost', ports=[self.pci_info])
        command_line_client = self.testpmd_path + eal_params + command_line_vdev + ' -- -i'
        try:
            out = self.vhost_user.send_expect(command_line_client, 'testpmd> ', 120)
            self.verify("Failed to create eth_vhost" not in out, "Failed to create some vhost_ethports")
        except Exception as e:
            self.verify(0, 'start testpmd failed')
        self.vhost_user.send_expect("quit", "#", 120)
        self.verify("Done" in out, "launch vhost with 1024 ethports failed")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect('rm -rf ./vhost-net*', '# ')
        self.dut.close_session(self.vhost_user)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.restore_dpdk()
