# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

"""
DPDK Test suite.
Virtio-user interrupt need test with l3fwd-power sample
"""

import re
import time

import framework.utils as utils
from framework.test_case import TestCase


class TestVhostVirtioUserInterrupt(TestCase):
    def set_up_all(self):
        """
        run at the start of each test suite.
        """
        self.core_config = "1S/4C/1T"
        self.dut_ports = self.dut.get_ports()
        self.cores_num = len([n for n in self.dut.cores if int(n["socket"]) == 0])
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(
            self.cores_num >= 4, "There has not enought cores to test this case"
        )
        self.core_list = self.dut.get_core_list(self.core_config)
        self.core_list_vhost = self.core_list[0:2]
        self.core_list_l3fwd = self.core_list[2:4]
        self.core_mask_vhost = utils.create_mask(self.core_list_vhost)
        self.core_mask_l3fwd = utils.create_mask(self.core_list_l3fwd)
        self.core_mask_virtio = self.core_mask_l3fwd
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.prepare_l3fwd_power()
        self.tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.tx_interface = self.tester.get_interface(self.tx_port)
        self.app_l3fwd_power_path = self.dut.apps_name["l3fwd-power"]
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.l3fwdpower_name = self.app_l3fwd_power_path.split("/")[-1]

    def set_up(self):
        """
        run before each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall %s" % self.l3fwdpower_name, "#")
        self.dut.send_expect("rm -rf vhost-net*", "#")
        self.l3fwd = self.dut.new_session(suite="l3fwd")
        self.vhost = self.dut.new_session(suite="vhost")
        self.virtio = self.dut.new_session(suite="virito")

    def close_all_session(self):
        self.dut.close_session(self.vhost)
        self.dut.close_session(self.virtio)
        self.dut.close_session(self.l3fwd)

    def prepare_l3fwd_power(self):
        out = self.dut.build_dpdk_apps("./examples/l3fwd-power")
        self.verify("Error" not in out, "compilation l3fwd-power error")

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def launch_l3fwd(self, path, packed=False):
        self.core_interrupt = self.core_list_l3fwd[0]
        example_para = "./%s " % self.app_l3fwd_power_path
        if not packed:
            vdev = "virtio_user0,path=%s,cq=1" % path
        else:
            vdev = "virtio_user0,path=%s,cq=1,packed_vq=1" % path
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list_l3fwd, prefix="l3fwd-pwd", no_pci=True, vdevs=[vdev]
        )
        if self.check_2M_env:
            eal_params += " --single-file-segments"
        para = (
            " --config='(0,0,%s)' --parse-ptype --interrupt-only" % self.core_interrupt
        )
        cmd_l3fwd = example_para + eal_params + " --log-level='user1,7' -- -p 1 " + para
        self.l3fwd.get_session_before(timeout=2)
        self.l3fwd.send_expect(cmd_l3fwd, "POWER", 40)
        time.sleep(10)
        out = self.l3fwd.get_session_before()
        if "Error" in out and "Error opening" not in out:
            self.logger.error("Launch l3fwd-power sample error")
        else:
            self.logger.info("Launch l3fwd-power sample finished")

    def start_vhost_testpmd(self, pci=""):
        """
        start testpmd on vhost side
        """
        testcmd = self.app_testpmd_path + " "
        vdev = ["net_vhost0,iface=vhost-net,queues=1,client=0"]
        para = " -- -i --rxq=1 --txq=1"
        allow_pci = [self.pci_info]
        if len(pci) == 0:
            eal_params = self.dut.create_eal_parameters(
                cores=self.core_list_vhost, ports=allow_pci, vdevs=vdev
            )
        else:
            eal_params = self.dut.create_eal_parameters(
                cores=self.core_list_vhost, prefix="vhost", no_pci=True, vdevs=vdev
            )
        cmd_vhost_user = testcmd + eal_params + para
        self.vhost.send_expect(cmd_vhost_user, "testpmd>", 30)
        self.vhost.send_expect("set fwd mac", "testpmd>", 30)
        self.vhost.send_expect("start", "testpmd>", 30)

    def start_virtio_user(self, packed=False):
        """
        start testpmd on virtio side
        """
        testcmd = self.app_testpmd_path + " "
        if not packed:
            vdev = "net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net"
        else:
            vdev = "net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1"
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list_l3fwd, prefix="virtio", no_pci=True, vdevs=[vdev]
        )
        para = " -- -i --txd=512 --rxd=128 --tx-offloads=0x00"
        cmd_virtio_user = testcmd + eal_params + para
        self.virtio.send_expect(cmd_virtio_user, "testpmd>", 120)
        self.virtio.send_expect("set fwd mac", "testpmd>", 20)
        self.virtio.send_expect("start", "testpmd>", 20)

    def check_interrupt_log(self, status):
        out = self.l3fwd.get_session_before()
        if status == "waked up":
            info = "lcore %s is waked up from rx interrupt on port 0 queue 0"
        elif status == "sleeps":
            info = "lcore %s sleeps until interrupt triggers"
        info = info % self.core_interrupt
        self.verify(info in out, "The CPU status not right for %s" % info)
        self.logger.info(info)

    def check_virtio_side_link_status(self, status):
        out = self.virtio.send_expect("show port info 0", "testpmd> ", 20)
        rinfo = re.search("Link\s*status:\s*([a-z]*)", out)
        result = rinfo.group(1)
        if status in result:
            self.logger.info("Link status is right, status is %s" % status)
        else:
            self.logger.error("Wrong link status not right, status is %s" % result)

    def test_split_ring_virtio_user_interrupt_with_vhost_net_as_backend(self):
        """
        Check the virtio-user interrupt can work when use vhost-net as backend
        """
        self.launch_l3fwd(path="/dev/vhost-net")
        self.virtio.send_expect("ifconfig tap0 up", "#", 20)
        self.virtio.send_expect("ifconfig tap0 1.1.1.2", "#", 20)
        # start to ping, check the status of interrupt core
        self.virtio.send_command("ping -I tap0 1.1.1.1 > aa &", 20)
        time.sleep(3)
        self.check_interrupt_log(status="waked up")
        # stop ping, check the status of interrupt core
        self.dut.send_expect("killall -s INT ping", "#")
        time.sleep(2)
        self.check_interrupt_log(status="sleeps")
        # restart ping, check the status of interrupt core
        self.virtio.send_command("ping -I tap0 1.1.1.1 > aa &", 20)
        time.sleep(3)
        self.check_interrupt_log(status="waked up")
        self.dut.send_expect("killall -s INT ping", "#")

    def test_split_ring_virtio_user_interrupt_with_vhost_user_as_backend(self):
        """
        Check the virtio-user interrupt can work when use vhost-user as backend
        """
        self.start_vhost_testpmd(pci="")
        self.launch_l3fwd(path="./vhost-net")
        # double check the status of interrupt core
        for i in range(2):
            self.tester.scapy_append(
                'pk=[Ether(dst="52:54:00:00:00:01")/IP()/("X"*64)]'
            )
            self.tester.scapy_append(
                'sendp(pk, iface="%s", count=100)' % self.tx_interface
            )
            self.tester.scapy_execute()
            time.sleep(3)
            self.check_interrupt_log(status="waked up")

    def test_lsc_event_between_vhost_user_and_virtio_user_with_split_ring(self):
        """
        LSC event between vhost-user and virtio-user
        """
        self.start_vhost_testpmd(pci="--no-pci")
        self.start_virtio_user()
        self.check_virtio_side_link_status("up")

        self.vhost.send_expect("quit", "#", 20)
        self.check_virtio_side_link_status("down")

    def test_packed_ring_virtio_user_interrupt_with_vhost_user_as_backend(self):
        """
        Check the virtio-user interrupt can work when use vhost-user as backend
        """
        self.start_vhost_testpmd(pci="")
        self.launch_l3fwd(path="./vhost-net", packed=True)
        # double check the status of interrupt core
        for i in range(2):
            self.tester.scapy_append(
                'pk=[Ether(dst="52:54:00:00:00:01")/IP()/("X"*64)]'
            )
            self.tester.scapy_append(
                'sendp(pk, iface="%s", count=100)' % self.tx_interface
            )
            self.tester.scapy_execute()
            time.sleep(3)
            self.check_interrupt_log(status="waked up")

    def test_packed_ring_virtio_user_interrupt_with_vhost_net_as_backend(self):
        """
        Check the virtio-user interrupt can work when use vhost-net as backend
        """
        self.launch_l3fwd(path="/dev/vhost-net", packed=True)
        self.virtio.send_expect("ifconfig tap0 up", "#", 20)
        self.virtio.send_expect("ifconfig tap0 1.1.1.2", "#", 20)
        # start to ping, check the status of interrupt core
        self.virtio.send_command("ping -I tap0 1.1.1.1 > aa &", 20)
        time.sleep(3)
        self.check_interrupt_log(status="waked up")
        # stop ping, check the status of interrupt core
        self.dut.send_expect("killall -s INT ping", "#")
        time.sleep(2)
        self.check_interrupt_log(status="sleeps")
        # restart ping, check the status of interrupt core
        self.virtio.send_command("ping -I tap0 1.1.1.1 > aa &", 20)
        time.sleep(3)
        self.check_interrupt_log(status="waked up")
        self.dut.send_expect("killall -s INT ping", "#")

    def test_lsc_event_between_vhost_user_and_virtio_user_with_packed_ring(self):
        """
        LSC event between vhost-user and virtio-user
        """
        self.start_vhost_testpmd(pci="--no-pci")
        self.start_virtio_user(packed=True)
        self.check_virtio_side_link_status("up")
        self.vhost.send_expect("quit", "#", 20)
        self.check_virtio_side_link_status("down")

    def tear_down(self):
        """
        run after each test case.
        """
        self.dut.send_expect("killall %s" % self.l3fwdpower_name, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.close_all_session()

    def tear_down_all(self):
        """
        run after each test suite.
        """
        pass
