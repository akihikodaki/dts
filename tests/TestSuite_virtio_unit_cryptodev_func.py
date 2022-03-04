 # BSD LICENSE
#
# Copyright(c) 2018-2019 Intel Corporation. All rights reserved.
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
DPDK Test suite
Test DPDK vhost + virtio scenarios
"""

import os
import subprocess

import framework.utils as utils
import tests.cryptodev_common as cc
from framework.qemu_kvm import QEMUKvm
from framework.test_case import TestCase


class VirtioCryptodevUnitTest(TestCase):
    def set_up_all(self):
        self.sample_app = self.dut.apps_name['vhost_crypto']
        self.user_app = self.dut.apps_name['test']

        self.vm0, self.vm0_dut = None, None
        self.dut.skip_setup = True

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, 'Insufficient ports for test')
        self.cores = self.dut.get_core_list("1S/3C/1T")
        self.mem_channel = self.dut.get_memory_channels()

        cc.bind_qat_device(self, self.drivername)
        self.dut.build_dpdk_apps("./examples/vhost_crypto")

        self.vf_assign_method = "vfio-pci"
        self.dut.setup_modules(None, self.vf_assign_method, None)

        self.dut.restore_interfaces()
        self.used_dut_port = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(
            self.used_dut_port, 1, driver='default')
        self.sriov_vfs_port = self.dut.ports_info[
            self.used_dut_port]['vfs_port']
        for port in self.sriov_vfs_port:
            port.bind_driver(self.vf_assign_method)

        intf = self.dut.ports_info[self.used_dut_port]['intf']
        vf_mac = "52:00:00:00:00:01"
        self.dut.send_expect("ip link set %s vf 0 mac %s" %
                (intf, vf_mac), "# ")

        self.launch_vhost_switch()
        self.vm0, self.vm0_dut = self.launch_virtio_dut("vm0")

    def set_up(self):
        pass

    def dut_execut_cmd(self, cmdline, ex='#', timout=30):
        return self.dut.send_expect(cmdline, ex, timout)

    def get_vhost_eal(self):
        default_eal_opts = {
            "c": None,
            "l": ','.join(self.cores),
            "a": None,
            "vdev": None,
            "socket-mem": "2048,0",
            "n": self.mem_channel,
        }
        opts = default_eal_opts.copy()

        # Update options with test suite/case config file
        for key in list(opts.keys()):
            if key in self.get_suite_cfg():
                opts[key] = self.get_suite_cfg()[key]

        # Generate option string
        opt_str = ""
        for key,value in list(opts.items()):
            if value is None:
                continue
            dash = "-" if len(key) == 1 else "--"
            opt_str = opt_str + "{0}{1} {2} ".format(dash, key, value)

        return opt_str

    def launch_vhost_switch(self):
        eal_opt_str = self.get_vhost_eal()

        config = '"(%s,0,0),(%s,0,0)"' % tuple(self.cores[-2:])
        socket_file = "%s,/tmp/vm0_crypto0.sock --socket-file=%s,/tmp/vm0_crypto1.sock" % tuple(self.cores[-2:])
        self.vhost_switch_cmd = cc.get_dpdk_app_cmd_str(self.sample_app, eal_opt_str,
                                    '--config %s --socket-file %s' % (config, socket_file))

        out = self.dut_execut_cmd(self.vhost_switch_cmd, "socket created", 30)
        self.logger.info(out)

    def set_virtio_pci(self, dut):
        out = dut.send_expect("lspci -d:1054|awk '{{print $1}}'", "# ", 10)
        virtio_list = out.replace("\r", "\n").replace("\n\n", "\n").split("\n")
        dut.send_expect('modprobe uio_pci_generic', '#', 10)
        for line in virtio_list:
            cmd = "echo 0000:{} > /sys/bus/pci/devices/0000\:{}/driver/unbind".format(
                line, line.replace(":", "\:"))
            dut.send_expect(cmd, "# ", 10)
        dut.send_expect('echo "1af4 1054" > /sys/bus/pci/drivers/uio_pci_generic/new_id', "# ", 10)

        return virtio_list

    def launch_virtio_dut(self, vm_name):
        # start vm
        vm = QEMUKvm(self.dut, vm_name, 'virtio_unit_cryptodev_func')
        vf0 = {'opt_host': self.sriov_vfs_port[0].pci}
        vm.set_vm_device(driver=self.vf_assign_method, **vf0)

        try:
            vm_dut = vm.start()
            if vm_dut is None:
                print(('{} start failed'.format(vm_name)))
        except Exception as err:
            raise err

        vm.virtio_list = self.set_virtio_pci(vm_dut)
        self.logger.info("{} virtio list: {}".format(vm_name, vm.virtio_list))
        vm.cores = vm_dut.get_core_list("all")
        self.logger.info("{} core list: {}".format(vm_name, vm.cores))
        vm.ports = [port["pci"] for port in vm_dut.ports_info]
        self.logger.info("{} port list: {}".format(vm_name, vm.ports))

        return vm, vm_dut

    def test_cryptodev_virtio_autotest(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"a":None, "vdev": "crypto_virtio"})
        self.__run_unit_test("cryptodev_virtio_autotest", eal_opt_str)

    def __run_unit_test(self, testsuite, eal_opt_str='', timeout=600):
        self.logger.info("STEP_TEST: " + testsuite)
        self.vm0_dut.send_expect("dmesg -C", "# ", 30)
        cmd_str = cc.get_dpdk_app_cmd_str(self.user_app, "--log-level 6", eal_opt_str)
        info = self.vm0_dut.send_expect(cmd_str, "RTE>>", 30)
        self.logger.info(info)

        out = ""
        try:
            out = self.vm0_dut.send_expect(testsuite, "RTE>>", timeout)
            self.vm0_dut.send_expect("quit", "# ", 30)
        except Exception as err:
            self.logger.error("Cryptodev Unit Tests Exception")
            dmesg = self.vm0_dut.alt_session.send_expect("dmesg", "# ", 30)
            self.logger.error("dmesg info:")
            self.logger.error(dmesg)

        self.logger.info(out)
        self.verify("Test OK" in out, "Test Failed")
        self.vm0_dut.kill_all()

    def tear_down(self):
        pass

    def tear_down_all(self):
        if getattr(self, 'vm0', None):
            self.vm0_dut.kill_all()
            self.vm0.stop()
            self.vm0 = None

        if getattr(self, 'used_dut_port', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.used_dut_port = None

        self.dut_execut_cmd("^C", "# ")
        self.app_name = self.sample_app[self.sample_app.rfind('/')+1:]
        self.dut.send_expect("killall -s INT %s" % self.app_name, "#")
        self.dut_execut_cmd("killall -s INT qemu-system-x86_64")
        self.dut_execut_cmd("rm -r /tmp/*")
