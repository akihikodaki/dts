# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

"""
DPDK Test suite.
Vhost enqueue interrupt need test with l3fwd-power sample
"""

import re
import time

import framework.utils as utils
from framework.test_case import TestCase
from tests.virtio_common import basic_common as BC
from tests.virtio_common import cbdma_common as CC


class TestVhostUserInterruptCbdma(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.

        """
        self.queues = 1
        self.cores_num = len([n for n in self.dut.cores if int(n["socket"]) == 0])
        self.vmac = "00:11:22:33:44:10"
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.prepare_l3fwd_power()
        self.app_l3fwd_power_path = self.dut.apps_name["l3fwd-power"]
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.l3fwdpower_name = self.app_l3fwd_power_path.split("/")[-1]

        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        # get cbdma device
        self.cbdma_dev_infos = []
        self.dmas_info = None
        self.device_str = None
        self.BC = BC(self)
        self.CC = CC(self)

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
        out = self.dut.build_dpdk_apps("examples/l3fwd-power")
        self.verify("Error" not in out, "compilation l3fwd-power error")

    def get_core_list(self):
        """
        get core list depend on the core number
        """
        need_num = 2 * self.queues + 1
        self.core_config = "1S/%dC/1T" % need_num
        self.verify(
            self.cores_num >= need_num, "There has not enought cores to test this case"
        )
        core_list = self.dut.get_core_list(self.core_config)
        self.core_list_virtio = core_list[0 : self.queues + 1]
        self.core_list_l3fwd = core_list[self.queues + 1 : need_num]

    def lanuch_virtio_user(self, packed=False):
        """
        launch virtio-user with server mode
        """
        vdev = (
            "net_virtio_user0,mac=%s,path=./vhost-net,server=1,queues=%d"
            % (self.vmac, self.queues)
            if not packed
            else "net_virtio_user0,mac=%s,path=./vhost-net,server=1,queues=%d,packed_vq=1"
            % (self.vmac, self.queues)
        )
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list_virtio, prefix="virtio", no_pci=True, vdevs=[vdev]
        )

        if self.BC.check_2M_hugepage_size():
            eal_params += " --single-file-segments"
        para = " -- -i --rxq=%d --txq=%d --rss-ip" % (self.queues, self.queues)
        command_line_client = self.app_testpmd_path + " " + eal_params + para
        self.virtio_user.send_expect(
            command_line_client, "waiting for client connection...", 120
        )

    def lanuch_l3fwd_power(self):
        """
        launch l3fwd-power with a virtual vhost device
        """
        self.logger.info("Launch l3fwd_sample sample:")
        # config the interrupt cores
        config_info = ""
        for i in range(self.queues):
            if config_info != "":
                config_info += ","
            config_info += "(0,%d,%s)" % (i, self.core_list_l3fwd[i])
            info = {"core": self.core_list_l3fwd[i], "port": 0, "queue": i}
            self.verify_info.append(info)

        example_cmd = self.app_l3fwd_power_path + " "
        example_cmd += " --log-level=9 "
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas_info = (
            "txq0@%s;txq1@%s;txq2@%s;txq3@%s;rxq0@%s;rxq1@%s;rxq2@%s;rxq3@%s"
            % (
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
            )
        )
        vdev = "'net_vhost0,iface=vhost-net,queues=%d,client=1,dmas=[%s]'" % (
            self.queues,
            dmas_info,
        )
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list_l3fwd,
            ports=cbdmas,
            vdevs=[vdev],
        )
        para = " -- -p 0x1 --parse-ptype 1 --config '%s' --interrupt-only" % config_info
        command_line_client = example_cmd + eal_params + para
        self.vhost.get_session_before(timeout=2)
        self.vhost.send_expect(command_line_client, "POWER", 40)
        time.sleep(10)
        out = self.vhost.get_session_before()
        if "Error" in out and "Error opening" not in out:
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
                info = info % (
                    self.verify_info[i]["core"],
                    self.verify_info[i]["port"],
                    self.verify_info[i]["queue"],
                )
            elif status == "sleeps":
                info = (
                    "lcore %s sleeps until interrupt triggers"
                    % self.verify_info[i]["core"]
                )
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

    def test_wake_up_split_ring_vhost_user_core_with_l3fwd_power_sample_when_multi_queues_enabled_and_cbdma_enabled(
        self,
    ):
        """
        Test Case1: Wake up split ring vhost-user cores with l3fwd-power sample when multi queues and cbdma are enabled
        """
        self.queues = 4
        self.get_core_list()
        self.lanuch_virtio_user(packed=False)
        self.lanuch_l3fwd_power()
        self.virtio_user.send_expect("set fwd txonly", "testpmd> ", 20)
        self.send_and_verify()

    def test_wake_up_packed_ring_vhost_user_core_with_l3fwd_power_sample_when_multi_queues_enabled_and_cbdma_enabled(
        self,
    ):
        """
        Test Case2: Wake up packed ring vhost-user cores with l3fwd-power sample when multi queues and cbdma are enabled
        """
        self.queues = 4
        self.get_core_list()
        self.lanuch_virtio_user(packed=True)
        self.lanuch_l3fwd_power()
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

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.CC.bind_cbdma_to_kernel_driver(cbdma_idxs="all")
