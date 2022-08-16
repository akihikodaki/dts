# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

"""
DPDK Test suite.
Virtio-user interrupt need test with l3fwd-power sample
"""

import re
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestVirtioUserInterruptCbdma(TestCase):
    def set_up_all(self):
        """
        run at the start of each test suite.
        """
        self.core_config = "1S/4C/1T"
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n["socket"]) == 0])
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(
            self.cores_num >= 4, "There has not enought cores to test this case"
        )
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket
        )
        self.vhost_core_list = self.core_list[0:2]
        self.l3fwd_core_list = self.core_list[2:4]
        self.core_mask_vhost = utils.create_mask(self.vhost_core_list)
        self.l3fwd_core_mask = utils.create_mask(self.l3fwd_core_list)
        self.virtio_core_mask = self.l3fwd_core_mask
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.cbdma_dev_infos = []
        self.dmas_info = None
        self.device_str = None
        self.prepare_l3fwd_power()
        self.tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.tx_interface = self.tester.get_interface(self.tx_port)
        self.app_l3fwd_power_path = self.dut.apps_name["l3fwd-power"]
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.l3fwdpower_name = self.app_l3fwd_power_path.split("/")[-1]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.vhost_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.virtio_pmd = PmdOutput(self.dut, self.virtio_user)
        self.l3fwd = self.dut.new_session(suite="l3fwd")

    def set_up(self):
        """
        run before each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall %s" % self.l3fwdpower_name, "#")
        self.dut.send_expect("rm -rf vhost-net*", "#")

    def close_all_session(self):
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)
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
        self.core_interrupt = self.l3fwd_core_list[0]
        example_para = "./%s " % self.app_l3fwd_power_path
        if not packed:
            vdev = "virtio_user0,path=%s,cq=1" % path
        else:
            vdev = "virtio_user0,path=%s,cq=1,packed_vq=1" % path
        eal_params = self.dut.create_eal_parameters(
            cores=self.l3fwd_core_list, prefix="l3fwd-pwd", no_pci=True, vdevs=[vdev]
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

    def check_interrupt_log(self, status, out):
        if status == "waked up":
            info = "lcore %s is waked up from rx interrupt on port 0 queue 0"
        elif status == "sleeps":
            info = "lcore %s sleeps until interrupt triggers"
        info = info % self.core_interrupt
        self.verify(info in out, "The CPU status not right for %s" % info)

    def check_virtio_side_link_status(self, status):
        out = self.virtio_pmd.execute_cmd("show port info 0")
        rinfo = re.search("Link\s*status:\s*([a-z]*)", out)
        result = rinfo.group(1)
        if status in result:
            self.logger.info("Link status is right, status is %s" % status)
        else:
            self.logger.error("Wrong link status not right, status is %s" % result)

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num, allow_diff_socket=False):
        """
        get all cbdma ports
        """
        self.all_cbdma_list = []
        self.cbdma_list = []
        self.cbdma_str = ""
        out = self.dut.send_expect(
            "./usertools/dpdk-devbind.py --status-dev dma", "# ", 30
        )
        device_info = out.split("\n")
        for device in device_info:
            pci_info = re.search("\s*(0000:\S*:\d*.\d*)", device)
            if pci_info is not None:
                dev_info = pci_info.group(1)
                # the numa id of ioat dev, only add the device which on same socket with nic dev
                bus = int(dev_info[5:7], base=16)
                if bus >= 128:
                    cur_socket = 1
                else:
                    cur_socket = 0
                if allow_diff_socket:
                    self.all_cbdma_list.append(pci_info.group(1))
                else:
                    if self.ports_socket == cur_socket:
                        self.all_cbdma_list.append(pci_info.group(1))
        self.verify(
            len(self.all_cbdma_list) >= cbdma_num, "There no enough cbdma device"
        )
        self.cbdma_list = self.all_cbdma_list[0:cbdma_num]
        self.cbdma_str = " ".join(self.cbdma_list)
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=%s %s"
            % (self.drivername, self.cbdma_str),
            "# ",
            60,
        )

    def bind_cbdma_device_to_kernel(self):
        self.dut.send_expect("modprobe ioatdma", "# ")
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -u %s" % self.cbdma_str, "# ", 30
        )
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=ioatdma  %s" % self.cbdma_str,
            "# ",
            60,
        )

    def test_split_ring_lsc_event_between_vhost_user_and_virtio_user_with_cbdma_enable(
        self,
    ):
        """
        Test Case1: Split ring LSC event between vhost-user and virtio-user with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=1)
        lcore_dma = "lcore%s@%s" % (self.vhost_core_list[1], self.cbdma_list[0])
        vhost_param = "--lcore-dma=[%s]" % lcore_dma
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,client=0,dmas=[txq0;rxq0]'"
        )
        ports = self.cbdma_list
        self.vhost_pmd.start_testpmd(
            cores=self.vhost_core_list,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_pmd.execute_cmd("set fwd mac")
        self.vhost_pmd.execute_cmd("start")
        virtio_param = "--tx-offloads=0x00"
        virtio_eal_param = (
            "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net"
        )
        self.virtio_pmd.start_testpmd(
            cores=self.l3fwd_core_list,
            no_pci=True,
            prefix="virtio",
            eal_param=virtio_eal_param,
            param=virtio_param,
        )
        self.virtio_pmd.execute_cmd("set fwd mac")
        self.virtio_pmd.execute_cmd("start")
        self.check_virtio_side_link_status("up")
        self.vhost_pmd.quit()
        self.check_virtio_side_link_status("down")

    def test_split_ring_virtio_user_interrupt_test_with_vhost_user_as_backend_and_cbdma_enable(
        self,
    ):
        """
        Test Case2: Split ring virtio-user interrupt test with vhost-user as backend and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=2)
        lcore_dma = "lcore%s@%s,lcore%s@%s" % (
            self.vhost_core_list[1],
            self.cbdma_list[0],
            self.vhost_core_list[1],
            self.cbdma_list[1],
        )
        vhost_param = "--rxq=1 --txq=1 --lcore-dma=[%s]" % lcore_dma
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0;rxq0]'"
        )
        ports = self.cbdma_list
        ports.append(self.dut.ports_info[0]["pci"])
        self.logger.info(ports)
        self.vhost_pmd.start_testpmd(
            cores=self.vhost_core_list,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_pmd.execute_cmd("start")
        self.launch_l3fwd(path="./vhost-net")
        # double check the status of interrupt core
        for _ in range(2):
            self.tester.scapy_append(
                'pk=[Ether(dst="52:54:00:00:00:01")/IP()/("X"*64)]'
            )
            self.tester.scapy_append(
                'sendp(pk, iface="%s", count=100)' % self.tx_interface
            )
            self.tester.scapy_execute()
            time.sleep(3)
            out = self.l3fwd.get_session_before()
            self.logger.info(out)
            self.check_interrupt_log(status="waked up", out=out)
            self.check_interrupt_log(status="sleeps", out=out)

    def test_packed_ring_lsc_event_between_vhost_user_and_virtio_user_with_cbdma_enable(
        self,
    ):
        """
        Test Case3: Packed ring LSC event between vhost-user and virtio-user with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=1)
        lcore_dma = "lcore%s@%s" % (self.vhost_core_list[1], self.cbdma_list[0])
        vhost_param = "--lcore-dma=[%s]" % lcore_dma
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,client=0,dmas=[txq0;rxq0]'"
        )
        ports = self.cbdma_list
        self.vhost_pmd.start_testpmd(
            cores=self.vhost_core_list,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_pmd.execute_cmd("set fwd mac")
        self.vhost_pmd.execute_cmd("start")
        virtio_param = "--tx-offloads=0x00"
        virtio_eal_param = (
            "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,packed_vq=1"
        )
        self.virtio_pmd.start_testpmd(
            cores=self.l3fwd_core_list,
            no_pci=True,
            prefix="virtio",
            eal_param=virtio_eal_param,
            param=virtio_param,
        )
        self.virtio_pmd.execute_cmd("set fwd mac")
        self.virtio_pmd.execute_cmd("start")
        self.check_virtio_side_link_status("up")
        self.vhost_pmd.quit()
        self.check_virtio_side_link_status("down")

    def test_packed_ring_virtio_user_interrupt_test_with_vhost_user_as_backend_and_cbdma_enable(
        self,
    ):
        """
        Test Case4: Packed ring virtio-user interrupt test with vhost-user as backend and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=2)
        lcore_dma = "lcore%s@%s,lcore%s@%s" % (
            self.vhost_core_list[1],
            self.cbdma_list[0],
            self.vhost_core_list[1],
            self.cbdma_list[1],
        )
        vhost_param = "--rxq=1 --txq=1 --lcore-dma=[%s]" % lcore_dma
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=1,dmas=[txq0;rxq0]'"
        )
        ports = self.cbdma_list
        ports.append(self.dut.ports_info[0]["pci"])
        self.vhost_pmd.start_testpmd(
            cores=self.vhost_core_list,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_pmd.execute_cmd("start")
        self.launch_l3fwd(path="./vhost-net", packed=True)
        # double check the status of interrupt core
        for _ in range(2):
            self.tester.scapy_append(
                'pk=[Ether(dst="52:54:00:00:00:01")/IP()/("X"*64)]'
            )
            self.tester.scapy_append(
                'sendp(pk, iface="%s", count=100)' % self.tx_interface
            )
            self.tester.scapy_execute()
            time.sleep(3)
            out = self.l3fwd.get_session_before()
            self.logger.info(out)
            self.check_interrupt_log(status="waked up", out=out)
            self.check_interrupt_log(status="sleeps", out=out)

    def tear_down(self):
        """
        run after each test case.
        """
        self.dut.send_expect("killall %s" % self.l3fwdpower_name, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        run after each test suite.
        """
        self.close_all_session()
