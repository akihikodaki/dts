# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2018-2019 Intel Corporation
#

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


class TestVirtioPerfCryptodevFunc(TestCase):
    def set_up_all(self):
        self.sample_app = self.dut.apps_name["vhost_crypto"]
        self.user_app = self.dut.apps_name["test-crypto-perf"]
        self._default_crypto_perf_opts = {
            "ptest": "throughput",
            "silent": "",
            "pool-sz": None,
            "total-ops": "1000000",
            "burst-sz": "32",
            "buffer-sz": "64",
            "devtype": None,
            "segments-nb": None,
            "optype": "cipher-then-auth",
            "sessionless": None,
            "out-of-place": None,
            "test-file": None,
            "test-name": None,
            "cipher-algo": None,
            "cipher-op": None,
            "cipher-key-sz": None,
            "cipher-iv-sz": None,
            "auth-algo": None,
            "auth-op": None,
            "auth-key-sz": None,
            "auth-iv-sz": None,
            "aead-algo": None,
            "aead-op": None,
            "aead-key-sz": None,
            "aead-iv-sz": None,
            "aead-aad-sz": None,
            "digest-sz": None,
            "csv-friendly": None,
        }

        self.vm0, self.vm0_dut = None, None
        self.dut.skip_setup = True

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for test")
        self.cores = self.dut.get_core_list("1S/3C/1T")
        self.mem_channel = self.dut.get_memory_channels()

        self.dut.build_dpdk_apps("./examples/vhost_crypto")
        cc.bind_qat_device(self, self.drivername)

        self.vf_assign_method = "vfio-pci"
        self.dut.setup_modules(None, self.vf_assign_method, None)

        self.dut.restore_interfaces()
        self.used_dut_port = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 1, driver="default")
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]["vfs_port"]
        for port in self.sriov_vfs_port:
            port.bind_driver(self.vf_assign_method)

        intf = self.dut.ports_info[self.used_dut_port]["intf"]
        vf_mac = "52:00:00:00:00:01"
        self.dut.send_expect("ip link set %s vf 0 mac %s" % (intf, vf_mac), "# ")

        self.launch_vhost_switch()
        self.vm0, self.vm0_dut = self.launch_virtio_dut("vm0")

    def set_up(self):
        pass

    def dut_execut_cmd(self, cmdline, ex="#", timout=30):
        return self.dut.send_expect(cmdline, ex, timout)

    def get_vhost_eal(self):
        default_eal_opts = {
            "c": None,
            "l": ",".join(self.cores),
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
        for key, value in list(opts.items()):
            if value is None:
                continue
            dash = "-" if len(key) == 1 else "--"
            opt_str = opt_str + "{0}{1} {2} ".format(dash, key, value)

        return opt_str

    def launch_vhost_switch(self):
        eal_opt_str = self.get_vhost_eal()
        config = '"(%s,0,0),(%s,0,0)"' % tuple(self.cores[-2:])
        socket_file = (
            "%s,/tmp/vm0_crypto0.sock --socket-file=%s,/tmp/vm0_crypto1.sock"
            % tuple(self.cores[-2:])
        )
        self.vhost_switch_cmd = cc.get_dpdk_app_cmd_str(
            self.sample_app,
            eal_opt_str,
            "--config %s --socket-file %s" % (config, socket_file),
        )

        out = self.dut_execut_cmd(self.vhost_switch_cmd, "socket created", 30)
        self.logger.info(out)

    def set_virtio_pci(self, dut):
        out = dut.send_expect("lspci -d:1054|awk '{{print $1}}'", "# ", 10)
        virtio_list = out.replace("\r", "\n").replace("\n\n", "\n").split("\n")
        dut.send_expect("modprobe uio_pci_generic", "#", 10)
        for line in virtio_list:
            cmd = "echo 0000:{} > /sys/bus/pci/devices/0000\:{}/driver/unbind".format(
                line, line.replace(":", "\:")
            )
            dut.send_expect(cmd, "# ", 10)
        dut.send_expect(
            'echo "1af4 1054" > /sys/bus/pci/drivers/uio_pci_generic/new_id', "# ", 10
        )

        return virtio_list

    def launch_virtio_dut(self, vm_name):
        # start vm
        vm = QEMUKvm(self.dut, vm_name, "virtio_perf_cryptodev_func")

        vf0 = {"opt_host": self.sriov_vfs_port[0].pci}
        vm.set_vm_device(driver=self.vf_assign_method, **vf0)
        skip_setup = self.dut.skip_setup

        try:
            self.dut.skip_setup = True
            vm_dut = vm.start()
            if vm_dut is None:
                print(("{} start failed".format(vm_name)))
        except Exception as err:
            raise err

        self.dut.skip_setup = skip_setup
        vm_dut.restore_interfaces()

        vm_dut.setup_modules(self.target, self.drivername, None)
        vm_dut.bind_interfaces_linux(self.drivername)
        vm.virtio_list = self.set_virtio_pci(vm_dut)
        self.logger.info("{} virtio list: {}".format(vm_name, vm.virtio_list))
        vm.cores = vm_dut.get_core_list("all")
        self.logger.info("{} core list: {}".format(vm_name, vm.cores))
        vm.ports = [port["pci"] for port in vm_dut.ports_info]
        self.logger.info("{} port list: {}".format(vm_name, vm.ports))

        return vm, vm_dut

    def test_aesni_mb_aes_cbc_sha1_hmac(self):
        if cc.is_test_skip(self):
            return

        eal_opt_str = cc.get_eal_opt_str(self, {"a": None})
        crypto_perf_opt_str = cc.get_opt_str(self, self._default_crypto_perf_opts)
        out = self._run_crypto_perf(eal_opt_str, crypto_perf_opt_str)
        self.logger.info(out)
        self.verify("Enqueued" in out, "Test fail")
        self.verify("Error" not in out, "Test fail")

    def test_virtio_aes_cbc_sha1_hmac(self):
        if cc.is_test_skip(self):
            return

        eal_opt_str = cc.get_eal_opt_str(
            self, {"a": self.vm0.virtio_list[0], "vdev": None}
        )
        crypto_perf_opt_str = cc.get_opt_str(self, self._default_crypto_perf_opts)
        out = self._run_crypto_perf(eal_opt_str, crypto_perf_opt_str)
        self.logger.info(out)
        self.verify("Enqueued" in out, "Test fail")
        self.verify("Error" not in out, "Test fail")

    def _run_crypto_perf(self, eal_opt_str, crypto_perf_opt_str):
        cmd_str = cc.get_dpdk_app_cmd_str(
            self.user_app, eal_opt_str, crypto_perf_opt_str
        )
        self.logger.info(cmd_str)
        try:
            out = self.vm0_dut.send_expect(cmd_str, "#", 600)
        except Exception as ex:
            self.logger.error(ex)
            raise ex

        return out

    def tear_down(self):
        pass

    def tear_down_all(self):
        if getattr(self, "vm0", None):
            self.vm0_dut.kill_all()
            self.vm0.stop()
            self.vm0 = None

        if getattr(self, "used_dut_port", None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.used_dut_port = None

        self.dut_execut_cmd("^C", "# ")
        self.app_name = self.sample_app[self.sample_app.rfind("/") + 1 :]
        self.dut.send_expect("killall -s INT %s" % self.app_name, "#")
        self.dut_execut_cmd("killall -s INT qemu-system-x86_64")
        self.dut_execut_cmd("rm -r /tmp/*")
