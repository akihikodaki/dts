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
Vhost enqueue interrupt need test with l3fwd-power sample
"""

import utils
import time
from test_case import TestCase


class TestVhostEnqueueInterrupt(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.

        """
        self.queues = 1
        self.cores_num = len([n for n in self.dut.cores if int(n['socket']) == 0])
        self.vmac = "00:11:22:33:44:10"
        self.pci_info = self.dut.ports_info[0]['pci']
        self.prepare_l3fwd_power()

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.verify_info = []
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall l3fwd-power", "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.vhost = self.dut.new_session(suite="vhost-l3fwd")
        self.virtio_user = self.dut.new_session(suite="virtio-user")

    def prepare_l3fwd_power(self):
        self.dut.send_expect("cp ./examples/l3fwd-power/main.c .", "#")
        self.dut.send_expect(
                "sed -i '/DEV_RX_OFFLOAD_CHECKSUM/d' ./examples/l3fwd-power/main.c", "#")
        out = self.dut.build_dpdk_apps('examples/l3fwd-power')
        self.verify("Error" not in out, "compilation l3fwd-power error")

    def get_core_list(self):
        """
        get core list depend on the core number
        """
        need_num = 2*self.queues+1
        self.core_config = "1S/%dC/1T" % need_num
        self.verify(self.cores_num >= need_num,
                    "There has not enought cores to test this case")
        core_list = self.dut.get_core_list(self.core_config)
        self.core_list_virtio = core_list[0: self.queues+1]
        self.core_list_l3fwd = core_list[self.queues+1: need_num]

    def lanuch_virtio_user(self, packed=False):
        """
        launch virtio-user with server mode
        """
        vdev = "net_virtio_user0,mac=%s,path=./vhost-net,server=1,queues=%d" % (self.vmac, self.queues) if not packed else "net_virtio_user0,mac=%s,path=./vhost-net,server=1,queues=%d,packed_vq=1" % (self.vmac, self.queues)
        eal_params = self.dut.create_eal_parameters(cores=self.core_list_virtio, prefix='virtio', no_pci=True, ports=[self.pci_info], vdevs=[vdev])
        para = " -- -i --rxq=%d --txq=%d --rss-ip" % (self.queues, self.queues)
        command_line_client =  self.dut.target + "/app/testpmd " + eal_params + para
        self.virtio_user.send_expect(command_line_client, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd txonly", "testpmd> ", 20)

    def lanuch_l3fwd_power(self):
        """
        launch l3fwd-power with a virtual vhost device
        """
        self.logger.info("Launch l3fwd_sample sample:")
        # config the interrupt cores
        config_info = ""
        for i in range(self.queues):
            if config_info != "":
                config_info += ','
            config_info += '(0,%d,%s)' % (i, self.core_list_l3fwd[i])
            info = {'core': self.core_list_l3fwd[i], 'port': 0, 'queue': i}
            self.verify_info.append(info)

        example_cmd = "./examples/l3fwd-power/build/l3fwd-power "
        vdev = 'net_vhost0,iface=vhost-net,queues=%d,client=1' % self.queues
        para = " -- -p 0x1 --parse-ptype 1 --config '%s' --interrupt-only" % config_info
        eal_params = self.dut.create_eal_parameters(cores=self.core_list_l3fwd, no_pci=True, ports=[self.pci_info], vdevs=[vdev])
        command_line_client = example_cmd + eal_params + para
        self.vhost.get_session_before(timeout=2)
        self.vhost.send_expect(command_line_client, "POWER", 40)
        time.sleep(10)
        out = self.vhost.get_session_before()
        if ("Error" in out and "Error opening" not in out):
            self.logger.error("Launch l3fwd-power sample error")
        else:
            self.logger.info("Launch l3fwd-power sample finished")

    def check_vhost_core_status(self, status):
        """
        check the cpu status
        """
        out = self.vhost.get_session_before()
        for i in range(len(self.verify_info)):
            if status == "waked up":
                info = "lcore %s is waked up from rx interrupt on port %d queue %d"
                info = info % (self.verify_info[i]["core"], self.verify_info[i]['port'],
                                self.verify_info[i]['queue'])
            elif status == "sleeps":
                info = "lcore %s sleeps until interrupt triggers" % self.verify_info[i]["core"]
            self.verify(info in out, "The CPU status not right for %s" % info)
            self.logger.info(info)

    def send_and_verify(self):
        """
        start to send packets and check the cpu status
        stop and restart to send packets and check the cpu status
        """
        self.virtio_user.send_expect("start", "testpmd> ", 20)
        self.check_vhost_core_status("waked up")

        self.virtio_user.send_expect("stop", "testpmd> ", 20)
        self.check_vhost_core_status("sleeps")

        self.virtio_user.send_expect("start", "testpmd> ", 20)
        self.check_vhost_core_status("waked up")

    def close_testpmd_and_session(self):
        self.virtio_user.send_expect("quit", "#", 20)
        self.dut.close_session(self.vhost)
        self.dut.close_session(self.virtio_user)

    def test_wake_up_split_ring_vhost_user_core_with_l3fwd_power_sample(self):
        """
        Check the virtio-user interrupt can work when use vhost-net as backend
        """
        self.queues = 1
        self.get_core_list()
        self.lanuch_virtio_user()
        self.lanuch_l3fwd_power()
        self.send_and_verify()

    def test_wake_up_split_ring_vhost_user_core_with_l3fwd_power_sample_when_multi_queues_enabled(self):
        """
        Check the virtio-user interrupt can work with multi queue
        """
        self.queues = 4
        self.get_core_list()
        self.lanuch_virtio_user()
        self.lanuch_l3fwd_power()
        self.send_and_verify()

    def test_wake_up_packed_ring_vhost_user_core_with_l3fwd_power_sample(self):
        """
        Check the virtio-user interrupt can work when use vhost-net as backend
        """
        self.queues = 1
        self.get_core_list()
        self.lanuch_virtio_user(packed=True)
        self.lanuch_l3fwd_power()
        self.send_and_verify()

    def test_wake_up_packed_ring_vhost_user_core_with_l3fwd_power_sample_when_multi_queues_enabled(self):
        """
        Check the virtio-user interrupt can work with multi queue
        """
        self.queues = 4
        self.get_core_list()
        self.lanuch_virtio_user(packed=True)
        self.lanuch_l3fwd_power()
        self.send_and_verify()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.close_testpmd_and_session()
        self.dut.send_expect("killall l3fwd-power", "#")
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        # revert the code
        self.dut.send_expect("mv ./main.c ./examples/l3fwd-power/", "#")
        self.dut.build_dpdk_apps('examples/l3fwd-power')
        pass
