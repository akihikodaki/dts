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

import re
import time

import framework.utils as utils
from framework.test_case import TestCase


class TestVhostUserInterrupt(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.

        """
        self.queues = 1
        self.cores_num = len([n for n in self.dut.cores if int(n['socket']) == 0])
        self.vmac = "00:11:22:33:44:10"
        self.pci_info = self.dut.ports_info[0]['pci']
        self.prepare_l3fwd_power()
        self.app_l3fwd_power_path = self.dut.apps_name['l3fwd-power']
        self.app_testpmd_path = self.dut.apps_name['test-pmd']
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.l3fwdpower_name = self.app_l3fwd_power_path.split("/")[-1]

        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        # get cbdma device
        self.cbdma_dev_infos = []
        self.dmas_info = None
        self.device_str = None

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.verify_info = []
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall %s" % self.l3fwdpower_name, "#")
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

    def lanuch_virtio_user(self, packed=False, cbdma=False):
        """
        launch virtio-user with server mode
        """
        vdev = "net_virtio_user0,mac=%s,path=./vhost-net,server=1,queues=%d" % (self.vmac, self.queues) if not packed else "net_virtio_user0,mac=%s,path=./vhost-net,server=1,queues=%d,packed_vq=1" % (self.vmac, self.queues)
        if cbdma ==True:
            eal_params = self.dut.create_eal_parameters(cores=self.core_list_virtio, prefix='virtio', no_pci=True, vdevs=[vdev])
        else:
            eal_params = self.dut.create_eal_parameters(cores=self.core_list_virtio, prefix='virtio', no_pci=True, ports=[self.pci_info], vdevs=[vdev])
        if self.check_2M_env:
            eal_params += " --single-file-segments"
        para = " -- -i --rxq=%d --txq=%d --rss-ip" % (self.queues, self.queues)
        command_line_client =  self.app_testpmd_path + " " + eal_params + para
        self.virtio_user.send_expect(command_line_client, "waiting for client connection...", 120)

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num):
        """
        get all cbdma ports
        """
        # check driver name in execution.cfg
        self.verify(self.drivername == 'igb_uio',
                    "CBDMA test case only use igb_uio driver, need config drivername=igb_uio in execution.cfg")
        str_info = 'Misc (rawdev) devices using kernel driver'
        out = self.dut.send_expect('./usertools/dpdk-devbind.py --status-dev misc', '# ', 30)
        device_info = out.split('\n')
        for device in device_info:
            pci_info = re.search('\s*(0000:\d*:\d*.\d*)', device)
            if pci_info is not None:
                dev_info = pci_info.group(1)
                # the numa id of ioat dev, only add the device which
                # on same socket with nic dev
                bus = int(dev_info[5:7], base=16)
                if bus >= 128:
                    cur_socket = 1
                else:
                    cur_socket = 0
                if self.ports_socket == cur_socket:
                    self.cbdma_dev_infos.append(pci_info.group(1))
        self.verify(len(self.cbdma_dev_infos) >= cbdma_num, 'There no enough cbdma device to run this suite')
        used_cbdma = self.cbdma_dev_infos[0:cbdma_num]
        dmas_info = ''
        for dmas in used_cbdma:
            number = used_cbdma.index(dmas)
            dmas = 'txq{}@{};'.format(number, dmas)
            dmas_info += dmas
        self.dmas_info = dmas_info[:-1]
        self.device_str = ' '.join(used_cbdma)
        self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=%s %s' % (self.drivername, self.device_str), '# ', 60)

    def bind_cbdma_device_to_kernel(self):
        if self.device_str is not None:
            self.dut.send_expect('modprobe ioatdma', '# ')
            self.dut.send_expect('./usertools/dpdk-devbind.py -u %s' % self.device_str, '# ', 30)
            self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=ioatdma  %s' % self.device_str, '# ', 60)

    @property
    def check_2M_env(self):
        out = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        return True if out == '2048' else False

    def lanuch_l3fwd_power(self, cbdma=False):
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

        example_cmd = self.app_l3fwd_power_path + " "
        if cbdma ==True:
            example_cmd += " --log-level=9 "
            self.get_cbdma_ports_info_and_bind_to_dpdk(4)
            vdev = "'net_vhost0,iface=vhost-net,queues=%d,client=1,dmas=[%s]'" % (self.queues, self.dmas_info)
            eal_params = self.dut.create_eal_parameters(cores=self.core_list_l3fwd, ports=self.cbdma_dev_infos[0:4], vdevs=[vdev])
        else:
            vdev = 'net_vhost0,iface=vhost-net,queues=%d,client=1' % self.queues
            eal_params = self.dut.create_eal_parameters(cores=self.core_list_l3fwd, no_pci=True, vdevs=[vdev])
        para = " -- -p 0x1 --parse-ptype 1 --config '%s' --interrupt-only" % config_info
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
        Test Case1: Wake up split ring vhost-user core with l3fwd-power sample
        """
        self.queues = 1
        self.get_core_list()
        self.lanuch_virtio_user()
        self.lanuch_l3fwd_power()
        self.virtio_user.send_expect("set fwd txonly", "testpmd> ", 20)
        self.send_and_verify()

    def test_wake_up_split_ring_vhost_user_core_with_l3fwd_power_sample_when_multi_queues_enabled(self):
        """
        Test Case2: Wake up split ring vhost-user cores with l3fwd-power sample when multi queues are enabled
        """
        self.queues = 4
        self.get_core_list()
        self.lanuch_virtio_user()
        self.lanuch_l3fwd_power()
        self.virtio_user.send_expect("set fwd txonly", "testpmd> ", 20)
        self.send_and_verify()

    def test_wake_up_packed_ring_vhost_user_core_with_l3fwd_power_sample(self):
        """
        Test Case3: Wake up packed ring vhost-user core with l3fwd-power sample
        """
        self.queues = 1
        self.get_core_list()
        self.lanuch_virtio_user(packed=True)
        self.lanuch_l3fwd_power()
        self.virtio_user.send_expect("set fwd txonly", "testpmd> ", 20)
        self.send_and_verify()

    def test_wake_up_packed_ring_vhost_user_core_with_l3fwd_power_sample_when_multi_queues_enabled(self):
        """
        Test Case4:  Wake up packed ring vhost-user cores with l3fwd-power sample when multi queues are enabled
        """
        self.queues = 4
        self.get_core_list()
        self.lanuch_virtio_user(packed=True)
        self.lanuch_l3fwd_power()
        self.virtio_user.send_expect("set fwd txonly", "testpmd> ", 20)
        self.send_and_verify()

    def test_wake_up_split_ring_vhost_user_core_with_l3fwd_power_sample_when_multi_queues_enabled_and_cbdma_enabled(self):
        """
        Test Case5: Wake up split ring vhost-user cores with l3fwd-power sample when multi queues and cbdma are enabled
        """
        self.queues = 4
        self.get_core_list()
        self.lanuch_virtio_user(cbdma=True)
        self.lanuch_l3fwd_power(cbdma=True)
        self.virtio_user.send_expect("set fwd txonly", "testpmd> ", 20)
        self.send_and_verify()

    def test_wake_up_packed_ring_vhost_user_core_with_l3fwd_power_sample_when_multi_queues_enabled_and_cbdma_enabled(self):
        """
        Test Case6: Wake up packed ring vhost-user cores with l3fwd-power sample when multi queues and cbdma are enabled
        """
        self.queues = 4
        self.get_core_list()
        self.lanuch_virtio_user(packed=True, cbdma=True)
        self.lanuch_l3fwd_power(cbdma=True)
        self.virtio_user.send_expect("set fwd txonly", "testpmd> ", 20)
        self.send_and_verify()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.close_testpmd_and_session()
        self.dut.send_expect("killall %s" % self.l3fwdpower_name, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.kill_all()
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        # revert the code
        self.dut.send_expect("mv ./main.c ./examples/l3fwd-power/", "#")
        self.dut.build_dpdk_apps('examples/l3fwd-power')
