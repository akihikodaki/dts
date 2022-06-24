# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM


class TestVhostQemuMTU(TestCase):
    def set_up_all(self):
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_list = self.dut.get_core_list("all", socket=self.ports_socket)
        self.verify(
            len(self.cores_list) >= 4,
            "There has not enough cores to test this suite %s" % self.suite_name,
        )
        self.vhost_core_list = self.cores_list[0:2]
        self.vm_num = 1
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)

    def set_up(self):
        """
        run before each test case.
        """
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT dpdk-testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.vm_dut = []
        self.vm = []

    def start_vhost_testpmd(self):
        """
        start testpmd on vhost
        """
        vdevs = ["net_vhost0,iface=vhost-net0,queues=1"]
        ports = [self.dut.ports_info[self.dut_ports[0]]["pci"]]
        param = "--txd=512 --rxd=128 --nb-cores=1 --port-topology=chained"
        self.vhost_user_pmd.start_testpmd(
            cores=self.vhost_core_list,
            param=param,
            vdevs=vdevs,
            ports=ports,
            prefix="vhost-user",
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

    def start_vms(self, vm_config="vhost_sample", mtu=9000):
        """
        start two VM, each VM has one virtio device
        """
        for i in range(self.vm_num):
            vm_dut = None
            vm_info = VM(self.dut, "vm%d" % i, vm_config)
            vm_params = {}
            vm_params["driver"] = "vhost-user"
            vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i
            vm_params["opt_mac"] = "52:54:00:00:00:0%d" % (i + 1)
            vm_params["opt_settings"] = "mrg_rxbuf=on,host_mtu=%d" % mtu
            vm_info.set_vm_device(**vm_params)
            try:
                vm_dut = vm_info.start(set_target=False)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                print(utils.RED("Failure for %s" % str(e)))
            self.verify(vm_dut is not None, "start vm failed")
            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def check_mtu_value_in_vm(self, mtu):
        vm1_intf = self.vm_dut[0].ports_info[0]["intf"]
        out = self.vm_dut[0].send_expect("ifconfig %s" % vm1_intf, "#", 10)
        self.verify("mtu %d" % mtu in out, "Check MTU value in VM FAILED!")

    def check_mtu_value_in_testpmd(self, mtu):
        out = self.vhost_user_pmd.execute_cmd("show port info 1")
        self.verify("MTU: %d" % mtu in out, "Check MTU value in testpmd FAILED!")

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm[i].stop()
            self.vm_dut.remove(self.vm_dut[i])
            self.vm.remove(self.vm[i])
        self.vhost_user_pmd.quit()

    def test_mtu_in_virtio_net(self):
        """
        Test Case: Test the MTU in virtio-net
        """
        MTU_LIST = [9000, 68, 65535]
        for expected_mtu in MTU_LIST:
            self.start_vhost_testpmd()
            self.start_vms(mtu=expected_mtu)
            self.check_mtu_value_in_vm(mtu=expected_mtu)
            self.check_mtu_value_in_testpmd(mtu=expected_mtu)
            self.stop_all_apps()

    def tear_down(self):
        """
        run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
